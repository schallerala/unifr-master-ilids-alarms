import typer

from ilids.commands.video_utils import typer_app as video_utils_typer_app


typer_app = typer.Typer()

typer_app.add_typer(video_utils_typer_app, name="video-utils")


if __name__ == "__main__":
    typer_app()
