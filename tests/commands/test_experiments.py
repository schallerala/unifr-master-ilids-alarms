from pathlib import Path

import pytest
from typer.testing import CliRunner

from ilids.commands.experiments import typer_app

runner = CliRunner(mix_stderr=False)


@pytest.mark.handcrafted_files(("actionclip_sequences.csv", "actionclip_sequences"))
@pytest.mark.ckpt_files((Path("actionclip") / "vit-b-16-16f.pt", "actionclip_ckpt"))
@pytest.mark.long
def test_actionclip(actionclip_sequences: Path, actionclip_ckpt: Path, tmp_path: Path):
    result = runner.invoke(
        typer_app,
        [
            "actionclip",
            "ViT-B-16",
            str(actionclip_ckpt),
            str(actionclip_sequences),
            str(tmp_path / "output.pkl"),
        ],
    )

    assert result.exit_code == 0
