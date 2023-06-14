from enum import Enum

import numpy as np


class ScoreMethod(str, Enum):
    mean = "mean"
    positive = "positive"

    # def __repr__(self) -> str:
    #     return self.value


def mean_ratio_score(similarity_scores: np.ndarray, positive_length: int) -> np.ndarray:
    # create the score (positive are above the negative)
    #   - foreach column, cut after the number of positive texts
    #       - mean the values (get a value for the positive and the negative texts)
    #       - divide both values
    positive_texts_similarity_score_mean = similarity_scores[:positive_length].mean(
        axis=0
    )
    negative_texts_similarity_score_mean = similarity_scores[positive_length:].mean(
        axis=0
    )

    ratio_score = (
        positive_texts_similarity_score_mean / negative_texts_similarity_score_mean
    )

    return ratio_score


def positive_score(similarity_scores: np.ndarray):
    # mean of each video which are the columns
    # 1 x N
    return similarity_scores.mean(axis=0)


def score(
    score_method: ScoreMethod, similarity_scores: np.ndarray, positive_length: int
) -> np.ndarray:
    if score_method == ScoreMethod.mean:
        return mean_ratio_score(similarity_scores, positive_length)
    elif score_method == ScoreMethod.positive:
        return positive_score(similarity_scores)
    else:
        raise ValueError(f"Unknown score method: {score_method}")
