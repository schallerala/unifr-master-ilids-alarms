import typer

import ilids.commands.szte.extract_index_metadata_szte as szte_index
import ilids.commands.szte.extract_video_metadata_szte as szte_video

import ilids.commands.sztr.extract_index_metadata_sztr as sztr_index
import ilids.commands.sztr.extract_video_metadata_sztr as sztr_video

import ilids.commands.ilids_indexes as ilids_indexes
import ilids.commands.ilids_videos as ilids_videos

typer_app = typer.Typer()

typer_app.add_typer(szte_index.typer_app, name="szte-index")
typer_app.add_typer(szte_video.typer_app, name="szte-videos")

typer_app.add_typer(sztr_index.typer_app, name="sztr-index")
typer_app.add_typer(sztr_video.typer_app, name="sztr-videos")

typer_app.add_typer(ilids_indexes.typer_app, name="ilids-indexes")
typer_app.add_typer(ilids_videos.typer_app, name="ilids-videos")


if __name__ == "__main__":
    typer_app()
