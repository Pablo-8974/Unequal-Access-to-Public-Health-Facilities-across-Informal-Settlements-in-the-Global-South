import os

import numpy as np
from osgeo import gdal
import glob
import pandas as pd

def output_csv(raster, csv_save_path):
    pop_count = dict()
    element_mask = raster > 0

    element_count = list(raster[element_mask])
    element_len = len(element_count)

    pop_count['speed'] = element_count

    df = pd.DataFrame(pop_count)
    df.to_csv(csv_save_path, index=False)
    print('Output xlsx file to', csv_save_path, '\tWith len:', element_len)


distance_raster_dir = '/intelnvme04/jiang.mingyu/slum/RelativeSpeed/Raster/non_slum'	# -------------------
time_raster_dir = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/Health/ProportionInPopulation/non_slum'	# -------------------
save_dir = '/intelnvme04/jiang.mingyu/slum/RelativeSpeed/Weighted/non_slum'	# -------------------

os.makedirs(save_dir, exist_ok=True)
distance_raster_list = glob.glob(os.path.join(distance_raster_dir, '*.tif'))
for distance_raster in distance_raster_list:
    city_name = os.path.basename(distance_raster)
    time_raster = os.path.join(time_raster_dir, city_name.replace('-non_slum.tif', '_non_slum_distance.tif'))	# -------------------non_

    if not os.path.isfile(distance_raster):
        print(distance_raster)
    if not os.path.isfile(time_raster):
        print(time_raster)

    _distance_raster = gdal.Open(distance_raster).ReadAsArray()
    _time_raster = gdal.Open(time_raster).ReadAsArray()
    distance_mask = _distance_raster <= 3000	# -------------------
    _distance_raster = np.where(distance_mask, _distance_raster, np.nan)

    time_raster_time = _time_raster[1]
    time_raster_population = _time_raster[0]
    time_raster_time = np.where(distance_mask, time_raster_time, np.nan)
    time_raster_population = np.where(distance_mask, time_raster_population, np.nan)

    time_raster_time = np.where(time_raster_time<=120, time_raster_time, np.nan)
    time_raster_time = np.where(time_raster_time>0, time_raster_time, np.nan)
    time_raster_time = np.where(np.isfinite(time_raster_time), time_raster_time, np.nan)
    nan_mask = time_raster_time == np.nan

    total_population = np.sum(time_raster_population[time_raster_population>0])
    relative_speed = (_distance_raster / (time_raster_time * 60)) * time_raster_population
    relative_speed[nan_mask] = np.nan

    output_csv(relative_speed,
               os.path.join(save_dir, f'{city_name.replace("tif", "csv")}')
               )
    print(city_name)

