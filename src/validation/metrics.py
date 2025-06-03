import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, roc_curve
import logging

def ecospat_boyce(fit, obs, nclass=0, window_w="default", res=100, plot=False, plot_save=None):
    """Calculate Boyce Index as per Hirzel et al. 2006"""
    
    if nclass == 0:
        if window_w == "default":
            window_w = (np.max(fit) - np.min(fit)) / 10
        interval = np.arange(np.min(fit), np.max(fit), window_w)
    else:
        interval = np.quantile(fit, np.linspace(0, 1, nclass+1))
    
    interval = interval[:-1]
    
    def boycei(interval, obs, fit):
        pi = np.sum((obs >= interval[0]) & (obs < interval[1])) / len(obs)
        ei = np.sum((fit >= interval[0]) & (fit < interval[1])) / len(fit)
        return pi / ei if ei > 0 else np.nan
    
    f = []
    for i in range(len(interval)-1):
        f.append(boycei([interval[i], interval[i+1]], obs, fit))
    
    f = np.array(f, dtype=np.float32)
    to_keep = np.where(~np.isnan(f))[0]
    f = f[to_keep]
    
    if len(f) > 1:
        boyce_index = np.corrcoef(np.arange(len(f)), f)[0, 1]
    else:
        boyce_index = np.nan
    
    if plot and plot_save:
        plt.figure(figsize=(8, 6))
        plt.plot(np.arange(len(f)), f, 'bo-')
        plt.xlabel('Habitat suitability class')
        plt.ylabel('Predicted/Expected ratio')
        plt.title(f'Boyce Index: {boyce_index:.3f}')
        plt.grid(True)
        plt.savefig(plot_save, dpi=300, bbox_inches='tight')
        plt.close()
    
    return boyce_index

class ModelValidator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def calculate_metrics(self, y_true, y_pred_prob, class_of_interest, output_dir):
        """Calculate validation metrics"""
        metrics = {}
        
        if 'roc_auc' in self.config['validation']['metrics']:
            auc = roc_auc_score(y_true, y_pred_prob)
            metrics['roc_auc'] = round(auc, 3)
            
            fpr, tpr, _ = roc_curve(y_true, y_pred_prob)
            plt.figure(figsize=(8, 6))
            plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.3f})')
            plt.plot([0, 1], [0, 1], 'k--')
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title(f'ROC Curve - Class {class_of_interest}')
            plt.legend()
            plt.grid(True)
            plt.savefig(f"{output_dir}/roc_curve_{class_of_interest}.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        if 'boyce_index' in self.config['validation']['metrics']:
            obs_positive = y_pred_prob[y_true == 1]
            if len(obs_positive) > 0:
                boyce = ecospat_boyce(
                    y_pred_prob, obs_positive,
                    nclass=self.config['validation']['boyce_nclass'],
                    res=self.config['validation']['boyce_res'],
                    plot=True,
                    plot_save=f"{output_dir}/boyce_index_{class_of_interest}.png"
                )
                metrics['boyce_index'] = round(boyce, 3)
            else:
                metrics['boyce_index'] = np.nan
        
        self.logger.info(f"Validation metrics for class {class_of_interest}: {metrics}")
        return metrics
