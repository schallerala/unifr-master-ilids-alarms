from pathlib import Path

import numpy as np
import open_clip
import optuna
import pandas as pd
import typer
import torch

from ilids.models.actionclip.constants import get_base_model_name_from_ckpt_path, get_input_frames_from_ckpt_path

from ilids.models.actionclip.factory import create_models_and_transforms
from hparam.texts import NEGATIVE_TEXTS, POSITIVE_TEXTS, get_all_composition


SEED = 16896375
SOURCE_PATH = Path().resolve()

# encode_texts(["human"])





def objective_builder(model_text, y_true, visual_features):
    ALL_POSITIVE_TEXTS_COMBINATIONS = get_all_composition(POSITIVE_TEXTS)
    ALL_NEGATIVE_TEXTS_COMBINATIONS = get_all_composition(NEGATIVE_TEXTS)

    # Define the objective function to optimize
    def objective(trial):
        # suggest
        positive_texts = trial.suggest_int("positive_texts", ALL_POSITIVE_TEXTS_COMBINATIONS)
        positive_texts = trial.suggest_int("negative_texts", ALL_NEGATIVE_TEXTS_COMBINATIONS)
        # minus_similarity_weight = trial.suggest_float("minus_similarity_weight", 0.1, 0.9)

        # similarity

        # score

        # print

        # return roc-auc
        return len(positive_texts)

    return objective


def normalize(features):
    return features / features.norm(dim=-1, keepdim=True)


def load_y_true() -> pd.Series:
    tp_fp_sequences_path = (
        SOURCE_PATH.parent.parent / "data" / "handcrafted-metadata" / "tp_fp_sequences.csv"
    )
    # the first column being the sequence file name: e.g. "SZTEA101a_00_05_37.mov"
    SEQUENCES_DF = pd.read_csv(tp_fp_sequences_path, index_col=0)

    return SEQUENCES_DF["Classification"] == "TP"


def load_visual_features(model_name, y_true):
    pickle_file = SOURCE_PATH / f"{model_name}.pkl"
    features_df = pd.read_pickle(pickle_file)
    features_df.set_index(features_df.index.str.lstrip("data/sequences/"), inplace=True)

    FEATURES_COLUMNS_INDEXES = pd.RangeIndex.from_range(range(512))

    visual_features = torch.from_numpy(
        # make sure to have matching indexes order
        features_df.join(y_true)
        # Drop NaN, in case a sequence wasn't fed to the model as it didn't have enough frames
        .dropna(subset=FEATURES_COLUMNS_INDEXES)
        # only select the features columns
        [FEATURES_COLUMNS_INDEXES]
        .to_numpy(dtype=np.float64)
    )

    return visual_features


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
    # load true data
    y_true: pd.Series = load_y_true()

    # load image features
    visual_features = load_visual_features(model_name, y_true)

    # load model
    model_text = load_model_text_encoder(model_name)

    # Create a study object and optimize the objective function.
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=SEED),  # student number as seed
    )
    study.optimize(objective_builder(model_text, y_true, visual_features), n_trials=200)

    # Print the best value and parameters
    print(study.best_params)


if __name__ == "__main__":
    typer.run(run)