import os

import numpy as np
from osgeo import gdal
import glob
import pandas as pd
from MergeCSVByCol import mergeCSVbycol

def output_csv(raster, csv_save_path):
    pop_count = dict()
    element_mask = raster > 0

    element_count = list(raster[element_mask])
    element_len = len(element_count)

    pop_count['speed'] = element_count

    df = pd.DataFrame(pop_count)
    df.to_csv(csv_save_path, index=False)
    print('Output xlsx file to', csv_save_path, '\tWith len:', element_len)


def single():
    distance_raster_dir = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/Health/Distance/slum_distance_map'  # -------------------
    time_raster_dir = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/Health/ProportionInPopulation/slum'  # -------------------non_
    save_dir = '/intelnvme04/jiang.mingyu/slum/RelativeSpeed/Raster/3km/slum'  # -------------------

    os.makedirs(save_dir, exist_ok=True)
    distance_raster_list = glob.glob(os.path.join(distance_raster_dir, '*.tif'))
    for distance_raster in distance_raster_list:
        city_name = os.path.basename(distance_raster)
        time_raster = os.path.join(time_raster_dir,
                                   city_name.replace('-non_slum.tif', '_non_slum_distance.tif'))  # -------------------

        # if not os.path.isfile(distance_raster):
        #     print(distance_raster)
        # if not os.path.isfile(time_raster):
        #     print(time_raster)

        _distance_raster = gdal.Open(distance_raster).ReadAsArray()
        _time_raster = gdal.Open(time_raster).ReadAsArray()
        # if _distance_raster.shape != _time_raster.shape[1:]:
        #     print(city_name, 'size not match.', 'distance', _distance_raster.shape, 'time', _time_raster.shape)

        distance_mask = _distance_raster <= 3000  # -------------------
        _distance_raster = np.where(distance_mask, _distance_raster, np.nan)

        time_raster_time = np.where(distance_mask, _time_raster[1], np.nan)
        time_raster_time = np.where(time_raster_time <= 120, time_raster_time, np.nan)
        time_raster_time = np.where(time_raster_time > 0, time_raster_time, np.nan)
        time_raster_time = np.where(np.isfinite(time_raster_time), time_raster_time, np.nan)

        relative_speed = _distance_raster / (time_raster_time * 60)
        output_csv(relative_speed,
                   os.path.join(save_dir, f'{city_name.replace("tif", "csv")}')
                   )
        print(city_name)


distance_raster_dir = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/Health/Distance/slum_distance_map'	# -------------------
time_raster_dir = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/Health/ProportionInPopulation/slum'	# -------------------non_

for distance_scale in [3000, 5000, 10000, None]:
    save_dir = f'/intelnvme04/jiang.mingyu/slum/RelativeSpeed/Raster/{"full" if distance_scale is None else distance_scale // 1000}km/slum'	# -------------------

    os.makedirs(save_dir, exist_ok=True)
    distance_raster_list = glob.glob(os.path.join(distance_raster_dir, '*.tif'))
    for distance_raster in distance_raster_list:
        city_name = os.path.basename(distance_raster)
        print(city_name)
        time_raster = os.path.join(time_raster_dir, city_name.replace('_Slum_Distance.tif', '_slum_distance.tif'))	# -------------------

        # if not os.path.isfile(distance_raster):
        #     print(distance_raster)
        # if not os.path.isfile(time_raster):
        #     print(time_raster)

        _distance_raster = gdal.Open(distance_raster).ReadAsArray()
        _time_raster = gdal.Open(time_raster).ReadAsArray()

        distance_mask = _distance_raster <= distance_scale
        _distance_raster = np.where(distance_mask, _distance_raster, np.nan)

        time_raster_time = np.where(distance_mask, _time_raster[1], np.nan)
        time_raster_time = np.where(np.isfinite(time_raster_time), time_raster_time, np.nan)

        relative_speed = _distance_raster / (time_raster_time * 60)
        output_csv(relative_speed,
                   os.path.join(save_dir, f'{city_name.replace("tif", "csv")}')
                   )

    mergeCSVbycol(save_dir, os.path.join(save_dir, 'merge.csv'))
