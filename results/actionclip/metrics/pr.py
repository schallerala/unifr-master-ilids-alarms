import numpy as np
from sklearn.metrics import auc, precision_recall_curve


def pr_auc(y_true: np.ndarray, y_score: np.ndarray):
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    pr_auc = auc(recall, precision)

    return pr_auc