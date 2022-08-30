from collections import OrderedDict
from pathlib import Path

import xmltodict

from ilids.utils.encoding import get_file_encoding


def read_xml(file_path: Path) -> OrderedDict:
    # by default, those xml files are encoded in utf-16, therefore, we can't rely on the default
    # encoding of python 'open' function
    with open(file_path, "r", encoding=get_file_encoding(file_path)) as f:
        return xmltodict.parse(f.read())
