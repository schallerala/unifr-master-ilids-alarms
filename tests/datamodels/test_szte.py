import pytest
from hamcrest import *

from ilids.datamodels.szte import IlidsLibrary


@pytest.fixture()
def raw_library_clips_with_alarms() -> str:
    return """{
        "scenario": "Sterile Zone",
        "dataset": "Test",
        "libversion": "1.0",
        "clip": [{
            "filename": "SZTEA101a.qtl",
            "Stage": "1",
            "AlarmEvents": "10",
            "Duration": "00:37:11",
            "Weather": {
                "TimeOfDay": "Dawn",
                "Clouds": "None",
                "Rain": "No",
                "Snow": "No",
                "Fog": "No"
            },
            "Distractions": {
                "Distraction": "Camera switch from monochrome to colour"
            },
            "Alarms": {
                "Alarm": [
                    {
                        "StartTime": "00:05:37",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:00",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:08:58",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:08",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crawl",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:12:12",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:00",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:15:14",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:38",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:18:41",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:52",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:21:32",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:53",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:24:44",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:07",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:27:58",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:01",
                        "Distance": "15",
                        "SubjectDescription": "Two people",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:31:14",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:02:29",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Diagonal"
                    },
                    {
                        "StartTime": "00:35:51",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:31",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk With Ladder",
                        "SubjectOrientation": "Perpendicular"
                    }
                ]
            }
        }]
    }"""


@pytest.fixture()
def raw_library_clips_without_alarms() -> str:
    return """{
        "scenario": "Sterile Zone",
        "dataset": "Test",
        "libversion": "1.0",
        "clip": [{
            "filename": "SZTEN101b.qtl",
            "Stage": "1",
            "AlarmEvents": "0",
            "Duration": "00:30:00",
            "Weather": {
                "TimeOfDay": "Day",
                "Clouds": "None",
                "Rain": "No",
                "Snow": "No",
                "Fog": "No"
            },
            "Distractions": {
                "Distraction": ["Rabbits", "Shadow through fence"]
            }
        }]
    }"""


@pytest.fixture()
def raw_library_clips_without_distraction() -> str:
    return """{
        "scenario": "Sterile Zone",
        "dataset": "Test",
        "libversion": "1.0",
        "clip": [{
            "filename": "SZTEA103a.qtl",
            "Stage": "1",
            "AlarmEvents": "17",
            "Duration": "00:47:14",
            "Weather": {
                "TimeOfDay": "Day",
                "Clouds": "Some",
                "Rain": "No",
                "Snow": "No",
                "Fog": "No"
            },
            "Alarms": {
                "Alarm": [
                    {
                        "StartTime": "00:06:17",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:02",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:08:46",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:54",
                        "Distance": "15",
                        "SubjectDescription": "Two people",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:11:21",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:57",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Diagonal"
                    },
                    {
                        "StartTime": "00:13:38",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:50",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:16:19",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:05",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:18:38",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:04",
                        "Distance": "30",
                        "SubjectDescription": "Two people",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:21:23",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:10",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:23:55",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:55",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:26:10",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:02",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:28:50",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:07",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Diagonal"
                    },
                    {
                        "StartTime": "00:31:50",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:03",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:34:09",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:03",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Walk",
                        "SubjectOrientation": "Diagonal"
                    },
                    {
                        "StartTime": "00:36:41",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:08",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crawl",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:39:36",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:23",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Body Drag",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:42:09",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:57",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:44:25",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:50",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:46:44",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:30",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk With Ladder",
                        "SubjectOrientation": "Perpendicular"
                    }
                ]
            }
        }]
    }"""


@pytest.fixture()
def raw_library_clips_with_one_distraction() -> str:
    return """{
        "scenario": "Sterile Zone",
        "dataset": "Test",
        "libversion": "1.0",
        "clip": [{
            "filename": "SZTEN102b.qtl",
            "Stage": "1",
            "AlarmEvents": "0",
            "Duration": "00:30:00",
            "Weather": {
                "TimeOfDay": "Day",
                "Clouds": "Overcast",
                "Rain": "Yes",
                "Snow": "No",
                "Fog": "No"
            },
            "Distractions": { "Distraction": "Birds" }
        }]
    }"""


@pytest.fixture()
def raw_library_clips_with_multiple_distractions() -> str:
    return """{
        "scenario": "Sterile Zone",
        "dataset": "Test",
        "libversion": "1.0",
        "clip": [{
            "filename": "SZTEN101b.qtl",
            "Stage": "1",
            "AlarmEvents": "0",
            "Duration": "00:30:00",
            "Weather": {
                "TimeOfDay": "Day",
                "Clouds": "None",
                "Rain": "No",
                "Snow": "No",
                "Fog": "No"
            },
            "Distractions": {
                "Distraction": ["Rabbits", "Shadow through fence"]
            }
        }]
    }"""


@pytest.fixture()
def raw_library_with_multiple_clips_with_multiple_distractions_multiple_alarms() -> str:
    return """{
        "scenario": "Sterile Zone",
        "dataset": "Test",
        "libversion": "1.0",
        "clip": [{
            "filename": "SZTEA204a.qtl",
            "Stage": "2",
            "AlarmEvents": "31",
            "Duration": "01:32:12",
            "Weather": {
                "TimeOfDay": "Night",
                "Rain": "No",
                "Snow": "No",
                "Fog": "No"
            },
            "Distractions": { "Distraction": "Bats" },
            "Alarms": {
                "Alarm": [
                    {
                        "StartTime": "00:07:06",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:57",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:09:45",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:54",
                        "Distance": "15",
                        "SubjectDescription": "Two people",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:12:54",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:28",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:15:54",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:04",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:18:41",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:18",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Body Drag",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:21:29",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:41",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Body Drag",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:25:07",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:16",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Body Drag",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:28:33",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:49",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Diagonal"
                    },
                    {
                        "StartTime": "00:30:54",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:57",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:33:15",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:57",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:35:29",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:59",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:37:57",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:53",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:41:01",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:57",
                        "Distance": "10",
                        "SubjectDescription": "Two people",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:43:28",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:36",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:46:53",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:56",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:49:35",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:58",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:52:12",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:09",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crawl",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:54:48",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:20",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crawl",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:57:37",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:27",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Log Roll",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:00:41",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:12",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:03:22",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:03",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Diagonal"
                    },
                    {
                        "StartTime": "01:06:08",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:08",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:09:28",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:51",
                        "Distance": "30",
                        "SubjectDescription": "Two people",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:13:00",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:42",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Diagonal"
                    },
                    {
                        "StartTime": "01:16:10",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:32",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:19:21",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:03",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:21:56",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:08",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crawl",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:24:45",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:09",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Log Roll",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:27:06",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:51",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:29:45",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:51",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "01:31:46",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:26",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk With Ladder",
                        "SubjectOrientation": "Perpendicular"
                    }
                ]
            }
        }, {
            "filename": "SZTEA101b.qtl",
            "Stage": "1",
            "AlarmEvents": "15",
            "Duration": "00:49:46",
            "Weather": {
                "TimeOfDay": "Dusk",
                "Clouds": "Overcast",
                "Rain": "No",
                "Snow": "No",
                "Fog": "No"
            },
            "Distractions": {
                "Distraction": [
                    "Camera switch from colour to monochrome",
                    "Bats"
                ]
            },
            "Alarms": {
                "Alarm": [
                    {
                        "StartTime": "00:07:45",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:31",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:10:40",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:46",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:13:56",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:59",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Diagonal"
                    },
                    {
                        "StartTime": "00:16:17",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:05",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:18:50",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:05",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:21:12",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:06",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crouch Run",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:24:02",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:37",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:26:51",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:52",
                        "Distance": "30",
                        "SubjectDescription": "Two people",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:29:16",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:41",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Creep walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:32:26",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:29",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Body Drag",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:35:29",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:20",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Diagonal"
                    },
                    {
                        "StartTime": "00:38:29",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:58",
                        "Distance": "10",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:41:47",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:11",
                        "Distance": "10",
                        "SubjectDescription": "Two people",
                        "SubjectApproachType": "Walk",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:45:54",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:01:05",
                        "Distance": "30",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Crawl",
                        "SubjectOrientation": "Perpendicular"
                    },
                    {
                        "StartTime": "00:48:48",
                        "AlarmDescription": "Fence Attack",
                        "AlarmDuration": "00:00:42",
                        "Distance": "15",
                        "SubjectDescription": "One Person",
                        "SubjectApproachType": "Walk With Ladder",
                        "SubjectOrientation": "Perpendicular"
                    }
                ]
            }
        }]
    }"""


def test_parse_clip_with_alarm(raw_library_clips_with_alarms):
    IlidsLibrary.parse_raw(raw_library_clips_with_alarms)


def test_parse_clip_without_alarm(raw_library_clips_without_alarms):
    IlidsLibrary.parse_raw(raw_library_clips_without_alarms)


def test_get_library_alarms(raw_library_clips_with_alarms):
    lib = IlidsLibrary.parse_raw(raw_library_clips_with_alarms)

    assert_that(len(lib.flat_map_alarms_dict()), is_(10))


def test_get_library_alarms_without_alarms(raw_library_clips_without_alarms):
    lib = IlidsLibrary.parse_raw(raw_library_clips_without_alarms)

    assert_that(len(lib.flat_map_alarms_dict()), is_(0))


def test_parse_clip_without_distraction(raw_library_clips_without_distraction):
    IlidsLibrary.parse_raw(raw_library_clips_without_distraction)


def test_get_library_distraction_without_distraction(
    raw_library_clips_without_distraction,
):
    lib = IlidsLibrary.parse_raw(raw_library_clips_without_distraction)

    assert_that(len(lib.flat_map_distractions_dict()), is_(0))


def test_parse_clip_with_one_distraction(raw_library_clips_with_one_distraction):
    IlidsLibrary.parse_raw(raw_library_clips_with_one_distraction)


def test_get_library_distraction_with_one_distraction(
    raw_library_clips_with_one_distraction,
):
    lib = IlidsLibrary.parse_raw(raw_library_clips_with_one_distraction)

    assert_that(len(lib.flat_map_distractions_dict()), is_(1))


def test_parse_clip_with_multiple_distractions(
    raw_library_clips_with_multiple_distractions,
):
    IlidsLibrary.parse_raw(raw_library_clips_with_multiple_distractions)


def test_get_library_distraction_with_multiple_distractions(
    raw_library_clips_with_multiple_distractions,
):
    lib = IlidsLibrary.parse_raw(raw_library_clips_with_multiple_distractions)

    assert_that(len(lib.flat_map_distractions_dict()), is_(2))


def test_parse_with_multiple_clips_with_multiple_distractions_multiple_alarms(
    raw_library_with_multiple_clips_with_multiple_distractions_multiple_alarms,
):
    IlidsLibrary.parse_raw(
        raw_library_with_multiple_clips_with_multiple_distractions_multiple_alarms
    )


def test_get_library_with_multiple_clips_with_multiple_distractions_multiple_alarms(
    raw_library_with_multiple_clips_with_multiple_distractions_multiple_alarms,
):
    lib = IlidsLibrary.parse_raw(
        raw_library_with_multiple_clips_with_multiple_distractions_multiple_alarms
    )

    assert_that(len(lib.flat_map_alarms_dict()), is_(31 + 15))
    assert_that(len(lib.flat_map_distractions_dict()), is_(3))
