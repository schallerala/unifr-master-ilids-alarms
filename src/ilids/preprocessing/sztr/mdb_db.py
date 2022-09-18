"""This concentrates on the SZTR.mdb file/database at the root of SZTR.

With the mdb-tools cli:

    * getting the tables: `mdb-tables SZTR/SZTR.mdb`
    * getting their columns: `mdb-tables --single-column SZTR/SZTR.mdb | xargs -I_ sh -c 'echo _; mdb-export SZTR/SZTR.mdb _ | head -1'`
    * export all their content: **see ilids.cli.mdb**

It is expected to find the tables with its columns like so:

    CLIPDATA            # Equivalent to what is present in the index.xml but in a table
    │                   #   way, referring element id's from the DATASTRUCTURE.ElemID
    │
    ├── <empty>         # Line id
    ├── ClipdataID      # Id in this table
    ├── ClipID          # Id of the clip, referencing CLIPS.ClipID
    ├── ElemID          # Id of the "field/information", referencing DATASTRUCTURE.ElemID
    ├── value           # value
    └── ParentCID       # References the ClipdataID to build array like values
                        #   (think in a XML way)

    CLIPS               # List of all clips in the SZTR/video folder
    │
    ├── <empty>         # Line id
    ├── ClipID          # Id of the clip
    ├── VitalfileID     # Body of the video's filename (without the extension)
    ├── LibID           # Id of the ilids library, referencing LIBRARIES.LibID
    ├── stage           # Id of the stage of the camera (1 or 2)
    └── filename        # Video filename with the '.qtl' extension

    DATASTRUCTURE       # Mimic the index.xml's XML tags and referred by CLIPDATA
    │
    ├── <empty>         # Line id
    ├── ElemID          # Id of the element
    ├── Name            # Name of the element
    ├── Sort            # In case multiple element share the same parent, order then
    ├── Description     # Description of the element and in some cases the set of
    │                   #   their value
    └── Parent          # Parent element, referencing ElemID

    LIBRARIES       # Metadata of the library's state (single entry line + header)
    │
    ├── <empty>     # Line id
    ├── LibID       # Id of the ilids library
    ├── scenario    # => Sterile Zone
    ├── dataset     # => Training
    └── version     # -> 1.0

In short, no very relevant data to find here, as it can be more easily extracted from
the index.xml file.
"""
