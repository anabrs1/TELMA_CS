# Land Use Change Modeling System

A local script-based system for Land Use Change Modelling based on the CLUM repository methodology.

## Features
- Complete CORINE Land Cover classification system (50+ land use codes)
- Data ingestion from local raster files
- Preprocessing with configurable focus on cropland transitions
- Random Forest modeling with hyperparameter tuning
- ROC AUC and Boyce Index validation metrics
- Spatial probability map generation in GeoTIFF format
- Configurable pipeline with comprehensive logging

## Land Use Classification

The system uses the CORINE Land Cover classification mapped to simplified classes:

| Class | Description | CORINE Codes |
|-------|-------------|--------------|
| 0 | null | 122, 123, 124, 131, 132, 133, 141, 142, 335, 411, 412, 421, 422, 423, 511, 512, 521, 522, 523 |
| 1 | Urban | 111, 112 |
| 2 | Industrial | 121 |
| 3 | Arable (Cropland) | 211, 212, 213, 241, 242, 243 |
| 4 | PermanentCrops | 221, 222, 223 |
| 5 | Pastures | 231, 244 |
| 6 | ForestsMature | 311, 312, 313 |
| 7 | TransWoodlandShrub | 321, 322, 323, 334 |
| 14 | SHVA | 331, 332, 333 |
| 15 | ForestYoung | 324 |
| 999 | nodata | 999 |

## Installation

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev

# Install Python dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
# Model all land use transitions
python run_pipeline.py --input-dir data/input --output-dir outputs

# Focus only on cropland transitions (class 3)
python run_pipeline.py --input-dir data/input --output-dir outputs --focus-cropland

# Use custom configuration
python run_pipeline.py --config config/custom_config.yaml
```

### Configuration

Edit `config/default_config.yaml` to customize:

```yaml
land_use:
  focus_on_cropland_transitions: false  # Set to true for cropland focus
  cropland_class: 3
  all_classes: [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 999]

modeling:
  hyperparameter_tuning: true
  n_estimators_range: [50, 100, 200]
  max_depth_range: [10, 20, 30]

validation:
  metrics: ["roc_auc", "boyce_index"]
```

## Data Structure

Expected input files in the input directory:
- `land_use_06.tif` - Land use map for 2006
- `land_use_12.tif` - Land use map for 2012  
- `land_use_18.tif` - Land use map for 2018
- `transition_06_12.tif` - Land use transitions 2006-2012
- `transition_12_18.tif` - Land use transitions 2012-2018
- `land_mask.tif` - Valid land mask
- Additional covariate files (*.tif)
- Geopackage files (*.gpkg) - Vector data with spatial features

### CORINE Data Download

Use the included script to download CORINE Land Cover data:

```bash
# Download all CORINE layers for Andalucía region
python download_corine_data.py --region andalucia --bbox 2840000 2200000 3140000 2500000

# Download only CLC layers
python download_corine_data.py --region andalucia --bbox 2840000 2200000 3140000 2500000 --layers clc

# Download only CHA layers  
python download_corine_data.py --region andalucia --bbox 2840000 2200000 3140000 2500000 --layers cha

# Custom output directory and image size
python download_corine_data.py --region test --bbox 2840000 2200000 2850000 2210000 --output-dir data/input --size 1024 1024
```

## Outputs

- `processed_data.parquet` - Preprocessed sparse data
- `rf_model_{class}.pkl` - Trained Random Forest models
- `probability_map_{class}.tiff` - Spatial probability maps
- `validation_metrics.json` - Model performance metrics
- `roc_curve_{class}.png` - ROC curve plots
- `boyce_index_{class}.png` - Boyce index plots

## Testing

```bash
# Test land use classification system
python test_classification.py

# Test with sample data
python run_pipeline.py --input-dir data/sample --output-dir test_outputs
```
