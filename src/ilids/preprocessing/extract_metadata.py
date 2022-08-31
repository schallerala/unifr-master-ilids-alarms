import typer

import ilids.preprocessing.szte.extract_index_metadata_szte as szte_index

typer_app = typer.Typer()

typer_app.add_typer(szte_index.typer_app, name="szte-index")


if __name__ == "__main__":
    typer_app()
