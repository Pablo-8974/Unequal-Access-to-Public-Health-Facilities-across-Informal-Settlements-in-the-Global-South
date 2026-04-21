# Unequal Access to Public Health Facilities across Informal Settlements in the Global South

This repository contains the source code and data processing workflow for the paper:

> **Unequal Access to Public Health Facilities across Informal Settlements in the Global South**

The code supports the full analytical pipeline, including population raster preprocessing, informal settlement separation, medical facility accessibility assessment, walking-time-based network analysis, and relative walking speed estimation.

---

## 📂 Project Structure Overview

The workflow is organized into **11 main methodological steps**, consistent with the paper.
The origin files in Pic dictionary is avaliable at https://doi.org/10.5281/zenodo.19676385, please go to the website to get these files.

---

## 1️⃣ Residential Population Raster Preparation

### 1.1 Download population raster

- Source: Global Human Settlement Layer (GHSL)  
  https://human-settlement.emergency.copernicus.eu/download.php

Download both **total population** and **non-residential population** rasters.

### 1.2 Extract residential regions

```bash
1.2.GHSExtractResidential.py
```

---

## 2️⃣ Informal Settlement (Slum) and Non‑Slum Population Separation

### 2.1 Informal settlement boundary data

- Source (Zenodo):  
  https://doi.org/10.5281/zenodo.18606153

### 2.2 Extract slum population raster

```bash
2.2.CropPopulationFromModelShp.py
```

### 2.3 Extract non‑slum population raster

```bash
2.3.SplitSlumAndnonSlum.py
```

---

## 3️⃣ Sub‑Region Boundary Generation

### 3.1 Convert population raster to shapefile

Run separately for **slum** and **non‑slum** rasters (update output suffix accordingly):

```bash
3.1.GetSubRegionShp.py
```

---

## 4️⃣ Medical Facility Location Data

### 4.1 Data source

- Healthsites.io:  
  https://healthsites.io/map

> Data accessed for the paper: **1 December 2025**

### 4.2 Convert facility polygons into point locations

Centroids are extracted and saved as both `.csv` and point shapefiles:

```bash
4.2.GetCenterOfShp.py
```

---

## 5️⃣ Road Network and Node Preparation

### 5.1 Road network data

Sources:
- https://www.openstreetmap.org/
- https://download.geofabrik.de/

### 5.2 Planarize road intersections (ArcGIS Pro)

```text
Edit → Modify → Planarize
```

Use the **auto‑detected tolerance**.

### 5.3 Segment road network by distance

```bash
5.3.BreakRoadByDistance.py
```

---

## 6️⃣ Population‑Based Euclidean Distance Analysis

### 6.1 Distance from population raster to medical facilities

```bash
6.1.RasterToPointDIstanceRe.py
```

### 6.2 Merge continent‑level results

```bash
6.2.ExcelMergeInRegion.py
```

---

## 7️⃣ Road‑Node‑Based Walking Time Accessibility

### 7.1 Compute walking‑time costs

```bash
7.1.Accessibility.py
```

### 7.2 Split road nodes by residential type

```bash
7.2.SplitSlumAndNonSlum-RoadNode.py
```

---

## 8️⃣ Population Coverage within Walking‑Time Thresholds

### 8.1 Map walking time to population raster

```bash
8.1.MappingRoadNodeToPopulationRaster.py
```

### 8.2 Cumulative population proportion analysis

```bash
8.2.GetPopulationProportion.py
```

---

## 9️⃣ Relative Walking Speed (Raster‑Based)

Relative walking speed is defined as:

```text
Relative Speed = Euclidean Distance / Walking Time
```

```bash
9.RelativeSpeed-Raster.py
```

---

## 🔟 Relative Walking Speed (Road‑Node‑Based)

```bash
10.RelativeSpeed-RodeNode.py
```

Medical facility locations are obtained from **Step 4.2**.

---

## 1️⃣1️⃣ Population‑Weighted Relative Walking Speed

```bash
11.RelativeSpeed-PP.py
```

Inputs:
- Distance raster
- Walking‑time raster

---

## 🧰 Software & Environment

- Python ≥ 3.8
- ArcGIS Pro (required for planarization)
- Python libraries:
  - geopandas
  - rasterio
  - shapely
  - numpy
  - pandas

---

## 📄 Citation

The manuscript is now:

> *Unequal Access to Public Health Facilities across Informal Settlements in the Global South*

---

## ✉️ Contact

jiangmy.pablo@gmail.com 
