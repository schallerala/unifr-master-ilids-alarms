from enum import Enum
from pathlib import Path
from typing import Optional

import torch
import typer
from torch.utils.data import DataLoader

from ilids.experiments.actionclip import extract_actionclip_sequences_features
from ilids.experiments.movinet import extract_movinet_features
from ilids.models.actionclip.datasets import ActionDataset
from ilids.models.actionclip.factory import create_models_and_transforms
from ilids.models.actionclip.transform import get_augmentation
from ilids.synchronization.acquire_gpu_client import acquire_free_gpu
from ilids.synchronization.alternate_device import DeviceType, alternate_device
from ilids.towhee_utils.override.movinet import MovinetModelName
from ilids.utils.persistence_method import (
    CsvPandasPersistenceMethod,
    PicklePandasPersistenceMethod,
)

typer_app = typer.Typer()


class PersistenceMethodSource(str, Enum):
    pandas = "pandas"
    numpy = "numpy"
    torch = "torch"


class PersistenceMethod(str, Enum):
    csv = "csv"
    pickle = "pickle"
    torch = "torch"

    @classmethod
    def get_from_extension(cls, output: Path) -> "PersistenceMethod":
        suffix = output.suffix
        if suffix == ".csv":
            return PersistenceMethod.csv
        if suffix == ".pkl":
            return PersistenceMethod.pickle
        if suffix == ".pt":
            return PersistenceMethod.torch

        raise NotImplementedError(f"No implemented method for extension {suffix}")

    def get_persistence_impl(self, source: PersistenceMethodSource):
        if source == PersistenceMethodSource.pandas:
            if self == PersistenceMethod.csv:
                return CsvPandasPersistenceMethod()
            if self == PersistenceMethod.pickle:
                return PicklePandasPersistenceMethod()

        raise NotImplementedError(f"No implement method for {source} and output {self}")


@typer_app.command()
def movinet(
    model_name: MovinetModelName,
    input_glob: str,
    features_output_path: Path,
    overwrite: bool = typer.Option(False, "-f", "--force"),
):
    if not overwrite and features_output_path.exists():
        raise ValueError(
            f"Use -f option to overwrite the existing output: {str(features_output_path)}"
        )

    assert features_output_path.parent.exists()
    assert features_output_path.parent.is_dir()

    print(f"Starting features extract for {model_name}")
    extract_movinet_features(
        model_name,
        input_glob,
        features_output_path,
        PersistenceMethod.get_from_extension(features_output_path).get_persistence_impl(
            PersistenceMethodSource.pandas
        ),
    )


@typer_app.command()
def actionclip(
    model_name: str,  # TODO
    model_pretrained_checkpoint: Path,
    list_input_sequences_file: Path,
    features_output_path: Path,
    device_type: DeviceType = DeviceType.cpu,
    distributed: bool = False,
    sync_server_host: Optional[str] = typer.Option(
        None, "--sync-sever-host", "--host", "-h"
    ),
    sync_server_port: Optional[int] = typer.Option(
        None, "--sync-server-port", "--port", "-P"
    ),
    overwrite: bool = typer.Option(False, "-f", "--force"),
):
    if not overwrite and features_output_path.exists():
        raise ValueError(
            f"Use -f option to overwrite the existing output: {str(features_output_path)}"
        )

    assert features_output_path.parent.exists()
    assert features_output_path.parent.is_dir()

    print(f"Starting features extract for {model_name}")

    with alternate_device(
        device_type, distributed, sync_server_host, sync_server_port
    ) as device:
        (
            model_image,
            model_text,
            fusion_model,
            preprocess_image,
        ) = create_models_and_transforms(
            actionclip_pretrained_ckpt=model_pretrained_checkpoint,
            openai_model_name="ViT-B-16",
        )

        ilids_dataset = ActionDataset(
            list_input_sequences_file, transform=get_augmentation()
        )
        batch_size = 64  # 2
        ilids_loader = DataLoader(
            ilids_dataset,
            batch_size=batch_size,
            num_workers=1,
            shuffle=False,
            pin_memory=True,
        )

        extract_actionclip_sequences_features(
            model_image, fusion_model, ilids_loader, device
        )
