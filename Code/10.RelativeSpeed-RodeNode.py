import glob
import os

import geopandas as gpd
import numpy as np
from shapely.strtree import STRtree


def get_csv(shp, output_csv, speed_field="relative_s", distance_field='nearest_di', distance_scale=10000):
    import pandas as pd
    series_dict = {}
    gdf = gpd.read_file(shp)

    # col_name = os.path.splitext(os.path.basename(shp))[0]
    if distance_scale is not None:
        gdf = gdf[gdf[distance_field] <= distance_scale]
    s = pd.Series(gdf[speed_field].values, name='speed')
    series_dict['speed'] = s

    df = pd.concat(series_dict.values(), axis=1)

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")


def get_speed(research_shp, medical_shp, output_shp):

    gdf_med = gpd.read_file(medical_shp)
    gdf_res = gpd.read_file(research_shp)

    if gdf_med.crs.is_geographic:
        gdf_med = gdf_med.to_crs(epsg=3857)
    if gdf_res.crs.is_geographic:
        gdf_res = gdf_res.to_crs(epsg=3857)
    if gdf_med.crs != gdf_res.crs:
        gdf_med = gdf_med.to_crs(gdf_res.crs)

    medical_geoms = list(gdf_med.geometry)
    tree = STRtree(medical_geoms)

    def nearest_distance(point):
        nearest_geom = medical_geoms[tree.nearest(point)]
        return point.distance(nearest_geom)

    gdf_res["nearest_dist_m"] = gdf_res.geometry.apply(nearest_distance)

    gdf_res = gdf_res[gdf_res["min_time_m"] > 1]
    gdf_res["relative_speed_ms"] = np.where(
        gdf_res["min_time_m"] > 0,
        gdf_res["nearest_dist_m"] / (gdf_res["min_time_m"] * 60),
        np.nan
    )

    gdf_res.to_file(
        output_shp,
        encoding="utf-8"
    )

    print("✅")


if __name__ == '__main__':
    medical_shp_dir = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/Health/CityHealthPoint'
    research_shp_dir = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/Health/TimeCost/HealthRoadNodesAccessTimeCostCropped/slum'
    shp_output_dir = '/intelnvme04/jiang.mingyu/slum/RelativeSpeed/RodeNode/slum'
    csv_output_dir = '/intelnvme04/jiang.mingyu/slum/RelativeSpeed/RodeNode/slum'

    os.makedirs(shp_output_dir, exist_ok=True)
    research_list = glob.glob(os.path.join(research_shp_dir, '*.shp'))
    for research_shp_path in research_list:
        city_name = os.path.basename(research_shp_path).replace('_slum_distance.shp', '')
        medical_shp_path = os.path.join(medical_shp_dir, city_name + '_health_institute_point.shp')
        output_shp_path = os.path.join(shp_output_dir, city_name + '.shp')
        output_csv_path = os.path.join(csv_output_dir, city_name + '.csv')

        # if not os.path.isfile(research_shp_path):
        #     print(research_shp_path)
        # if not os.path.isfile(medical_shp_path):
        #     print(medical_shp_path)

        get_speed(research_shp_path, medical_shp_path, output_shp_path)
        get_csv(output_shp_path, output_csv_path, distance_scale=3000)
        print(city_name)

