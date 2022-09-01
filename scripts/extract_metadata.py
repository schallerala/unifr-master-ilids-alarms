import typer

import ilids.commands.szte.extract_index_metadata_szte as szte_index
import ilids.commands.szte.extract_video_metadata_szte as szte_video

typer_app = typer.Typer()

typer_app.add_typer(szte_index.typer_app, name="szte-index")
typer_app.add_typer(szte_video.typer_app, name="szte-videos")


if __name__ == "__main__":
    typer_app()
