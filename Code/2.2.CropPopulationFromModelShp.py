import glob
import random
from shapely.geometry import Point, box
from rasterio.windows import Window
from rasterio.windows import transform as window_transform

import os
from pathlib import Path

import geopandas as gpd
import rasterio
from rasterio.mask import mask

from shapely.ops import unary_union, transform
from shapely.geometry import mapping
from pyproj import Transformer


def reproject_geom(geom, src_crs, dst_crs):
    if src_crs is None or dst_crs is None:
        raise ValueError("re-projection error")

    if str(src_crs) == str(dst_crs):
        return geom

    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    return transform(transformer.transform, geom)


def random_point_in_geom(geom, rng, max_tries=20000):

    minx, miny, maxx, maxy = geom.bounds
    for _ in range(max_tries):
        x = rng.uniform(minx, maxx)
        y = rng.uniform(miny, maxy)
        p = Point(x, y)
        if geom.contains(p):
            return p
    raise RuntimeError("empty")


def point_window_within_raster(src, x, y, patch_size):
    """
    判断以(x,y)为中心的 patch_size×patch_size 窗口是否完全落在影像内部。
    返回: (ok, window, (row, col))
    """
    half = patch_size // 2
    row, col = src.index(x, y)  # row, col are ints

    col_off = col - half
    row_off = row - half

    ok = (col_off >= 0) and (row_off >= 0) and \
         (col_off + patch_size <= src.width) and \
         (row_off + patch_size <= src.height)

    if not ok:
        return False, None, (row, col)

    win = Window(col_off=col_off, row_off=row_off, width=patch_size, height=patch_size)
    return True, win, (row, col)


def sample_points(src, geom_target, n_in, n_out, patch_size, seed=42):
    rng = random.Random(seed)

    raster_geom = box(*src.bounds)  # shapely box(minx, miny, maxx, maxy)

    geom_in = geom_target.intersection(raster_geom)
    if geom_in.is_empty:
        raise ValueError("empty")

    geom_out = raster_geom.difference(geom_target)
    if geom_out.is_empty:
        raise ValueError("empty")

    inside_points = []
    outside_points = []

    def sample_valid_point(geom, label, max_tries=50000):
        for _ in range(max_tries):
            try:
                p = random_point_in_geom(geom, rng)
                ok, win, (row, col) = point_window_within_raster(src, p.x, p.y, patch_size)
                if ok:
                    return p, win, row, col
            except:
                pass

        raise RuntimeError(f" {label} error")

    for i in range(n_in):
        p, win, row, col = sample_valid_point(geom_in, label="inside")
        inside_points.append((p, win, row, col))

    for i in range(n_out):
        p, win, row, col = sample_valid_point(geom_out, label="outside")
        outside_points.append((p, win, row, col))

    return inside_points, outside_points


def crop_and_save(src, win, out_path):
    data = src.read(window=win)  # shape: (bands, H, W)
    meta = src.meta.copy()
    meta.update({
        "height": int(win.height),
        "width": int(win.width),
        "transform": window_transform(win, src.transform)
    })

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(data)


def fix_geometry_series(gser):
    from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
    from shapely.ops import unary_union

    gser = gser.copy()
    gser = gser[gser.notnull()]
    gser = gser[~gser.is_empty]

    # --- 1) make_valid ---
    def _make_valid(g):
        if g is None or g.is_empty:
            return g
        try:
            # shapely 2.x
            from shapely import make_valid
            return make_valid(g)
        except Exception:
            # shapely 1.8.x
            try:
                from shapely.validation import make_valid
                return make_valid(g)
            except Exception:
                return g

    gser = gser.apply(_make_valid)

    def _buffer0(g):
        if g is None or g.is_empty:
            return g
        try:
            if not g.is_valid:
                return g.buffer(0)
            return g
        except Exception:
            return g

    gser = gser.apply(_buffer0)

    def _keep_polygons(g):
        if g is None or g.is_empty:
            return None
        if isinstance(g, (Polygon, MultiPolygon)):
            return g
        if isinstance(g, GeometryCollection):
            polys = [gg for gg in g.geoms if isinstance(gg, (Polygon, MultiPolygon)) and (not gg.is_empty)]
            if len(polys) == 0:
                return None
            try:
                return unary_union(polys)
            except Exception:
                return polys[0]
        return None

    gser = gser.apply(_keep_polygons)
    gser = gser[gser.notnull()]
    gser = gser[~gser.is_empty]

    gser = gser[gser.is_valid]
    return gser


def crop_function(image_path, gdf_target, geom_target_src, out_path):
    image_path = str(image_path)

    with rasterio.open(image_path) as src:
        raster_crs = src.crs
        if raster_crs is None:
            raise ValueError(f"影像没有 CRS：{image_path}")

        shp_crs = gdf_target.crs
        geom_in_raster = reproject_geom(geom_target_src, shp_crs, raster_crs)

        if geom_in_raster.is_empty:
            print(f"[跳过] 重投影后几何为空：{image_path}")
            return

        shapes = [mapping(geom_in_raster)]

        try:
            out_img, out_transform = mask(
                src,
                shapes=shapes,
                crop=False,
                nodata=src.nodata,
                all_touched=False,
                filled=True
            )
        except ValueError as e:
            print(f"[跳过] 裁切失败（可能不相交）：{image_path} -> {e}")
            return

        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_img.shape[1],
            "width": out_img.shape[2],
            "transform": out_transform,
            "crs": raster_crs,
        })

        out_meta.update({
            "compress": "lzw",
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256
        })

    with rasterio.open(out_path, "w", **out_meta) as dst:
        dst.write(out_img)

    print(f"[OK] {image_path} -> {out_path}")


def validation2010(
    tif_list,
    shp_path,
    out_dir,
    status_field="status",
    target_values=(0, 1),
):
    os.makedirs(out_dir, exist_ok=True)

    gdf = gpd.read_file(shp_path)

    if status_field not in gdf.columns:
        raise KeyError(f"shp can not found '{status_field}', current status{list(gdf.columns)}")

    gdf_target = gdf[gdf[status_field].isin(list(target_values))].copy()
    if len(gdf_target) == 0:
        raise ValueError(f"shp status ∈ {target_values}  is empty")

    try:
        geom_target = unary_union(list(gdf_target.geometry))
        geom_target_src = unary_union(list(gdf_target.geometry))
    except:
        gdf_target = gdf_target[~gdf_target.geometry.is_empty & gdf_target.geometry.notnull()].copy()
        gdf_target["geometry"] = fix_geometry_series(gdf_target.geometry)
        if len(gdf_target) == 0:
            raise ValueError("empty, check status")
        print('empty', shp_path)
        geom_target = unary_union(list(gdf_target.geometry))
        geom_target_src = unary_union(list(gdf_target.geometry))
    if geom_target.is_empty:
        raise ValueError("empty")

    for image_path in tif_list:
        in_name = Path(image_path).stem
        out_path = os.path.join(out_dir, f"{in_name}_clip.tif")
        crop_function(image_path, gdf_target, geom_target_src, out_path)


def function_single(image_path, shp_path, save_path, status_field="status", target_values=(0, 1),):
    gdf = gpd.read_file(shp_path)

    if status_field not in gdf.columns:
        raise KeyError(f"shp can not found '{status_field}', current status {list(gdf.columns)}")

    gdf_target = gdf[gdf[status_field].isin(list(target_values))].copy()
    if len(gdf_target) == 0:
        raise ValueError(f"shp status ∈ {target_values} is empty")

    try:
        geom_target = unary_union(list(gdf_target.geometry))
        geom_target_src = unary_union(list(gdf_target.geometry))
    except:
        print('fixing')
        gdf_target = gdf_target[~gdf_target.geometry.is_empty & gdf_target.geometry.notnull()].copy()
        gdf_target["geometry"] = fix_geometry_series(gdf_target.geometry)
        if len(gdf_target) == 0:
            raise ValueError("empty")
        print('fixing：', shp_path)
        geom_target = unary_union(list(gdf_target.geometry))
        geom_target_src = unary_union(list(gdf_target.geometry))
    if geom_target.is_empty:
        raise ValueError("empty")

    crop_function(image_path, gdf_target, geom_target_src, save_path)


def one_step():
    city_dir = '/intelnvme04/jiang.mingyu/slum/GoogleMap'
    save_dir = os.path.join(city_dir, '2010validation')
    os.makedirs(save_dir, exist_ok=True)

    city_dir_list = os.listdir(city_dir)
    for city_dir_name in city_dir_list:
        if 'drop' in city_dir_name:
            continue

        city_dir_path = os.path.join(city_dir, city_dir_name)
        if not os.path.isdir(city_dir_path):
            continue

        city_dir_structure = os.listdir(city_dir_path)
        if '2010' not in city_dir_structure:
            continue

        image_path = os.path.join(city_dir_path, '2010', 'L19.tif')
        if os.path.isfile(image_path):
            _save_dir = os.path.join(save_dir, city_dir_name)

            shp_path = os.path.join(city_dir_path, 'TemporalChange.shp')
            if not os.path.isfile(shp_path):
                continue

            print("保存完成：", image_path)


if __name__ == "__main__":
    # slum shp from https://doi.org/10.5281/zenodo.18606153
    tif_shp_mach_dict = {
        'Cairo': 'Cairo.shp', 'CapeTown': 'CapeTown.shp', 'Dar_es_Salaam': 'Dar_es_Salaam.shp', 'Karachi': 'Karachi.shp',
        'Manila': 'MetroManila.shp', 'Mumbai': 'Mumbai.shp', 'Nairobi': 'Nairobi.shp',
        'Port_au_Prince': 'Port-au-Prince.shp', 'Rio': 'Rio_de_Janeiro.shp'
    }
    tif_dir = '/intelnvme04/jiang.mingyu/slum1/data/GHS-built/residential'
    shp_dir = '/intelnvme04/jiang.mingyu/slum/shp'
    save_dir = '/intelnvme04/jiang.mingyu/slum1/data/GHS-built/slum'
    os.makedirs(save_dir, exist_ok=True)

    tif_list = glob.glob(os.path.join(tif_dir, '*.tif'))
    for tif_path in tif_list:

        tif_name = os.path.basename(tif_path)
        city_name, year, _ = tif_name.split('-')
        shp_path = os.path.join(shp_dir, tif_shp_mach_dict[city_name])

        save_path = os.path.join(save_dir, tif_name.replace('RES', 'slum'))
        function_single(
            tif_path, shp_path, save_path,
            target_values=(0, 1) if year == '2010' else (0, 2)
        )

        print(tif_name)
