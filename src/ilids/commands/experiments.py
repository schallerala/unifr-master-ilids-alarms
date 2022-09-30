from enum import Enum
from pathlib import Path

import torch
import typer

from ilids.experiments.movinet import extract_movinet_features
from ilids.synchronization.acquire_gpu_client import acquire_free_gpu
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
    input_glob: str,
    features_output_path: Path,
    sync_server_host: str = typer.Option(
        "localhost", "--sync-sever-host", "--host", "-h"
    ),
    sync_server_port: int = typer.Option(..., "--sync-server-port", "--port", "-P"),
    overwrite: bool = typer.Option(False, "-f", "--force"),
):
    if not overwrite and features_output_path.exists():
        raise ValueError(
            f"Use -f option to overwrite the existing output: {str(features_output_path)}"
        )

    assert features_output_path.parent.exists()
    assert features_output_path.parent.is_dir()

    print(f"Starting features extract for {model_name}")

    with acquire_free_gpu(sync_server_host, sync_server_port) as gpu_id:
        device = torch.device("cuda", gpu_id)

        # TODO implement
