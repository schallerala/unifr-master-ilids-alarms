from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from ilids.commands.experiments import typer_app

runner = CliRunner(mix_stderr=False)


@pytest.mark.handcrafted_files(("actionclip_sequences.csv", "actionclip_sequences"))
@pytest.mark.ckpt_files((Path("actionclip") / "vit-b-16-8f.pt", "actionclip_ckpt"))
def test_actionclip(actionclip_sequences: Path, actionclip_ckpt: Path, tmp_path: Path):
    output_path = tmp_path / "output.pkl"

    input_df = pd.read_csv(actionclip_sequences)

    min_input_path = tmp_path / "min_input.csv"
    input_df.head(n=2).to_csv(min_input_path)

    result = runner.invoke(
        typer_app,
        [
            "actionclip",
            str(actionclip_ckpt),
            str(min_input_path),
            str(output_path),
        ],
    )

    assert result.exit_code == 0

    assert output_path.exists() and output_path.is_file()

    df = pd.read_pickle(output_path)

    assert len(df) == 2
    assert len(df.columns) == 512, df.columns
