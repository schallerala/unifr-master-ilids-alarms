import socketserver
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from ilids.synchronization.share_gpu_command import typer_app

runner = CliRunner(mix_stderr=False)


@pytest.fixture
def free_port():
    with socketserver.TCPServer(("localhost", 0), None) as s:
        free_port = s.server_address[1]

        return free_port


def test_serve_gpu_sync__missing_option(free_port: int):
    result = runner.invoke(
        typer_app,
        ["--port", free_port],
    )

    assert result.exit_code != 0


def test_serve_gpu_sync__too_many_options(free_port: int):
    result = runner.invoke(
        typer_app,
        [
            "--port",
            free_port,
            "--count",
            4,
            "--available",
            6,
        ],
    )

    assert result.exit_code != 0


def test_serve_gpu_sync__gpu_count(free_port: int):
    with patch("ilids.synchronization.share_gpu_command.DeleteFileLock") as Lock, patch(
        "ilids.synchronization.share_gpu_command.get_server_manager"
    ) as server_provider:
        result = runner.invoke(
            typer_app,
            ["--port", free_port, "--count", 4],
        )

        assert result.exit_code == 0

        Lock.assert_called()

        server_provider.assert_called_once_with(set(range(4)), free_port)


def test_serve_gpu_sync__available_gpus(free_port: int):
    with patch("ilids.synchronization.share_gpu_command.DeleteFileLock") as Lock, patch(
        "ilids.synchronization.share_gpu_command.get_server_manager"
    ) as server_provider:
        result = runner.invoke(
            typer_app,
            [
                "--port",
                free_port,
                "--available",
                2,
                "--available",
                3,
                "--available",
                5,
            ],
        )

        assert result.exit_code == 0

        Lock.assert_called()

        server_provider.assert_called_once_with({2, 3, 5}, free_port)


def test_serve_gpu_sync__available_gpus__duplicate(free_port: int):
    with patch("ilids.synchronization.share_gpu_command.DeleteFileLock") as Lock, patch(
        "ilids.synchronization.share_gpu_command.get_server_manager"
    ) as server_provider:
        result = runner.invoke(
            typer_app,
            [
                "--port",
                free_port,
                "--available",
                3,
                "--available",
                2,
                "--available",
                3,
                "--available",
                3,
                "--available",
                3,
                "--available",
                5,
            ],
        )

        assert result.exit_code == 0

        Lock.assert_called()

        server_provider.assert_called_once_with({3, 2, 5}, free_port)
