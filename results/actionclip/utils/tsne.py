import math


def get_tsne_perplexity(sample_count: int):
    """
    As the perplexity is a hyperparameter for the t-SNE algorithm, this function
    returns a value for the perplexity based on the number of samples, as it has to
    be smaller than the number of samples.

    Its default value is 30 as per sklearn documentation.
    """
    return min(30.0, math.floor(sample_count - 1))