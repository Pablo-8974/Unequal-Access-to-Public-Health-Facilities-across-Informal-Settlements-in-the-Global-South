# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer, Geod
import os
import glob

def compute_nearest_geodesic_distance_double_loop(raster_path, csv_path, out_path, nodata_override=None):

    with rasterio.open(raster_path) as src:
        width, height = src.width, src.height
        transform = src.transform
        raster_crs = src.crs
        profile = src.profile
        data = src.read(1)
        nodata = src.nodata if (src.nodata is not None) else nodata_override
        if nodata is None:
            nodata = -9999

    # CSV	longitude	latitude
    df = pd.read_csv(csv_path)
    df.columns = [c.lower() for c in df.columns]
    if not {"poly_id", "longitude", "latitude"}.issubset(df.columns):
        raise ValueError("CSV must include：id, longitude, latitude")
    df = df.dropna(subset=["longitude", "latitude"])
    if df.empty:
        raise ValueError("CSV no point")
    lon_pts = df["longitude"].to_numpy()
    lat_pts = df["latitude"].to_numpy()

    to_wgs84 = Transformer.from_crs(raster_crs, "EPSG:4326", always_xy=True)
    geod = Geod(ellps="WGS84")

    out = np.empty((height, width), dtype=np.float32)

    for row in range(height):
        for col in range(width):
            if np.isclose(data[row, col], nodata):
                out[row, col] = nodata
                continue

            x = transform.a * (col + 0.5) + transform.b * (row + 0.5) + transform.c
            y = transform.d * (col + 0.5) + transform.e * (row + 0.5) + transform.f

            lon_px, lat_px = to_wgs84.transform(x, y)

            min_dist = float("inf")
            for lon_t, lat_t in zip(lon_pts, lat_pts):
                _, _, dist_m = geod.inv(lon_px, lat_px, lon_t, lat_t)
                if dist_m < min_dist:
                    min_dist = dist_m

            out[row, col] = min_dist

    profile_out = profile.copy()
    profile_out.update({
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "nodata": nodata
    })
    with rasterio.open(out_path, "w", **profile_out) as dst:
        dst.write(out, 1)

    print(out_path)

tif_CSV_mach_dict = {
    'Cairo': 'Cairo', 'CapeTown': 'CapeTown', 'Dar_es_Salaam': 'Dar_es_Salaam', 'Karachi': 'Karachi',
    'Manila': 'Manila', 'Mumbai': 'Mumbai', 'Nairobi': 'Nairobi',
    'Port_au_Prince': 'Port-au-Prince', 'Rio': 'Rio_de_Janeiro'
}
basemap_tif_dir = '/intelnvme04/jiang.mingyu/slum1/data/GHS-built/residential'
element_location_csv_dir = '/intelnvme04/jiang.mingyu/slum1/data/Accessbility/CityHealthPoint-history/Excel'
out_tif_dir = "/intelnvme04/jiang.mingyu/slum1/data/Accessbility/2010/DistanceMap-origin"
csv_base_name = '_health_institute_point.csv'       # _school_point

city_list = glob.glob(os.path.join(basemap_tif_dir, '*.tif'))
os.makedirs(out_tif_dir, exist_ok=True)

for tif_path in city_list:
    tif_name = os.path.basename(tif_path).split('.')[0]
    if '2025' in tif_name:
        continue

    city_name, year, _ = tif_name.split('-')
    csv_path = os.path.join(element_location_csv_dir, tif_CSV_mach_dict[city_name] + csv_base_name)
    out_tif_path = os.path.join(out_tif_dir, city_name + '_distance.tif')

    compute_nearest_geodesic_distance_double_loop(
        raster_path=tif_path,
        csv_path=csv_path,
        out_path=out_tif_path,
        nodata_override=-9999
    )

print('Totally', len(city_list), 'files have been processed!')

