from pathlib import Path

from hamcrest import *

from ilids.subcommand.mdb import export_all_tables, mdb_export_table


def test_export_table():
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    table_data = mdb_export_table(source_dir / "SZTR.mdb", "CLIPDATA")
    assert_that(len(table_data), is_(3894))


def test_export_all_tables():
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    tables_df = export_all_tables(source_dir / "SZTR.mdb")
    assert_that(
        tables_df.keys(),
        contains_inanyorder("CLIPDATA", "CLIPS", "DATASTRUCTURE", "LIBRARIES"),
    )
