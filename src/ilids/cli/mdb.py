"""
mdb-tables --single-column ../SZTR/SZTR.mdb | \
   xargs -I{} sh -c \
   'mdb-export ../SZTR/SZTR.mdb {} > ../SZTR/$(echo {} | tr "[:upper:]" "[:lower:]").csv'
"""
import io
import subprocess
from pathlib import Path
from typing import Dict, List

import pandas as pd
from pandas import DataFrame


def mdb_tables(mdb: Path) -> List[str]:
    mdb_tables_command = ["mdb-tables", "--single-column", str(mdb)]

    mdb_tables_process = subprocess.Popen(mdb_tables_command, stdout=subprocess.PIPE)

    stdout, stderr = mdb_tables_process.communicate()

    assert (
        mdb_tables_process.returncode == 0
    ), f"mdb-tables didn't run successfully {stderr.decode()}"

    return stdout.decode().splitlines()


def mdb_export_table(mdb: Path, table_name: str) -> DataFrame:
    mdb_export_command = ["mdb-export", str(mdb), table_name]

    mdb_export_process = subprocess.Popen(mdb_export_command, stdout=subprocess.PIPE)

    stdout, stderr = mdb_export_process.communicate()

    assert (
        mdb_export_process.returncode == 0
    ), f"mdb-export didn't run successfully {stderr.decode()}"

    return pd.read_csv(io.StringIO(stdout.decode()))


def export_all_tables(mdb: Path) -> Dict[str, DataFrame]:
    tables = mdb_tables(mdb)

    return {table: mdb_export_table(mdb, table) for table in tables}
