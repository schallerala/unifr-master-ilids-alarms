import numpy as np
from sklearn.metrics import auc, roc_curve


def roc_auc(y_true: np.ndarray, y_score: np.ndarray):
    fpr, tpr, _ = roc_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr)

    return roc_auc
