import random
import warnings
from pathlib import Path

import numpy as np
import open_clip
import optuna
import pandas as pd
import torch
import typer
from hparam.texts import NEGATIVE_TEXTS, POSITIVE_TEXTS, get_all_composition
from metrics.confusion_matrix import confusion_matrix_fn_equals_0
from metrics.pr import pr_auc
from metrics.roc import roc_auc
from metrics.score.ratio import ScoreMethod, score
from metrics.score.topk import TopClassificationMethod, classify
from metrics.similarity.dot_product import SimilarityMethod, similarity

from ilids.models.actionclip.constants import (
    get_base_model_name_from_ckpt_path,
    get_input_frames_from_ckpt_path,
)
from ilids.models.actionclip.factory import create_models_and_transforms

SEED = 16896375
SOURCE_PATH = Path().resolve()

warnings.filterwarnings("ignore", category=UserWarning, module="optuna.distributions")


def objective_builder(model_text, y_true, visual_features):
    y_true = y_true.to_numpy()

    ALL_POSITIVE_TEXTS_COMBINATIONS = get_all_composition(POSITIVE_TEXTS, 12, 8)
    ALL_NEGATIVE_TEXTS_COMBINATIONS = get_all_composition(NEGATIVE_TEXTS, 12, 8)

    normalized_visual_features = normalize(visual_features)

    human_text_features = encode_text(model_text, ["human"])

    # Define the objective function to optimize
    def objective(trial: optuna.Trial):
        # suggest
        ## texts
        ### positive
        positive_texts = trial.suggest_categorical(
            "positive_texts", ALL_POSITIVE_TEXTS_COMBINATIONS
        )
        ### negative
        negative_texts = trial.suggest_categorical(
            "negative_texts", ALL_NEGATIVE_TEXTS_COMBINATIONS
        )
        ### reference text classes
        texts_classes = [True] * len(positive_texts) + [False] * len(negative_texts)

        ## get similarity method
        similarity_method = trial.suggest_categorical(
            "similarity_method",
            [
                SimilarityMethod.dot_product,
                SimilarityMethod.minus_human_features,
                SimilarityMethod.minus_human_similarity,
            ],
        )
        minus_similarity_weight = (
            trial.suggest_float("minus_similarity_weight", 0.1, 0.9)
            if similarity_method == SimilarityMethod.minus_human_similarity
            else None
        )

        ## get score method
        score_method = trial.suggest_categorical(
            "score_method",
            [
                ScoreMethod.mean,
                ScoreMethod.positive,
                TopClassificationMethod.mode,
                TopClassificationMethod.any,
                TopClassificationMethod.max_sum,
            ],
        )

        # encode texts
        positive_text_features = encode_text(model_text, positive_texts)
        negative_text_features = encode_text(model_text, negative_texts)

        # similarity
        similarities = similarity(
            similarity_method,
            positive_text_features,
            negative_text_features,
            human_text_features,
            normalized_visual_features,
            minus_similarity_weight,
        )

        # in case of a Top K score method, try multiple Top K values
        if isinstance(score_method, TopClassificationMethod):
            # get the top k values and return best roc-auc
            best_roc = 0
            best_topK = 0

            for topK in [1, 3, 5]:
                if topK > len(positive_texts):
                    break

                y = classify(score_method, similarities, texts_classes, topK).numpy()

                # roc, pr
                roc = roc_auc(y_true, y)
                pr = pr_auc(y_true, y)

                # confusion matrix
                TP, FN, FP, TN = confusion_matrix_fn_equals_0(y_true, y)

                # print
                print(
                    dict(
                        roc_auc=roc,
                        pr_auc=pr,
                        TP=TP,
                        FN=FN,
                        FP=FP,
                        TN=TN,
                        topK=topK,
                        **trial.params,
                    )
                )

                if roc > best_roc:
                    best_roc = roc
                    best_topK = topK

            # return best roc-auc
            trial.set_user_attr("best_topK", best_topK)

            return best_roc

        # otherwise, for a ratio score, just compute the score
        else:
            y = score(score_method, similarities.numpy(), len(positive_texts))

            # roc, pr
            roc = roc_auc(y_true, y)
            pr = pr_auc(y_true, y)

            # confusion matrix
            TP, FN, FP, TN = confusion_matrix_fn_equals_0(y_true, y)

            # print
            print(
                dict(roc_auc=roc, pr_auc=pr, TP=TP, FN=FN, FP=FP, TN=TN, **trial.params)
            )

            # return roc-auc
            return roc

    return objective


def normalize(features):
    return features / features.norm(dim=-1, keepdim=True)


def load_y_true() -> pd.Series:
    tp_fp_sequences_path = (
        SOURCE_PATH.parent.parent
        / "data"
        / "handcrafted-metadata"
        / "tp_fp_sequences.csv"
    )
    # the first column being the sequence file name: e.g. "SZTEA101a_00_05_37.mov"
    SEQUENCES_DF = pd.read_csv(tp_fp_sequences_path, index_col=0)

    return SEQUENCES_DF["Classification"] == "TP"


def load_visual_features(model_name, y_true):
    pickle_file = SOURCE_PATH / f"{model_name}.pkl"
    features_df = pd.read_pickle(pickle_file)
    features_df.set_index(features_df.index.str.lstrip("data/sequences/"), inplace=True)

    FEATURES_COLUMNS_INDEXES = pd.RangeIndex.from_range(range(512))

    visual_features_df = (
        # make sure to have matching indexes order
        features_df.join(y_true)
        # Drop NaN, in case a sequence wasn't fed to the model as it didn't have enough frames
        .dropna(subset=FEATURES_COLUMNS_INDEXES)
    )

    visual_features = torch.from_numpy(
        # only select the features columns
        visual_features_df[FEATURES_COLUMNS_INDEXES]
        .to_numpy(dtype=np.float32)
    )

    return visual_features, visual_features_df['Classification']


def load_model_text_encoder(model_name):
    ACTIONCLIP_CKPT_PATH = (
        SOURCE_PATH.parent.parent / "ckpt" / "actionclip" / f"{model_name}.pt"
    )

    model_text = create_models_and_transforms(
        actionclip_pretrained_ckpt=ACTIONCLIP_CKPT_PATH,
        openai_model_name=get_base_model_name_from_ckpt_path(ACTIONCLIP_CKPT_PATH),
        extracted_frames=get_input_frames_from_ckpt_path(ACTIONCLIP_CKPT_PATH),
        device=torch.device("cpu"),
    )[1]

    model_text.eval()

    return model_text


def encode_text(model_text, texts):
    tokenized_texts = open_clip.tokenize(texts)
    with torch.no_grad():
        return model_text(tokenized_texts)


def run(model_name: str):
    random.seed(SEED)

    # load true data
    y_true: pd.Series = load_y_true()

    # load image features
    #   and override the y_true as some sequences might have been dropped
    visual_features, y_true = load_visual_features(model_name, y_true)

    # load model
    model_text = load_model_text_encoder(model_name)

    # Create a study object and optimize the objective function.
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=SEED),  # student number as seed
    )
    study.optimize(objective_builder(model_text, y_true, visual_features), n_trials=200)

    # Print the best value and parameters
    print("Best value:")
    print(study.best_value)
    print("Best params:")
    print(study.best_params)
    print("Best trial user attributes:")
    print(study.best_trial.user_attrs)

    if optuna.visualization.is_available():
        path = Path(model_name) / "images"
        optuna.visualization.plot_contour(study).write_image(str(path / "optuna_contour.png"))
        optuna.visualization.plot_edf(study).write_image(str(path / "optuna_edf.png"))
        optuna.visualization.plot_optimization_history(study).write_image(str(path / "optuna_optimization_history.png"))
        # TODO Doesn't handle lists, therefore comment out. Should change suggestion
        # optuna.visualization.plot_parallel_coordinate(study).write_image(str(path / "optuna_parallel_coordinate.png"))
        optuna.visualization.plot_param_importances(study).write_image(str(path / "optuna_param_importances.png"))
        optuna.visualization.plot_rank(study).write_image(str(path / "optuna_rank.png"))
        optuna.visualization.plot_slice(study).write_image(str(path / "optuna_slice.png"))



if __name__ == "__main__":
    typer.run(run)
