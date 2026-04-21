import glob
import os.path

import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import Point
from scipy.spatial import cKDTree
from rasterio.warp import calculate_default_transform, reproject, Resampling


def find_time_field(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    raise ValueError(f"try {candidates}")

def compute_time_with_nodes(nodes_idx, node_times):
    return np.mean(node_times[nodes_idx])

def compute_time_nearest_node(pixel_center, distance_tree, node_times):
    dist, idx = distance_tree.query(pixel_center)
    return node_times[idx]


def mapping_function(population_raster, nodes_file, output_raster):
    with rasterio.open(population_raster) as src:
        profile = src.profile
        profile.update(count=2)
        transform = src.transform

        population_data = src.read(1)
        no_data = src.nodata
        raster_crs = src.crs

        nodes_gdf = gpd.read_file(nodes_file).to_crs(raster_crs)
        tf = find_time_field(nodes_gdf, TIME_FIELD_CANDIDATES)
        vals = nodes_gdf[tf].astype(float)
        vals = vals.replace([np.inf, -np.inf], np.nan)
        valid_mask = (~vals.isna()) & (vals >= 0)
        nodes_gdf = nodes_gdf.loc[valid_mask].copy()
        nodes_gdf.reset_index(drop=True, inplace=True)

        node_coords = np.array([(geom.x, geom.y) for geom in nodes_gdf.geometry])
        node_times = nodes_gdf[tf].values

        tree = cKDTree(node_coords)

        time_data = np.full(population_data.shape, no_data, dtype=np.float32)

        empty_count = 0
        total_count = 0
        for row in range(population_data.shape[0]):
            for col in range(population_data.shape[1]):
                pop_value = population_data[row, col]
                if pop_value <= 0 or np.isnan(pop_value):
                    continue

                x = transform[2] + col * transform[0] + transform[0] / 2
                y = transform[5] + row * transform[4] + transform[4] / 2
                pixel_center = (x, y)

                pixel_polygon = Point(x, y).buffer(transform[0] / 2)
                nodes_in_pixel = nodes_gdf[nodes_gdf.geometry.within(pixel_polygon)].index

                if len(nodes_in_pixel) > 0:
                    time_data[row, col] = compute_time_with_nodes(nodes_in_pixel, node_times)
                    total_count += 1
                else:
                    empty_count += 1

        print(f'Total pixel: {total_count}, invalid pixel: {empty_count}')

        with rasterio.open(output_raster, "w", **profile) as dst:
            dst.write(population_data, 1)
            dst.write(time_data, 2)

    print(f"Save file at {output_raster}")


def dir_loop():
    pop_raster_dir = '/intelnvme04/jiang.mingyu/slum1/data/GHS-pop'
    road_node_shp_dir = '/intelnvme04/jiang.mingyu/slum1/data/Accessbility/2010/With2025RoadNetwork/RoadNode-SlumArea'
    save_dir = '/intelnvme04/jiang.mingyu/slum1/data/Accessbility/2010/With2025RoadNetwork/PopulationRelated-2010-origin/MappingRaster'

    os.makedirs(save_dir, exist_ok=True)
    pop_raster_list = glob.glob(os.path.join(pop_raster_dir, '*.tif'))
    for pop_raster_path in pop_raster_list:
        pop_raster_name = os.path.basename(pop_raster_path)
        if '2025' in pop_raster_name:
            continue

        road_node_shp_path = os.path.join(road_node_shp_dir, pop_raster_name.replace('-2010.tif', '_AccessTimeCost_slum.shp'))
        save_path = os.path.join(save_dir, pop_raster_name)

        if not os.path.isfile(pop_raster_path):
            print(pop_raster_path)
        if not os.path.isfile(road_node_shp_path):
            print(road_node_shp_path)
        print(f'Compute {pop_raster_path} with {road_node_shp_path}\n')

        mapping_function(pop_raster_path, road_node_shp_path, save_path)


if __name__ == '__main__':
    TIME_FIELD_CANDIDATES = ["min_time_min", "min_time_m", "min_time"]

    # 参数设置
    population_raster = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\GHS-pop\CapeTown-2025.tif"  # 人口栅格文件
    nodes_file = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2025\RoadNode-2025-origin\CapeTown_AccessTimeCost.shp"  # 路网节点文件（包含步行时间字段）
    output_raster = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2025\CapeTown-2025.tif"  # 输出文件

    mapping_function(population_raster, nodes_file, output_raster)

    # dir_loop()

