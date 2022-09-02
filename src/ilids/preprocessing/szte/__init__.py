"""
Folder structure:

    SZTE/
    ├── calibration/        # Don't care, old .tif files
    ├── index-files/        # Html etc. files for their web interface, to browser and
    │                       #   filter the clips
    ├── video/              # Holds the videos in pairs with their xml files holding
    │   │                   #   video metadata
    │   ├── SZTEA101a.mov
    │   ├── SZTEA101a.xml       # Meta data for file SZTEA101a.mov.
    │   │                       #   Holds only minor meta on the video format itself
    │   ├── ... 64 pairs later
    │   ├── SZTEN203a.mov
    │   └── SZTEN203a.xml
    ├── i-LIDS Flyer.pdf        # General purpose 1 page flyer describing the different
    │                           #   i-LIDS datasets
    ├── index.xml               # Holds the perturbation annotations for the sequences
    │                           #   in the video/folder
    ├── Sterile Zone.pdf        # Short pdf describing the dataset and the structure of
    │                           #   the index.xml file
    └── User Guide.pdf          # Guide for the licensing, distribution, web app and more
"""
