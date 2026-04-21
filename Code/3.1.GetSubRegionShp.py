import os

import glob
from osgeo import gdal, ogr, osr


def raster_to_shapefile(input_raster, output_shapefile, target_value=1):
    # 打开输入栅格
    print("Raster to shp file")
    src_ds = gdal.Open(input_raster)
    if src_ds is None:
        raise ValueError("open error")

    band = src_ds.GetRasterBand(1)
    prj = src_ds.GetProjection()
    gt = src_ds.GetGeoTransform()

    driver = ogr.GetDriverByName("Memory")
    temp_ds = driver.CreateDataSource("temp")

    srs = osr.SpatialReference()
    srs.ImportFromWkt(prj)

    temp_layer = temp_ds.CreateLayer("polygons", srs, ogr.wkbPolygon)
    temp_layer.CreateField(ogr.FieldDefn("DN", ogr.OFTInteger))

    gdal.Polygonize(band, None, temp_layer, 0, [], callback=None)

    out_driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(output_shapefile):
        out_driver.DeleteDataSource(output_shapefile)
    out_ds = out_driver.CreateDataSource(output_shapefile)
    out_layer = out_ds.CreateLayer("polygons", srs, ogr.wkbPolygon)
    out_layer.CreateField(ogr.FieldDefn("value", ogr.OFTInteger))

    # 筛选目标值的要素并写入输出文件
    for feature in temp_layer:
        if feature.GetField("DN") > target_value:
            out_feature = ogr.Feature(out_layer.GetLayerDefn())
            out_feature.SetGeometry(feature.GetGeometryRef().Clone())
            out_feature.SetField("value", 1)
            out_layer.CreateFeature(out_feature)
            out_feature = None

    # 关闭所有数据集
    temp_ds = None
    out_ds = None
    src_ds = None

    print(f"成功创建shapefile: {output_shapefile}")
    return output_shapefile


def dir_loop():
    raster_dir = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2010\DistanceMap-2010-10km\DistanceMap-nonSlumArea"
    raster_suffix = '_distance_10km_non-slum.tif'

    save_dir = os.path.join(os.path.dirname(raster_dir), 'slum-shp')

    os.makedirs(save_dir, exist_ok=True)
    raster_list = glob.glob(os.path.join(raster_dir, '*.tif'))
    for raster_path in raster_list:
        # Cairo_distance_3km_non-slum.tif
        city_name = os.path.basename(raster_path).replace(raster_suffix, '')
        save_path = os.path.join(save_dir, city_name + '.shp')

        raster_to_shapefile(raster_path, save_path, 0)
        print(raster_path, '->', save_path)

if __name__ == '__main__':
    dir_loop()
