import numpy as np
import pandas as pd
import csv

def create_landtransition_lookup_table(land_transitions_codes_filename: str):
    """Create lookup table for land use transition codes"""
    lut_from_to_lookup_table = np.zeros((1515, 2), dtype="uint16")
    with open(land_transitions_codes_filename, "r") as csvfile:
        lut_codes_reader = csv.reader(csvfile, delimiter=";")
        next(lut_codes_reader)
        for row in lut_codes_reader:
            if len(row) >= 3:
                lut_code = int(row[-3])
                if lut_code == 0:
                    continue
                lu_to = int(row[-1])
                lu_from = int(row[-2])
                lut_from_to_lookup_table[lut_code, 0] = lu_from
                lut_from_to_lookup_table[lut_code, 1] = lu_to
    return lut_from_to_lookup_table

def get_indices_of_interest(clum_data, class_of_interest, year='all'):
    """Get indices for specific land use transition class"""
    if hasattr(clum_data, 'to_pandas'):
        df = clum_data.to_pandas()
    else:
        df = clum_data
        
    if year == 'all':
        indices = df.index[df.get('lut', df.get('transition_class', [])) == class_of_interest]
    else:
        indices = df.index[(df.get('lut', df.get('transition_class', [])) == class_of_interest) & 
                          (df.get('year', []) == year)]
    return indices.tolist()

def getX(clum_data, indices, excluded_covariates):
    """Extract feature matrix X from data"""
    if hasattr(clum_data, 'to_pandas'):
        df = clum_data.to_pandas()
    else:
        df = clum_data
        
    feature_cols = [col for col in df.columns if col not in excluded_covariates]
    return df.iloc[indices][feature_cols].values

def getY(clum_data, indices, year='all'):
    """Extract target variable Y from data"""
    if hasattr(clum_data, 'to_pandas'):
        df = clum_data.to_pandas()
    else:
        df = clum_data
        
    y = np.zeros(len(indices))
    return y.reshape(-1, 1)
