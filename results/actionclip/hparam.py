import random
import warnings
from pathlib import Path

from aim import Run, Text
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

# object that will replace Aim's logger as a noop, when "re-running" the objective function
# with the best parameters found
class DoNothing:
    def __getattr__(self, name):
        return self  # Return the DoNothing object itself
    def __call__(self, *args, **kwargs):
        return self  # Return the DoNothing object itself


def objective_builder(model_name, model_text, y_true, visual_features, ALL_POSITIVE_TEXTS_COMBINATIONS, ALL_NEGATIVE_TEXTS_COMBINATIONS, persist_y = False, log_run = False):
    y_true = y_true.to_numpy()

    normalized_visual_features = normalize(visual_features)

    human_text_features = encode_text(model_text, ["human"])

    run = Run(experiment=model_name) if log_run else DoNothing()

    # Define the objective function to optimize
    def objective(trial: optuna.Trial):
        # suggest
        ## texts
        ### positive
        positive_texts = trial.suggest_categorical(
            "positive_texts", ALL_POSITIVE_TEXTS_COMBINATIONS
        )
        run.track(Text(', '.join(positive_texts)), name="positive_texts", step=trial.number)

        ### negative
        negative_texts = trial.suggest_categorical(
            "negative_texts", ALL_NEGATIVE_TEXTS_COMBINATIONS
        )
        run.track(Text(', '.join(negative_texts)), name="negative_texts", step=trial.number)
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
        run.track(Text(similarity_method.value), name="similarity_method", step=trial.number)
        minus_similarity_weight = (
            trial.suggest_float("minus_similarity_weight", 0.1, 0.9)
            if similarity_method == SimilarityMethod.minus_human_similarity
            else None
        )
        if minus_similarity_weight:
            run.track(minus_similarity_weight, name="minus_similarity_weight", step=trial.number)

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
        run.track(Text(score_method.value), name="score_method", step=trial.number)

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
                        trail_number=trial.number,
                        **trial.params,
                    )
                )
                run.track(dict(
                        roc_auc=roc,
                        pr_auc=pr,
                        TP=TP,
                        FN=FN,
                        FP=FP,
                        TN=TN,
                        topK=topK,
                    ), step=trial.number)

                if roc > best_roc:
                    best_roc = roc
                    best_topK = topK

                    trial.set_user_attr("roc_auc", roc)
                    trial.set_user_attr("pr_auc", pr)
                    trial.set_user_attr("TP", TP)
                    trial.set_user_attr("FN", FN)
                    trial.set_user_attr("FP", FP)
                    trial.set_user_attr("TN", TN)
                    trial.set_user_attr("best_topK", best_topK)

                    if persist_y:
                        np.save('y.npy', y)
                        np.save('y_true.npy', y_true)

            # return best roc-auc
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
                dict(roc_auc=roc, pr_auc=pr, TP=TP, FN=FN, FP=FP, TN=TN, trail_number=trial.number, **trial.params)
            )
            run.track(
                dict(roc_auc=roc, pr_auc=pr, TP=TP, FN=FN, FP=FP, TN=TN),
                step=trial.number
            )
            trial.set_user_attr("roc_auc", roc)
            trial.set_user_attr("pr_auc", pr)
            trial.set_user_attr("TP", TP)
            trial.set_user_attr("FN", FN)
            trial.set_user_attr("FP", FP)
            trial.set_user_attr("TN", TN)

            if persist_y:
                np.save('y.npy', y)
                np.save('y_true.npy', y_true)

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


def run(model_name: str, plot_study: bool = typer.Argument(default=False), trials: int = typer.Argument(default=200)):
    if plot_study:
        if not optuna.visualization.is_available():
            raise RuntimeError("Visualization library is not available!")

    random.seed(SEED)

    # load true data
    y_true: pd.Series = load_y_true()

    # load image features
    #   and override the y_true as some sequences might have been dropped
    visual_features, y_true = load_visual_features(model_name, y_true)

    # load model
    model_text = load_model_text_encoder(model_name)

    # pick positive and negative prompts and create compositions
    ALL_POSITIVE_TEXTS_COMBINATIONS = get_all_composition(POSITIVE_TEXTS, 12, 8)
    ALL_NEGATIVE_TEXTS_COMBINATIONS = get_all_composition(NEGATIVE_TEXTS, 12, 8)

    # Create a study object and optimize the objective function.
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=SEED),  # student number as seed
    )
    study.optimize(objective_builder(model_name, model_text, y_true, visual_features, ALL_POSITIVE_TEXTS_COMBINATIONS, ALL_NEGATIVE_TEXTS_COMBINATIONS, log_run=True), n_trials=trials)

    # Print the best value and parameters
    print("Best value:")
    print(study.best_value)
    print("Best params:")
    print(study.best_params)
    print("Best trial user attributes:")
    print(study.best_trial.user_attrs)

    objective_builder(model_name, model_text, y_true, visual_features, ALL_POSITIVE_TEXTS_COMBINATIONS, ALL_NEGATIVE_TEXTS_COMBINATIONS, persist_y=True)(study.best_trial)

    if plot_study:  # should have checked previously if the visualization library is available
        path = Path(model_name) / "images"
        plt = optuna.visualization.plot_contour(study)
        plt.write_image(str(path / "optuna_contour.png"), width=3500, height=3500)
        plt = optuna.visualization.plot_edf(study)
        plt.write_image(str(path / "optuna_edf.png"))
        plt = optuna.visualization.plot_optimization_history(study)
        plt.write_image(str(path / "optuna_optimization_history.png"))
        # TODO Doesn't handle lists, therefore comment out. Should change suggestion
        # plt = optuna.visualization.plot_parallel_coordinate(study)
        # plt.write_image(str(path / "optuna_parallel_coordinate.png"), width=3500, height=2500)
        # plt = optuna.visualization.plot_param_importances(study)
        # plt.write_image(str(path / "optuna_param_importances.png"), width=3500, height=2500)
        plt = optuna.visualization.plot_rank(study)
        plt.write_image(str(path / "optuna_rank.png"), width=3500, height=2500)
        plt = optuna.visualization.plot_slice(study)
        plt.write_image(str(path / "optuna_slice.png"), width=3500, height=2500)


if __name__ == "__main__":
    typer.run(run)
