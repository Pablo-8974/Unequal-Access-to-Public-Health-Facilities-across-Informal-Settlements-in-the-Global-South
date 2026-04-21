import glob

from osgeo import gdal
import os
import numpy as np

def save_tif(array, save_path, geotransform=None, projection=None):
    driver = gdal.GetDriverByName('GTiff')
    if len(array.shape) == 2:
        array = array[..., None]
    ndvi_ds = driver.Create(save_path, array.shape[1], array.shape[0], array.shape[2], gdal.GDT_Byte)
    for band in range(array.shape[2]):
        ndvi_ds.GetRasterBand(band + 1).WriteArray(array[:, :, band])

    if geotransform is not None:
        ndvi_ds.SetGeoTransform(geotransform)
    if projection is not None:
        ndvi_ds.SetProjection(projection)

    del ndvi_ds  # 写出文件后关闭文件


def exclude_function(total_file_path, NRES_file_path, save_path):
    total_raster = gdal.Open(total_file_path)
    NRES_raster = gdal.Open(NRES_file_path).ReadAsArray()

    geotransform = total_raster.GetGeoTransform()
    projection = total_raster.GetProjection()

    total_raster = total_raster.ReadAsArray()
    assert total_raster.shape == NRES_raster.shape, f'{os.path.basename(total_file_path)} pixel not match! Passed!'

    NRES_mask = NRES_raster > 0
    total_raster[NRES_mask] = 0
    total_raster[total_raster>0] = 1

    save_tif(total_raster, save_path, geotransform, projection)


def slum_nonslum_loop():
    total_file_dir = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\GHS-built\residential"
    NRES_file_dir = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\GHS-built\slum"
    save_dir = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\GHS-built\non-slum"

    total_file_list = glob.glob(os.path.join(total_file_dir, '*.tif'))
    for total_file_path in total_file_list:
        total_file_name = os.path.basename(total_file_path)
        NRES_file_path = os.path.join(NRES_file_dir, total_file_name.replace('RES', 'slum'))
        save_path = os.path.join(save_dir, total_file_name.replace('RES', 'non-slum'))
        exclude_function(total_file_path, NRES_file_path, save_path)
        print(total_file_name)


if __name__ == '__main__':
    slum_nonslum_loop()