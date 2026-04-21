# -*- coding: utf-8 -*-

import glob
import os
import math
import geopandas as gpd
from shapely.geometry import Point
import networkx as nx

TARGET_CRS = "EPSG:3857"
UNIFORM_SPEED_KMH = 3.96
TIME_BINS_MIN = [5, 10, 15, 20, 30, 45, 60]


def ensure_projected(gdf: gpd.GeoDataFrame, target_crs: str) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("no crs")
    if str(gdf.crs).lower() != str(target_crs).lower():
        return gdf.to_crs(target_crs)
    return gdf

def build_graph_from_lines(roads_gdf: gpd.GeoDataFrame, speed_kmh: float) -> tuple[nx.Graph, gpd.GeoDataFrame]:
    node_records = []
    edges = []
    coord_to_id = {}
    next_node_id = 0

    for _, row in roads_gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        lines = []
        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = list(geom.geoms)
        else:
            continue

        for line in lines:
            if line.length == 0:
                continue
            start = Point(line.coords[0])
            end = Point(line.coords[-1])

            sx, sy = start.x, start.y
            ex, ey = end.x, end.y

            if (sx, sy) not in coord_to_id:
                coord_to_id[(sx, sy)] = next_node_id
                node_records.append({"node_id": next_node_id, "geometry": start})
                next_node_id += 1
            u = coord_to_id[(sx, sy)]

            if (ex, ey) not in coord_to_id:
                coord_to_id[(ex, ey)] = next_node_id
                node_records.append({"node_id": next_node_id, "geometry": end})
                next_node_id += 1
            v = coord_to_id[(ex, ey)]

            length_m = float(line.length)
            time_min = (length_m / 1000.0) / speed_kmh * 60.0

            edges.append({"u": u, "v": v, "length_m": length_m, "time_min": time_min})

    nodes_gdf = gpd.GeoDataFrame(node_records, geometry="geometry", crs=roads_gdf.crs)

    G = nx.Graph()
    for _, nrow in nodes_gdf.iterrows():
        G.add_node(int(nrow["node_id"]))

    for e in edges:
        G.add_edge(int(e["u"]), int(e["v"]), length_m=e["length_m"], time_min=e["time_min"])

    return G, nodes_gdf

def snap_points_to_nearest_nodes(points_gdf: gpd.GeoDataFrame, nodes_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    snapped = gpd.sjoin_nearest(points_gdf, nodes_gdf[["node_id", "geometry"]],
                                how="left", distance_col="snap_dist")
    return snapped

def multi_source_shortest(G: nx.Graph, sources: list[int], weight: str) -> dict[int, float]:
    return nx.multi_source_dijkstra_path_length(G, sources=sources, weight=weight)

def classify_time_bins(t: float, bins: list[float]) -> str:
    if t is None or math.isinf(t):
        return "不可达"
    prev = 0
    for b in bins:
        if t <= b:
            return f"{prev}-{b}min" if prev > 0 else f"<= {b}min"
        prev = b
    return f"> {bins[-1]}min"

def main():
    print('Loading file:', city_road_shp_path)
    roads = gpd.read_file(city_road_shp_path)
    print('Loading file:', city_element_shp_path)
    hosps = gpd.read_file(city_element_shp_path)
    print('Re Project roads')
    roads = ensure_projected(roads, TARGET_CRS)
    print('Re Project hosps:')
    hosps = ensure_projected(hosps, TARGET_CRS)

    print('Clear invalid polygon')
    roads = roads[roads.geometry.notna() & (~roads.geometry.is_empty)].copy()
    hosps = hosps[hosps.geometry.notna() & (~hosps.geometry.is_empty)].copy()

    print('build graph from lines')
    G, nodes_gdf = build_graph_from_lines(roads, speed_kmh=UNIFORM_SPEED_KMH)

    snapped_hosps = snap_points_to_nearest_nodes(hosps, nodes_gdf)
    hospital_nodes = [int(nid) for nid in snapped_hosps["node_id"].tolist()]

    if len(hospital_nodes) == 0:
        raise ValueError("医院点吸附后为空，请检查医院数据或坐标系。")

    min_time = multi_source_shortest(G, hospital_nodes, weight="time_min")

    nodes_gdf["min_time_min"] = nodes_gdf["node_id"].map(min_time).fillna(float("inf"))
    nodes_gdf["time_class"] = nodes_gdf["min_time_min"].apply(lambda t: classify_time_bins(t, TIME_BINS_MIN))
    nodes_gdf.to_file(out_put_path)
    print(f"[OK] save to {out_put_path}")

if __name__ == "__main__":
    city_road_shp_dir = '/intelnvme04/jiang.mingyu/slum1/data/Accessbility/CityRoadShp-2025'
    city_element_shp_dir = '/intelnvme04/jiang.mingyu/slum1/data/Accessbility/CityHealthPoint-history'
    output_dir = '/intelnvme04/jiang.mingyu/slum1/data/Accessbility/2010/With2025RoadNetwork/RoadNode-Result'
    os.makedirs(output_dir, exist_ok=True)

    city_element_shp_list = glob.glob(os.path.join(city_element_shp_dir, '*.shp'))
    for sub_city_element_shp_path in city_element_shp_list:
        element_base_name = os.path.basename(sub_city_element_shp_path).replace('_health_institute_point.shp', '')

        city_road_shp_path = os.path.join(city_road_shp_dir, element_base_name + '_road.shp')
        city_element_shp_path = sub_city_element_shp_path
        out_put_path = os.path.join(output_dir, element_base_name + '_AccessTimeCost.shp')

        if not os.path.exists(city_road_shp_path):
            print(element_base_name, 'city road shp file not exist in', city_road_shp_path)
        if not os.path.exists(city_element_shp_path):
            print(element_base_name, 'city element file not exist in', city_element_shp_path)
        print(f'Compute {city_road_shp_path} with {city_element_shp_path}\n')
        main()

    print('Totally', len(city_element_shp_list), 'files have been processed!')
