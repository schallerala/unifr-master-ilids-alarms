import time
from pathlib import Path

import pytest
import towhee
import tqdm
from hamcrest import *
from towhee import register


@pytest.mark.understanding
def test_progress_map():
    def log_return(message: str, v):
        print(message)
        return v

    def sleep(v):
        time.sleep(v / 10)
        return v

    def log_progress(v):
        progress.update()
        return v

    dc: towhee.DataCollection = towhee.dc(range(5))
    progress = tqdm.tqdm(total=5)

    res = (
        dc.stream()
        .map(lambda x: log_return(f"Starting {x}", x))
        .map(sleep)
        .map(lambda x: log_return(f"End of {x}", x))
        .map(lambda x: log_progress(x))
        .to_list()
    )

    assert len(res) == 5
    assert progress.n == 5


@pytest.mark.understanding
def test_functional_dataframe(tmp_path):
    @register(name="ilids/test_parent_folder")
    def parent_folder(path):
        return Path(path).parent

    file1 = tmp_path / "file1.txt"
    file1.touch()
    file2 = tmp_path / "file2.txt"
    file2.touch()

    # with table like definition of property, will return a functional DataFrame
    res = towhee.dc["path"](
        towhee.glob(str(tmp_path / "*.txt"))
    ).ilids.test_parent_folder["path", "parent_path"]()

    assert_that(res, is_(instance_of(towhee.DataFrame)))

    res_list = res.to_list()
    assert len(res_list) == 2

    assert_that(
        res_list,
        only_contains(
            has_properties(
                {
                    "parent_path": is_(all_of(instance_of(Path), equal_to(tmp_path))),
                    "path": is_(instance_of(str)),
                }
            )
        ),
    )
    assert_that(
        res.map(lambda entity: entity.path).to_list(), has_items(str(file1), str(file2))
    )


@pytest.mark.understanding
def test_functional_dc(tmp_path):
    @register(name="ilids/test_parent_folder")
    def parent_folder(path):
        return Path(path).parent

    file1 = tmp_path / "file1.txt"
    file1.touch()
    file2 = tmp_path / "file2.txt"
    file2.touch()

    # with table like definition of property, will return a functional DataFrame
    res = towhee.dc(towhee.glob(str(tmp_path / "*.txt"))).ilids.test_parent_folder()

    assert_that(res, is_(instance_of(towhee.DataCollection)))

    res_list = res.to_list()
    assert len(res_list) == 2

    # Contains a list of the parents
    assert_that(res_list, only_contains(all_of(instance_of(Path), equal_to(tmp_path))))
