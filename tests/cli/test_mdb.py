from pathlib import Path

import pytest
from hamcrest import *

from ilids.cli.mdb import export_all_tables, mdb_export_table


@pytest.mark.sztr_files(("SZTR.mdb", "mdb_file"))
@pytest.mark.parametrize(
    "table,entries,columns",
    [
        ("CLIPDATA", 3894, 5),
        ("CLIPS", 236, 5),
        ("DATASTRUCTURE", 19, 5),
        ("LIBRARIES", 1, 4),
    ],
)
def test_export_table(mdb_file: Path, table, entries, columns):
    table_data = mdb_export_table(mdb_file, table)
    assert_that(len(table_data), is_(entries))
    assert_that(len(table_data.columns), is_(columns))


@pytest.mark.sztr_files(("SZTR.mdb", "mdb_file"))
def test_export_all_tables(mdb_file: Path):
    tables_df = export_all_tables(mdb_file)
    assert_that(
        tables_df.keys(),
        contains_inanyorder("CLIPDATA", "CLIPS", "DATASTRUCTURE", "LIBRARIES"),
    )
