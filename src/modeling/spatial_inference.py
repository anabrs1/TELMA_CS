import numpy as np
import pyarrow.parquet as pq
from tqdm import tqdm
import joblib
import logging
from ..geospatial_utils.spatial_functions import export_sparse_to_tiff_dataset

class SpatialInference:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.batch_size = 10000
        
    def generate_probability_maps(self, model_path, data_path, template_raster, output_dir, class_of_interest):
        """Generate spatial probability maps"""
        model = joblib.load(model_path)
        
        parquet_file = pq.ParquetFile(data_path)
        
        total_rows = parquet_file.metadata.num_rows
        xcoords = np.empty([total_rows], np.int32)
        ycoords = np.empty([total_rows], np.int32)
        predictions = np.empty([total_rows], np.float32)
        
        index = 0
        for batch in tqdm(parquet_file.iter_batches(batch_size=self.batch_size), 
                        desc="Generating predictions"):
            chunk_df = batch.to_pandas()
            
            excluded_covariates = ['xcoord', 'ycoord', 'land_use_06', 'land_use_12', 
                                 'land_use_18', 'transition_06_12', 'transition_12_18']
            feature_cols = [col for col in chunk_df.columns if col not in excluded_covariates]
            X_batch = chunk_df[feature_cols].values
            
            batch_predictions = model.predict_proba(X_batch)[:, 1]
            batch_x_coord = chunk_df['xcoord'].values.astype(np.int32)
            batch_y_coord = chunk_df['ycoord'].values.astype(np.int32)
            
            index_increment = len(chunk_df)
            xcoords[index:index+index_increment] = batch_x_coord
            ycoords[index:index+index_increment] = batch_y_coord
            predictions[index:index+index_increment] = batch_predictions
            
            index += index_increment
        
        output_path = f"{output_dir}/probability_map_{class_of_interest}.tiff"
        export_sparse_to_tiff_dataset(template_raster, output_path, xcoords, ycoords, predictions)
        
        self.logger.info(f"Probability map saved to {output_path}")
        return output_path
