from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from joblib import cpu_count
from torch.utils.data import DataLoader

from ilids.experiments.actionclip import extract_actionclip_sequences_features
from ilids.experiments.movinet import extract_movinet_features
from ilids.models.actionclip.datasets import ActionDataset
from ilids.models.actionclip.factory import create_models_and_transforms
from ilids.models.actionclip.transform import get_augmentation
from ilids.synchronization.alternate_device import DeviceType, alternate_device
from ilids.towhee_utils.override.movinet import MovinetModelName
from ilids.utils.notify import notify_context
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
    notify: bool = typer.Option(
        False, "--notify", help="notify using ML Notify by Aporia"
    ),
):
    if not overwrite and features_output_path.exists():
        raise ValueError(
            f"Use -f option to overwrite the existing output: {str(features_output_path)}"
        )

    assert features_output_path.parent.exists()
    assert features_output_path.parent.is_dir()

    with notify_context(enable=notify):
        print(f"Starting features extract for {model_name}...")
        features_df = extract_movinet_features(
            model_name,
            input_glob,
        )

        PersistenceMethod.get_from_extension(features_output_path).get_persistence_impl(
            PersistenceMethodSource.pandas
        ).persist(features_output_path, features_df)


@typer_app.command()
def actionclip(
    model_name: str,
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
    batch_size: int = typer.Option(2 << 3, "-b", "--batch-size"),
    loader_num_workers: Optional[int] = typer.Option(
        None, "-w", "--workers", help="Number of workers for the Torch.DataLoader"
    ),
    notify: bool = typer.Option(
        False, "--notify", help="notify using ML Notify by Aporia"
    ),
):
    if not overwrite and features_output_path.exists():
        raise ValueError(
            f"Use -f option to overwrite the existing output: {str(features_output_path)}"
        )

    assert features_output_path.parent.exists()
    assert features_output_path.parent.is_dir()

    with notify_context(enable=notify), alternate_device(
        device_type, distributed, sync_server_host, sync_server_port
    ) as device:
        print(f"Starting features extract for {model_name}...")

        (
            model_image,
            model_text,
            fusion_model,
            preprocess_image,
        ) = create_models_and_transforms(
            actionclip_pretrained_ckpt=model_pretrained_checkpoint,
            openai_model_name=model_name,
        )

        ilids_dataset = ActionDataset(
            list_input_sequences_file, transform=get_augmentation()
        )
        loader_num_workers = loader_num_workers or cpu_count()
        ilids_loader = DataLoader(
            ilids_dataset,
            batch_size=batch_size,
            num_workers=loader_num_workers,
            shuffle=False,
            pin_memory=True,
        )

        features_df = extract_actionclip_sequences_features(
            model_image, fusion_model, ilids_loader, device
        )

        PersistenceMethod.get_from_extension(features_output_path).get_persistence_impl(
            PersistenceMethodSource.pandas
        ).persist(features_output_path, features_df)
