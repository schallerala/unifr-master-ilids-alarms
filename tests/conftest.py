import os
from pathlib import Path

import pytest


@pytest.fixture()
def szte_path() -> Path:
    return Path(os.getcwd()) / "SZTE"


@pytest.fixture()
def sztr_path() -> Path:
    return Path(os.getcwd()) / "SZTR"


def _data_file_marker_builder(request, marker_name: str, parent_folder: Path):
    marker = request.node.get_closest_marker(marker_name)
    if marker:
        for file, variable_name in marker.args:
            if (parent_folder / Path(file)).exists():
                request.node.fixturenames.append(variable_name)
                request.node.funcargs[variable_name] = parent_folder / Path(file)
            elif Path(file).exists():
                request.node.add_marker(
                    pytest.mark.parametrize(variable_name, [Path(file)])
                )
            else:
                pytest.skip(f"skipped as file {str(parent_folder / file)} is missing")


@pytest.fixture(autouse=True)
def add_data_files_markers(request, szte_path: Path, sztr_path):
    _data_file_marker_builder(request, "szte_files", szte_path)
    _data_file_marker_builder(request, "sztr_files", sztr_path)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "szte_files(...files): skip test if one of the given file name doesn't exists",
    )
    config.addinivalue_line(
        "markers",
        "sztr_files(...files): skip test if one of the given file name doesn't exists",
    )
