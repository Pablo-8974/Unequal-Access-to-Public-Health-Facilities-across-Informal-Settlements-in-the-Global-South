Source code for paper: Unequal Access to Public Health Facilities across Informal Settlements in the Global South

1. Get residential raster: 
	1.1. Download population raster file from: https://human-settlement.emergency.copernicus.eu/download.php (Both Total and Non-residential file)
	1.2. Get residential region: 1.2.GHSExtractResidential.py

2. Split slum and non-slum raster:
	2.1. Get slum shp file from: https://doi.org/10.5281/zenodo.18606153
	2.2. Get slum raster: 2.2.CropPopulationFromModelShp.py
	2.3. Get non-slum raster: 2.3.SplitSlumAndnonSlum.py

3. Get region's shp file (for latter raster crop):
	3.1. Transform residential raster into shp: 3.1.GetSubRegionShp.py (for both slum raster and non-slum raster, remember to change the suffix)

4. Get medical facilities location file:
	4.1. Get medical facilities's location from website: https://healthsites.io/map (in the paper, we access this data at 01, December, 2025)
	4.2 Medical facilities location format change (from vector shp to point shp): 4.2.GetCenterOfShp.py (output geo-location into csv file and shp file)

5. Get road node file:
	5.1. Get road network file from: https://www.openstreetmap.org/ or https://download.geofabrik.de/
	5.2. Break road network cross point in ArcGisPro: Edit->Modify->Planarize, with auto detected tolerance by ArcGisPro
	5.3. Break road network by distance: 5.3.BreakRoadByDistance.py

6. Population based straight line distance betweem residential type and medical facilities evaluation:
	6.1. Get distance: 6.1.RasterToPointDIstanceRe.py
	6.2. Merge output csv by continents: 6.2.ExcelMergeInRegion.py

7. Road node-based walking time cost:
	7.1. Get walking time cost: 7.1.Accessibility.py
	7.2. Crop road node into different residential type: 7.2.SplitSlumAndNonSlum-RoadNode.py

8. Population coverage within certain walking time cost:
	8.1. Get walking time cost of each raster point to medical facilities: 8.1.MappingRoadNodeToPopulationRaster.py
	8.2. Cumulative population proportions of medical service accessibility by walking time: 8.2.GetPopulationProportion.py

9. Relative speed. Split residential region into different distance group (straight line):
	9.RelativeSpeed-Raster.py, distance_raster from 4.3, time raster from 6

10. Relative speed. Split residential region into different distance group (road node):
	10.RelativeSpeed-RodeNode.py, medical shp from 4.2

11. Population weighted relative speed:
	11.RelativeSpeed-PP.py, distance_raster from 4.3, time raster from 6.2







