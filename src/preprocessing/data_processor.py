import numpy as np
import rasterio as rio
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm
import logging
from ..geospatial_utils.spatial_functions import get_spatial_reference_of_epsg_from_code
from ..land_use_mapping import CORINE_TO_CLASS, is_cropland_transition, CROPLAND_CORINE_CODES

class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.xres = config['preprocessing']['resolution']
        self.yres = -config['preprocessing']['resolution']
        self.crs = get_spatial_reference_of_epsg_from_code(config['preprocessing']['crs_epsg'])
        
    def create_observation_mask(self, datasets):
        """Create mask for valid observations"""
        mask = None
        
        if 'land_mask' in datasets:
            with datasets['land_mask'] as f:
                mask = f.read(1) == 1
        
        for name, dataset in datasets.items():
            if 'land_use' in name or 'transition' in name:
                with dataset as f:
                    data = f.read(1)
                    if mask is None:
                        mask = data != f.nodata
                    else:
                        mask = np.logical_and(mask, data != f.nodata)
                        
        return mask
        
    def extract_sparse_data(self, datasets, mask):
        """Extract sparse representation of valid pixels"""
        table_data = {}
        
        template_dataset = list(datasets.values())[0]
        with template_dataset as src:
            bounds = src.bounds
            height, width = src.height, src.width
            
        xcoord_row = np.arange(bounds.left + self.xres/2, bounds.right + self.xres/2, self.xres, np.int32)
        ycoord_row = np.arange(bounds.top + self.yres/2, bounds.bottom + self.yres/2, self.yres, np.int32)
        xcoord_block = np.tile(xcoord_row, (height, 1))
        ycoord_block = np.tile(ycoord_row, (width, 1)).transpose()
        
        table_data['xcoord'] = xcoord_block[mask]
        table_data['ycoord'] = ycoord_block[mask]
        
        for name, dataset in tqdm(datasets.items(), desc="Processing datasets"):
            with dataset as src:
                data = src.read(1)
                table_data[name] = data[mask]
                
        return table_data
        
    def filter_cropland_transitions(self, table_data):
        """Filter data to focus on cropland transitions"""
        if not self.config['land_use']['focus_on_cropland_transitions']:
            return table_data
            
        if 'transition_12_18' in table_data:
            transition_codes = table_data['transition_12_18']
            cropland_mask = np.zeros(len(transition_codes), dtype=bool)
            
            for i, code in enumerate(transition_codes):
                if is_cropland_transition(code) or code in CROPLAND_CORINE_CODES:
                    cropland_mask[i] = True
            
            filtered_data = {}
            for key, values in table_data.items():
                filtered_data[key] = values[cropland_mask]
            return filtered_data
            
        return table_data
        
    def save_to_parquet(self, table_data, output_path):
        """Save processed data to parquet format"""
        table = pa.Table.from_pydict(table_data)
        pq.write_table(table, output_path, use_dictionary=True, compression='snappy')
        self.logger.info(f"Saved processed data to {output_path}")
