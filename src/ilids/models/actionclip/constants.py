from pathlib import Path

OPENAI_BASE_MODEL_NAMES = {
    "vit-b-16-16f": "ViT-B-16",
    "vit-b-16-32f": "ViT-B-16",
    "vit-b-16-8f": "ViT-B-16",
    "vit-b-32-8f": "ViT-B-32",
}
"""
The base model names for the OpenAI models that have a checkpoint for actionclip.

The key is the stem name of the checkpoint file, and the value is the base model name
to be used in the `open_clip.load_openai_model` or
`ilids.models.actionclip.factory.create_models_and_transforms` function.
"""


def get_base_model_name_from_ckpt_path(ckpt_path: Path) -> str:
    """
    Get the base model name from the checkpoint path.

    Args:
        ckpt_path: The checkpoint path.

    Raises:
        ValueError: If the checkpoint path is unknown.

    Returns:
        The base model name.
    """

    # in case the ckpt_path is unknown, throw an error
    if ckpt_path.stem not in OPENAI_BASE_MODEL_NAMES:
        raise ValueError(f"Unknown checkpoint path: {ckpt_path}")

    model_name = OPENAI_BASE_MODEL_NAMES[ckpt_path.stem]

    return model_name


def get_input_frames_from_ckpt_path(ckpt_path: Path) -> int:
    """
    Get the expected number of frames as input for the model using its checkpoint path.
    As the number of frames is encoded in the checkpoint path, it is the last part of the
    stem name before the character 'f'.

    Args:
        ckpt_path: The checkpoint path.

    Raises:
        ValueError: If the checkpoint path is unknown.

    Returns:
        The number of frames as input for the model.
    """

    # in case the ckpt_path is unknown, throw an error
    if ckpt_path.stem not in OPENAI_BASE_MODEL_NAMES:
        raise ValueError(f"Unknown checkpoint path: {ckpt_path}")

    input_frames = int(ckpt_path.stem.split("-")[-1].replace("f", ""))

    return input_frames
