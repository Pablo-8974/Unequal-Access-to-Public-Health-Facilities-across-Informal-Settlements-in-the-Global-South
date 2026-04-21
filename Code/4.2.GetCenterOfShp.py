import geopandas as gpd
import csv
import os
import glob

shp_path = r'C:\Users\k\Desktop\slum\paper\data\Accessibility\School\CitySchoolShape'
save_path = r'C:\Users\k\Desktop\slum\paper\data\Accessibility\School\CitySchoolPoint\Excel'

city_list = glob.glob(os.path.join(shp_path, '*.shp'))
os.makedirs(save_path, exist_ok=True)
for city in city_list:
    file_name = os.path.basename(city)
    city_name, suffix = file_name.split('.')

    in_shp = os.path.join(shp_path, city)
    out_csv = os.path.join(save_path, city_name + '_point.csv')
    gdf = gpd.read_file(in_shp)

    if gdf.crs is None:
        raise ValueError("CRS don't exist")

    if not gdf.crs.is_geographic:
        gdf = gdf.to_crs(epsg=4326)

    with open(out_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["poly_id", "longitude", "latitude"])

        for idx, geom in enumerate(gdf.geometry):
            if geom.is_empty or geom is None:
                continue
            centroid = geom.centroid
            writer.writerow([idx + 1, centroid.x, centroid.y])

    print(f"save to {out_csv}")


