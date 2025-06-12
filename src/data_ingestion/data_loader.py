import rasterio as rio
import pandas as pd
import pyarrow.parquet as pq
import geopandas as gpd
import glob
import os
from pathlib import Path
import logging

class DataLoader:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def load_raster_files(self, input_dir):
        """Load all TIFF files from input directory"""
        tiff_files = glob.glob(os.path.join(input_dir, "*.tif"))
        tiff_files.extend(glob.glob(os.path.join(input_dir, "*.tiff")))
        
        datasets = {}
        for file_path in tiff_files:
            file_name = Path(file_path).stem
            try:
                datasets[file_name] = rio.open(file_path)
                self.logger.info(f"Loaded raster: {file_name}")
            except Exception as e:
                self.logger.error(f"Failed to load {file_path}: {e}")
                
        return datasets
        
    def load_geopackage_files(self, input_dir):
        """Load all geopackage files from input directory"""
        gpkg_files = glob.glob(os.path.join(input_dir, "*.gpkg"))
        
        datasets = {}
        for file_path in gpkg_files:
            file_name = Path(file_path).stem
            try:
                gdf = gpd.read_file(file_path)
                datasets[file_name] = gdf
                self.logger.info(f"Loaded geopackage: {file_name} with {len(gdf)} features")
            except Exception as e:
                self.logger.error(f"Failed to load {file_path}: {e}")
                
        return datasets
        
    def load_all_spatial_files(self, input_dir):
        """Load all spatial files (raster and vector) from input directory"""
        datasets = {}
        
        raster_datasets = self.load_raster_files(input_dir)
        datasets.update(raster_datasets)
        
        gpkg_datasets = self.load_geopackage_files(input_dir)
        datasets.update(gpkg_datasets)
        
        self.logger.info(f"Loaded {len(datasets)} spatial datasets total")
        return datasets
        
    def load_parquet_data(self, file_path):
        """Load parquet data file"""
        try:
            return pq.read_table(file_path)
        except Exception as e:
            self.logger.error(f"Failed to load parquet {file_path}: {e}")
            return None
            
    def validate_data_structure(self, datasets):
        """Validate that required data files are present"""
        required_files = ['land_use_06', 'land_use_12', 'land_use_18', 
                        'transition_06_12', 'transition_12_18', 'land_mask']
        
        missing_files = []
        for req_file in required_files:
            if not any(req_file in name for name in datasets.keys()):
                missing_files.append(req_file)
                
        if missing_files:
            self.logger.warning(f"Missing recommended files: {missing_files}")
            
        return len(missing_files) == 0
