"""This concentrates on the io of the index.xml file at the root of SZTR folder"""
from pathlib import Path

from ilids.models.sztr import IlidsLibrary
from ilids.preprocessing.szte import index_xml
from ilids.utils.dict import deep_get
from ilids.utils.xml import read_xml


def read_index_xml(index_xml: Path) -> IlidsLibrary:
    parsed_xml = read_xml(index_xml)

    # Extract only part of the produced structure (IlidsLibraryIndex.Library)
    ilids_library_xml = deep_get(parsed_xml, "IlidsLibraryIndex.Library")

    library = IlidsLibrary.parse_obj(ilids_library_xml)

    return library
