
import os
import math
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import rowcol
import glob

def main(shp_in, mask_tif, shp_out, csv_out):
    # ========= 写死的变量（按需修改） =========
    # shp_in       = r"D:\data\points.shp"
    # mask_tif     = r"D:\data\mask.tif"
    # shp_out      = r"D:\data\points_clipped_by_mask.shp"
    # csv_out      = r"D:\data\points_clipped_by_mask.csv"
    keep_value   = 1
    write_rowcol = True
    write_xy     = False

    with rasterio.open(mask_tif) as src_mask:
        mask_crs = src_mask.crs
        mask_transform = src_mask.transform
        mask_nodata = src_mask.nodata
        mask_dtype = src_mask.dtypes[0]
        height, width = src_mask.height, src_mask.width
        if src_mask.count != 1:
            raise ValueError(f"want single band file，but {src_mask.count} bands detected")

        gdf = gpd.read_file(shp_in)
        if gdf.empty:
            raise ValueError("empty")

        if gdf.geometry.geom_type.isin(["MultiPoint"]).any():
            gdf = gdf.explode(index_parts=False, ignore_index=True)

        if not gdf.geometry.geom_type.isin(["Point"]).all():
            raise ValueError("Should be all recorded in point")

        if gdf.crs is None:
            raise ValueError("no crs")
        if gdf.crs != mask_crs:
            gdf = gdf.to_crs(mask_crs)

        xs = gdf.geometry.x.values
        ys = gdf.geometry.y.values
        rr, cc = rowcol(mask_transform, xs, ys)
        rr = np.asarray(rr, dtype=np.int64)
        cc = np.asarray(cc, dtype=np.int64)

        in_bounds = (rr >= 0) & (rr < height) & (cc >= 0) & (cc < width)
        total_pts = len(gdf)
        in_bounds_count = int(in_bounds.sum())
        print(f"{total_pts}，{in_bounds_count}")

        coords_in = list(zip(xs[in_bounds], ys[in_bounds]))
        vals_in = np.fromiter((v[0] for v in src_mask.sample(coords_in)),
                              dtype=np.float64, count=in_bounds_count)

        if mask_nodata is None:
            if mask_dtype.startswith("float"):
                keep_in = np.isfinite(vals_in)
            else:
                keep_in = np.ones_like(vals_in, dtype=bool)
        else:
            if isinstance(mask_nodata, float) and math.isnan(mask_nodata):
                keep_in = np.isfinite(vals_in)
            else:
                keep_in = np.isfinite(vals_in) & (vals_in != float(mask_nodata))

        kept_in_count = int(keep_in.sum())

        keep = np.zeros(total_pts, dtype=bool)
        idx_inbounds = np.where(in_bounds)[0]
        keep[idx_inbounds[keep_in]] = True

        print(f"满足“非 NoData”条件的点数: {int(keep.sum())}")

        mask_val_full = np.full(total_pts, np.nan, dtype=np.float64)
        mask_val_full[idx_inbounds] = vals_in  # 先填范围内的值

        gdf_keep = gdf.loc[keep].copy()
        gdf_keep["mask_val"] = mask_val_full[keep]

        if write_rowcol and kept_in_count > 0:
            gdf_keep["row"] = rr[keep]
            gdf_keep["col"] = cc[keep]

        if write_xy and kept_in_count > 0:
            gdf_keep["x"] = gdf_keep.geometry.x
            gdf_keep["y"] = gdf_keep.geometry.y

        if keep.any():
            os.makedirs(os.path.dirname(shp_out), exist_ok=True)
            gdf_keep.to_file(shp_out, driver="ESRI Shapefile", encoding="utf-8")
            print(f"已写出裁切后的 Shapefile：{shp_out}")

            df_out = gdf_keep.drop(columns="geometry")
            os.makedirs(os.path.dirname(csv_out), exist_ok=True)
            df_out.to_csv(csv_out, index=False, encoding="utf-8")
            print(f"已写出逐点 CSV：{csv_out}")
        else:
            print("没有任何点落在“非 NoData”像素上，跳过 Shapefile 与 CSV 输出。")


def dir_loop():
    source_shp_dir = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2010\With2025RoadNetwork\RoadNode-Result"
    mask_tif_dir = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2010\DistanceMap-2010-10km\DistanceMap-SlumArea"
    output_tif_dir = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2010\With2025RoadNetwork\RoadNode-SlumArea"  # nonSlumArea SlumArea
    output_csv_dir = output_tif_dir
    source_shp_suffix = '_AccessTimeCost.shp'
    distance = '10km'
    resident_type = 'slum'      # non-slum  slum

    os.makedirs(output_csv_dir, exist_ok=True)
    os.makedirs(output_tif_dir, exist_ok=True)

    source_shp_list = glob.glob(os.path.join(source_shp_dir, '*.shp'))
    for source_shp_path in source_shp_list:
        shp_name = os.path.basename(source_shp_path)
        mask_tif_path = os.path.join(mask_tif_dir, shp_name.replace(source_shp_suffix, f'_distance_{distance}_{resident_type}.tif'))
        output_shp_path = os.path.join(output_tif_dir, shp_name.replace('.shp', f'_{resident_type}.shp'))
        output_csv_path = os.path.join(output_csv_dir, shp_name.replace('.shp', f'_{resident_type}.csv'))

        # if not os.path.isfile(source_shp_path):
        #     print(source_shp_path)
        # if not os.path.isfile(mask_tif_path):
        #     print(mask_tif_path)
        main(source_shp_path, mask_tif_path, output_shp_path, output_csv_path)
        print(shp_name)


if __name__ == "__main__":
    main(
        r"C:\Users\k\Desktop\slum\paper\data\Accessibility\Health\TimeCost\HealthRoadNodesAccessTimeCostWholeCity\Gauteng_AccessTimeCost.shp",
        r"C:\Users\k\Desktop\slum\paper\data\Accessibility\Health\Distance\non_slum_distance_map\Gauteng_non_Slum_Distance.tif",
        r"C:\Users\k\Desktop\slum\paper\data\Accessibility\Health\TimeCost\Gauteng_non_slum_distance.shp",
        r"C:\Users\k\Desktop\slum\paper\data\Accessibility\Health\TimeCost\Gauteng_non_slum_distance.csv",
    )
