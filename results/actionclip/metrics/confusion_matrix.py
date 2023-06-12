import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve


def confusion_matrix_fn_equals_0(
    y_true: np.ndarray, y_score: np.ndarray
):
    # get the threshold where FN = 0
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    fn_equals_0_threshold = thresholds[
        np.argmax(tpr)
    ]  # argmax will return the first occurrence of the max value (1, as TP/(TP + FN = 0) = TP/TP = 1)

    # get the confusion matrix
    y_pred = y_score >= fn_equals_0_threshold
    TN, FP, FN, TP = confusion_matrix(y_true, y_pred).ravel()

    return dict(TN=TN, FP=FP, FN=FN, TP=TP)
