import numpy as np


def mean_ratio_score(similarity_scores: np.ndarray, positive_length: int) -> np.ndarray:
    # create the score (positive are above the negative)
    #   - foreach column, cut after the number of positive texts
    #       - mean the values (get a value for the positive and the negative texts)
    #       - divide both values
    positive_texts_similarity_score_mean = similarity_scores[:positive_length].mean(axis=0)
    negative_texts_similarity_score_mean = similarity_scores[positive_length:].mean(axis=0)

    ratio_score = (
        positive_texts_similarity_score_mean / negative_texts_similarity_score_mean
    )

    return ratio_score


def positive_score(similarity_scores: np.ndarray):
    # mean of each video which are the columns
    # 1 x N
    return similarity_scores.mean(axis=0)