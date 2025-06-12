#!/usr/bin/env python3
import argparse
import yaml
import logging
import os
from pathlib import Path
import sys
import numpy as np
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_ingestion.data_loader import DataLoader
from preprocessing.data_processor import DataProcessor
from modeling.random_forest_model import RandomForestLandUseModel
from validation.metrics import ModelValidator
from modeling.spatial_inference import SpatialInference

def setup_logging(config):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, config['logging']['level']),
        format=config['logging']['format'],
        handlers=[
            logging.FileHandler('logs/pipeline.log'),
            logging.StreamHandler()
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='Land Use Change Modeling Pipeline')
    parser.add_argument('--config', default='config/default_config.yaml',
                      help='Path to configuration file')
    parser.add_argument('--input-dir', help='Input data directory')
    parser.add_argument('--output-dir', help='Output directory')
    parser.add_argument('--focus-cropland', action='store_true',
                      help='Focus on cropland transitions only')
    
    args = parser.parse_args()
    
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    if args.input_dir:
        config['data']['input_dir'] = args.input_dir
    if args.output_dir:
        config['data']['output_dir'] = args.output_dir
    if args.focus_cropland:
        config['land_use']['focus_on_cropland_transitions'] = True
    
    os.makedirs('logs', exist_ok=True)
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Land Use Change Modeling Pipeline")
    
    try:
        logger.info("Step 1: Data Ingestion")
        data_loader = DataLoader(config)
        datasets = data_loader.load_all_spatial_files(config['data']['input_dir'])
        
        if not data_loader.validate_data_structure(datasets):
            logger.warning("Some recommended data files are missing")
        
        logger.info("Step 2: Data Preprocessing")
        processor = DataProcessor(config)
        
        mask = processor.create_observation_mask(datasets)
        logger.info(f"Valid observations: {np.count_nonzero(mask):,}")
        
        table_data = processor.extract_sparse_data(datasets, mask)
        
        if config['land_use']['focus_on_cropland_transitions']:
            table_data = processor.filter_cropland_transitions(table_data)
            logger.info(f"Filtered to {len(table_data['xcoord']):,} cropland transition observations")
        
        os.makedirs(config['data']['output_dir'], exist_ok=True)
        processed_data_path = f"{config['data']['output_dir']}/processed_data.parquet"
        processor.save_to_parquet(table_data, processed_data_path)
        
        logger.info("Step 3: Model Training")
        model = RandomForestLandUseModel(config)
        validator = ModelValidator(config)
        
        if config['land_use']['focus_on_cropland_transitions']:
            transitions_to_model = [3]
            logger.info("Focusing on cropland transitions (class 3)")
        else:
            transitions_to_model = config['land_use']['all_classes']
            logger.info(f"Modeling all {len(transitions_to_model)} land use classes")
        
        all_metrics = {}
        
        for class_of_interest in transitions_to_model:
            logger.info(f"Training model for transition class {class_of_interest}")
            
            X, y, feature_cols = model.prepare_data(table_data, class_of_interest)
            
            if np.sum(y) < 10:
                logger.warning(f"Skipping class {class_of_interest}: insufficient positive examples")
                continue
            
            X_test, y_test, y_pred_prob = model.train_model(X, y, class_of_interest)
            
            metrics = validator.calculate_metrics(y_test, y_pred_prob, class_of_interest, 
                                                config['data']['output_dir'])
            all_metrics[class_of_interest] = metrics
            
            model.save_model(config['data']['output_dir'], class_of_interest)
            
            logger.info(f"Step 4: Generating spatial outputs for class {class_of_interest}")
            spatial_inference = SpatialInference(config)
            
            template_raster = list(datasets.values())[0].name
            model_path = f"{config['data']['output_dir']}/rf_model_{class_of_interest}.pkl"
            
            probability_map = spatial_inference.generate_probability_maps(
                model_path, processed_data_path, template_raster,
                config['data']['output_dir'], class_of_interest
            )
        
        with open(f"{config['data']['output_dir']}/validation_metrics.json", 'w') as f:
            json.dump(all_metrics, f, indent=2)
        
        logger.info("Pipeline completed successfully!")
        logger.info(f"Results saved to: {config['data']['output_dir']}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    
    finally:
        for dataset in datasets.values():
            dataset.close()

if __name__ == "__main__":
    main()
