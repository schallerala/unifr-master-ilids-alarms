from enum import Enum

import torch


class TopClassificationMethod(str, Enum):
    mode = "mode"  # text classification with the most frequent class in top k
    max_sum = "max_sum"  # sum all similarity by text class and pick biggest
    any = "any"  # any text classification in top k is defined as alarm

    # def __repr__(self) -> str:
    #     return self.value


def mode(similarities, text_class, topK):
    # for each clip, get the top K most similar clips, and based on their text class,
    # get the mode (the value pressed the most)

    # make sure that the text classes is a tensor for further operations
    text_class = torch.tensor(text_class)

    # similarities: text x visual
    # for each column (clip), get the topk texts similarity
    _, indices = similarities.topk(k=topK, dim=0)

    # map the indices to the text class
    best_text_classes = text_class[indices]

    # for each column (the clips), get the mode
    return best_text_classes.mode(dim=0).values


def any(similarities, text_class, topK):
    # for each clip, get the top K most similar clips, and based on their text class,
    # is there any positive text class

    # make sure that the text classes is a tensor for further operations
    text_class = torch.tensor(text_class)

    # similarities: text x visual
    # for each column (clip), get the topk texts similarity
    indices = similarities.topk(k=topK, dim=0).indices

    # map the indices to the text class
    best_text_classes = text_class[indices]

    # for each column (the clips), get if there is any positive text class
    return best_text_classes.any(dim=0)


def max_sum(similarities, text_class, topK):
    # for each clip, get the top K most similar clips, and based on their text class,
    # sum the similarity values by the text class and get the max

    # make sure that the text classes is a tensor for further operations
    text_class = torch.tensor(text_class)

    # similarities: text x visual
    # for each column (clip), get the topk texts similarity
    values, indices = similarities.topk(k=topK, dim=0)

    # select the top K text classes
    topk_text_classes = text_class[indices]

    # for each clip, sum the positive similarity values and the negative similarity values
    positive_similarity_values_sum = (values * topk_text_classes).sum(dim=0)
    negative_similarity_values_sum = (values * ~topk_text_classes).sum(dim=0)

    y_class = (positive_similarity_values_sum >= negative_similarity_values_sum).bool()

    return y_class


def classify(method: TopClassificationMethod, similarities, text_class, topK):
    if method == TopClassificationMethod.mode:
        return mode(similarities, text_class, topK)
    elif method == TopClassificationMethod.max_sum:
        return max_sum(similarities, text_class, topK)
    elif method == TopClassificationMethod.any:
        return any(similarities, text_class, topK)
    else:
        raise ValueError(f"Unknown method: {method}")
