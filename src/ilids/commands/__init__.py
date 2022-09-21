import typer

import ilids.commands.experiments as experiments
import ilids.commands.ilids_aggregate.ilids_indexes as ilids_indexes
import ilids.commands.ilids_aggregate.ilids_videos as ilids_videos
import ilids.commands.szte.extract_index_metadata_szte as szte_index
import ilids.commands.szte.extract_video_metadata_szte as szte_video
import ilids.commands.sztr.extract_index_metadata_sztr as sztr_index
import ilids.commands.sztr.extract_video_metadata_sztr as sztr_video
import ilids.commands.videos.frames_extraction as videos_frames
import ilids.commands.videos.videos_compress as videos_compress

typer_app = typer.Typer()

szte_typer_app = typer.Typer()

szte_typer_app.add_typer(szte_index.typer_app, name="index")
szte_typer_app.add_typer(szte_video.typer_app, name="videos")

sztr_typer_app = typer.Typer()

sztr_typer_app.add_typer(sztr_index.typer_app, name="index")
sztr_typer_app.add_typer(sztr_video.typer_app, name="videos")

ilids_typer_app = typer.Typer()

ilids_typer_app.add_typer(ilids_indexes.typer_app, name="indexes")
ilids_typer_app.add_typer(ilids_videos.typer_app, name="videos")

videos_typer_app = typer.Typer()

videos_typer_app.add_typer(videos_compress.typer_app, name="compress")
videos_typer_app.add_typer(videos_frames.typer_app, name="frames")

typer_app.add_typer(szte_typer_app, name="szte")
typer_app.add_typer(sztr_typer_app, name="sztr")
typer_app.add_typer(ilids_typer_app, name="ilids")
typer_app.add_typer(videos_typer_app, name="videos")
typer_app.add_typer(experiments.typer_app, name="experiments")
