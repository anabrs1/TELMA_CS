import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import roc_auc_score, recall_score
import joblib
import logging
import time
from ..land_use_mapping import CORINE_TO_CLASS, CLASS_DESCRIPTIONS, is_cropland_transition

class RandomForestLandUseModel:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.hyperparameters = {}
        
    def prepare_data(self, table_data, class_of_interest):
        """Prepare X and Y for training"""
        excluded_covariates = ['xcoord', 'ycoord', 'land_use_06', 'land_use_12', 
                             'land_use_18', 'transition_06_12', 'transition_12_18']
        
        feature_cols = [col for col in table_data.keys() if col not in excluded_covariates]
        X = np.column_stack([table_data[col] for col in feature_cols])
        
        y = np.zeros(len(table_data['xcoord']))
        if 'transition_12_18' in table_data:
            transition_codes = table_data['transition_12_18']
            for i, code in enumerate(transition_codes):
                target_class = CORINE_TO_CLASS.get(code, code)
                if target_class == class_of_interest:
                    y[i] = 1
        
        return X, y, feature_cols
        
    def tune_hyperparameters(self, X_train, y_train):
        """Tune Random Forest hyperparameters"""
        if not self.config['modeling']['hyperparameter_tuning']:
            return {'n_estimators': 100, 'max_depth': 20}
            
        self.logger.info("Starting hyperparameter tuning...")
        start_time = time.time()
        
        if len(X_train) < 1000:
            param_grid = {
                'n_estimators': [50, 100],
                'max_depth': [10, 20],
                'min_samples_split': [2, 5],
                'min_samples_leaf': [1, 2]
            }
        else:
            param_grid = {
                'n_estimators': self.config['modeling']['n_estimators_range'],
                'max_depth': self.config['modeling']['max_depth_range'],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        
        rf = RandomForestClassifier(random_state=self.config['modeling']['random_state'])
        grid_search = GridSearchCV(rf, param_grid, cv=5, scoring='roc_auc', n_jobs=-1)
        grid_search.fit(X_train, y_train)
        
        elapsed_time = round((time.time() - start_time) / 60)
        self.logger.info(f"Finished tuning in {elapsed_time} minutes.")
        
        return grid_search.best_params_
        
    def train_model(self, X, y, class_of_interest):
        """Train Random Forest model"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.config['modeling']['test_size'],
            random_state=self.config['modeling']['random_state']
        )
        
        best_params = self.tune_hyperparameters(X_train, y_train)
        self.hyperparameters[class_of_interest] = best_params
        
        self.model = RandomForestClassifier(**best_params, 
                                          random_state=self.config['modeling']['random_state'])
        self.model.fit(X_train, y_train)
        
        y_pred_prob = self.model.predict_proba(X_test)[:, 1]
        auc_score = roc_auc_score(y_test, y_pred_prob)
        
        self.hyperparameters[class_of_interest]['auc_score'] = round(auc_score, 2)
        
        self.logger.info(f"Model trained for class {class_of_interest}, AUC: {auc_score:.3f}")
        
        return X_test, y_test, y_pred_prob
        
    def save_model(self, output_path, class_of_interest):
        """Save trained model"""
        model_path = f"{output_path}/rf_model_{class_of_interest}.pkl"
        joblib.dump(self.model, model_path)
        
        params_path = f"{output_path}/hyperparameters_{class_of_interest}.pkl"
        joblib.dump(self.hyperparameters, params_path)
        
        self.logger.info(f"Model saved to {model_path}")
