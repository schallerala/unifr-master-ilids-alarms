"""
Folder structure:

    SZTR/
    ├── calibration/        # Don't care, old .tif files
    ├── index-files/        # Html etc. files for their web interface, to browser and
    │                       #   filter the clips
    ├── video/              # Holds the videos in pairs with their xml files holding
    │   │                   #   video metadata
    │   ├── SZTRA101a01.mov
    │   ├── ... 235 videos later
    │   └── SZTRN203a.mov
    ├── i-LIDS Flyer.pdf        # General purpose 1 page flyer describing the different
    │                           #   i-LIDS datasets
    ├── index.xml               # Holds the perturbation annotations for the sequences
    │                           #   in the video/folder
    ├── Sterile Zone.pdf        # Short pdf describing the dataset and the structure of
    │                           #   the index.xml file
    ├── SZTR.mdb                # Database holding 4 tables: CLIPDATA, CLIPS, DATASTRUCTURE, LIBRARIES
    └── User Guide.pdf          # Guide for the licensing, distribution, web app and more
"""
