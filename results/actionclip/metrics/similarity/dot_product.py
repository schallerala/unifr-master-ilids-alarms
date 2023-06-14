from enum import Enum

import torch


class SimilarityMethod(str, Enum):
    dot_product = "dot_product"
    minus_human_features = "minus_human_features"
    minus_human_similarity = "minus_human_similarity"

    # def __repr__(self) -> str:
    #     return self.value


def _normalize(features):
    return features / features.norm(dim=-1, keepdim=True)


def dot_product(
    positive_text_features, negative_text_features, normalized_visual_features
):
    text_features = torch.vstack([positive_text_features, negative_text_features])

    similarities = _normalize(text_features) @ normalized_visual_features.T

    return similarities


def dot_product_minus_human_features(
    positive_text_features,
    negative_text_features,
    human_text_features,
    normalized_visual_features,
):
    human_text_features = human_text_features.squeeze(dim=0)

    negative_text_features -= human_text_features

    text_features = torch.vstack([positive_text_features, negative_text_features])

    # text x visual
    similarities = _normalize(text_features) @ normalized_visual_features.T

    return similarities


def dot_product_minus_human_similarity(
    positive_text_features,
    negative_text_features,
    human_text_features,
    normalized_visual_features,
    minus_similarity_weight,
):
    if minus_similarity_weight is None:
        raise ValueError("minus_similarity_weight must be defined")

    # text x visual
    pos_similarities = _normalize(positive_text_features) @ normalized_visual_features.T
    neg_similarities = _normalize(negative_text_features) @ normalized_visual_features.T
    human_similarities = _normalize(human_text_features) @ normalized_visual_features.T

    return torch.vstack(
        (
            pos_similarities,
            neg_similarities - (minus_similarity_weight * human_similarities),
        )
    )


def similarity(
    method: SimilarityMethod,
    positive_text_features,
    negative_text_features,
    human_text_features,
    normalized_visual_features,
    minus_similarity_weight=None,
):
    if method == SimilarityMethod.dot_product:
        return dot_product(
            positive_text_features=positive_text_features,
            negative_text_features=negative_text_features,
            normalized_visual_features=normalized_visual_features,
        )
    elif method == SimilarityMethod.minus_human_features:
        return dot_product_minus_human_features(
            positive_text_features=positive_text_features,
            negative_text_features=negative_text_features,
            human_text_features=human_text_features,
            normalized_visual_features=normalized_visual_features,
        )
    elif method == SimilarityMethod.minus_human_similarity:
        return dot_product_minus_human_similarity(
            positive_text_features=positive_text_features,
            negative_text_features=negative_text_features,
            human_text_features=human_text_features,
            normalized_visual_features=normalized_visual_features,
            minus_similarity_weight=minus_similarity_weight,
        )
    else:
        raise ValueError(f"Unknown similarity method: {method}")
