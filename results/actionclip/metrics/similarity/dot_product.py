import torch


def dot_product(normalized_text_features, normalized_visual_features):
    similarities = normalized_text_features @ normalized_visual_features.T

    return similarities


def dot_product_minus_human_features(normalized_positive_text_features, negative_text_features, human_text_features, normalized_visual_features):
    human_text_features = human_text_features.squeeze(dim=0)

    negative_text_features -= human_text_features

    normalized_negative_text_features = (
        negative_text_features / negative_text_features.norm(dim=-1, keepdim=True)
    )

    normalized_text_features = torch.vstack(
        [normalized_positive_text_features, normalized_negative_text_features]
    )

    # text x visual
    similarities = normalized_text_features @ normalized_visual_features.T

    return similarities


def dot_product_minus_human_similarity(normalized_positive_text_features, normalized_negative_text_features, normalized_human_text_features, normalized_visual_features, minus_similarity_weight):
    # text x visual
    pos_similarities = (
        normalized_positive_text_features @ normalized_visual_features.T
    )
    neg_similarities = (
        normalized_negative_text_features @ normalized_visual_features.T
    )
    human_similarities = (
        normalized_human_text_features @ normalized_visual_features.T
    )

    return torch.hstack(
        (
            pos_similarities,
            neg_similarities
            - (minus_similarity_weight * human_similarities),
        )
    )