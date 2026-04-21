
# -*- coding: utf-8 -*-
import glob
import math
import os

import geopandas as gpd
from typing import Optional, List
from shapely.geometry import LineString, MultiLineString, MultiPoint
from shapely.ops import split, linemerge

try:
    from shapely.ops import substring  # Shapely 2.0+
    HAS_SUBSTRING = True
except Exception:
    HAS_SUBSTRING = False


def _split_by_measures_substring(line: LineString, max_len: float) -> List[LineString]:
    L = float(line.length)
    if L == 0 or L <= max_len:
        return [line]

    n = int(math.ceil(L / max_len))
    step = L / n

    parts = []
    start = 0.0
    for i in range(n):
        end = min(start + step, L)
        seg = substring(line, start, end)
        if isinstance(seg, LineString) and seg.length > 0:
            parts.append(seg)
        start = end

    return parts if parts else [line]


def _split_by_points_split(line: LineString, max_len: float) -> List[LineString]:
    L = float(line.length)
    if L == 0 or L <= max_len:
        return [line]

    n = int(math.ceil(L / max_len))
    distances = [L * i / n for i in range(1, n)]

    points = []
    for d in distances:
        try:
            pt = line.interpolate(d)
            points.append(pt)
        except Exception:
            pass

    if not points:
        return [line]

    try:
        parts = split(line, MultiPoint(points))
        geoms = [seg for seg in parts.geoms if isinstance(seg, LineString) and seg.length > 0]
        return geoms if geoms else [line]
    except Exception:
        segments = []
        cur = line
        for pt in points:
            try:
                res = split(cur, pt)
                geoms = [g for g in res.geoms if isinstance(g, LineString) and g.length > 0]
                if len(geoms) == 2:
                    segments.append(geoms[0])
                    cur = geoms[1]
                else:
                    pass
            except Exception:
                pass
        if isinstance(cur, LineString) and cur.length > 0:
            segments.append(cur)
        merged = linemerge(MultiLineString(segments)) if len(segments) > 1 else segments[0]
        if isinstance(merged, MultiLineString):
            return [s for s in merged.geoms if s.length > 0]
        elif isinstance(merged, LineString):
            return [merged]
        else:
            return [line]


def split_line_equal(line: LineString, max_len: float = 100.0) -> List[LineString]:
    if HAS_SUBSTRING:
        return _split_by_measures_substring(line, max_len)
    else:
        return _split_by_points_split(line, max_len)


def segment_roads(input_path: str,
                  output_path: str,
                  target_crs: str = "EPSG:3857",
                  max_len_m: float = 100.0,
                  keep_fields: Optional[List[str]] = None,
                  assume_src_crs: Optional[str] = None,
                  verbose: bool = True):

    gdf = gpd.read_file(input_path)
    if gdf.empty:
        raise ValueError("input error")

    total_in = len(gdf)
    if verbose:
        print(f"[INFO] {total_in}")

    # 处理 CRS
    original_crs = gdf.crs
    if gdf.crs is None:
        if assume_src_crs is None:
            raise ValueError("no crs")
        gdf = gdf.set_crs(assume_src_crs)
        if verbose:
            print(f"[INFO] set CRS = {assume_src_crs}")

    gdf = gdf.to_crs(target_crs)
    if verbose:
        print(f"[INFO]  {target_crs}")

    # 只保留线要素
    gdf = gdf[gdf.geometry.notna()]
    gdf = gdf[gdf.geometry.geom_type.isin(["LineString", "MultiLineString"])]
    if gdf.empty:
        raise ValueError("no（LineString/MultiLineString）。")

    # explode MultiLineString
    try:
        gdf = gdf.explode(ignore_index=True)
    except TypeError:
        gdf = gdf.explode(index_parts=True, ignore_index=True)

    if verbose:
        # 粗略长度统计
        lens = gdf.geometry.length
        print(f"[INFO] min={lens.min():.3f}, median={lens.median():.3f}, max={lens.max():.3f}")
        n_long = int((lens > max_len_m).sum())
        print(f"[INFO]  {max_len_m} m {n_long}")

    # 决定保留的属性
    if keep_fields is None:
        keep_fields = [c for c in gdf.columns if c != "geometry"]
    else:
        keep_fields = [c for c in keep_fields if c in gdf.columns]

    out_records = []
    cut_count_lines = 0
    unchanged_lines = 0

    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        lines = []
        if isinstance(geom, MultiLineString):
            lines = [seg for seg in geom.geoms if isinstance(seg, LineString)]
        elif isinstance(geom, LineString):
            lines = [geom]
        else:
            continue

        for line in lines:
            L = float(line.length)
            if L > max_len_m:
                parts = split_line_equal(line, max_len=max_len_m)
                if len(parts) > 1:
                    cut_count_lines += 1
                else:
                    unchanged_lines += 1  # 理论应切但结果没切，后面日志会提示
            else:
                parts = [line]
                unchanged_lines += 1

            for p in parts:
                if not isinstance(p, LineString) or p.is_empty or p.length == 0:
                    continue
                attrs = {f: row[f] for f in keep_fields}
                attrs["geometry"] = p
                out_records.append(attrs)

    if verbose:
        print(f"[INFO] （L > {max_len_m}）：{int((gdf.geometry.length > max_len_m).sum())}")
        print(f"[INFO] ：{cut_count_lines}")
        print(f"[INFO] ：{unchanged_lines}")

    if not out_records:
        raise RuntimeError("no output")

    out_gdf = gpd.GeoDataFrame(out_records, crs=gdf.crs)
    out_gdf["seg_len_m"] = out_gdf.geometry.length
    out_gdf = out_gdf.to_crs(original_crs)

    # 写出
    out_gdf.to_file(output_path)
    if verbose:
        print(f"[INFO] ：{len(out_gdf)} -> {output_path}")
    print('File save at', output_path)


if __name__ == "__main__":
    input_file = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\CityRoadShp-history\CityRoadNetwork\Mumbai.shp"
    output_file = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\CityRoadShp-history\Mumbai.shp"

    segment_roads(
        input_path=input_file,
        output_path=output_file,
        target_crs="EPSG:3857",     # change according to where is the city
        max_len_m=100.0,
        keep_fields=None,
        verbose=False
    )
