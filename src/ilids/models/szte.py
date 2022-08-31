# generated by datamodel-codegen:
#   filename:  index-library.tmp.json
#   timestamp: 2022-08-14T13:21:26+00:00

"""
Can be generated with the help of datamodel_code_generator like so:

# Extract only part of the produced structure (IlidsLibraryIndex.Library)
ilids_library_xml = deep_get(index_xml, "IlidsLibraryIndex.Library")

datamodel_code_generator.generate(
    json.dumps(ilids_library_xml),
    input_file_type=datamodel_code_generator.InputFileType.Json,
    output=Path(".") / "szte.py",
    target_python_version=datamodel_code_generator.PythonVersion.PY_310,
    class_name="IlidsLibrary"
)

# However, a few adaptation are done to improve the typing of certain fields
"""

from __future__ import annotations

from datetime import time
from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class AlarmItem(BaseModel):
    AlarmDescription: str
    AlarmDuration: time
    Distance: int
    StartTime: time
    SubjectApproachType: str
    SubjectDescription: str
    SubjectOrientation: str


class Alarms(BaseModel):
    Alarm: List[AlarmItem]


class Distractions(BaseModel):
    Distraction: Union[str, List[str]]

    def unsqueeze(self) -> List[str]:
        return self.Distraction if isinstance(self.Distraction, list) else [self.Distraction]


class Weather(BaseModel):
    Clouds: Optional[str] = None
    Fog: bool
    Rain: bool
    Snow: bool
    TimeOfDay: str


class ClipItem(BaseModel):
    AlarmEvents: int
    Alarms: Optional[Alarms] = None
    Distractions: Optional[Distractions] = None
    Duration: time
    Stage: int
    Weather: Weather
    filename: str

    def dict_clip_information(self) -> Dict:
        return self.dict(exclude={"Alarms", "Distractions"})

    def get_alarms_dict(self) -> List[Dict]:
        return (
            []
            if self.AlarmEvents == 0
            else [
                dict(filename=self.filename, **alarm.dict())
                for alarm in self.Alarms.Alarm
            ]
        )

    def get_distractions_dict(self) -> List[Dict]:
        return [] if self.Distractions is None else [
            dict(filename=self.filename, distraction=distraction)
            for distraction in self.Distractions.unsqueeze()
        ]


class IlidsLibrary(BaseModel):
    clip: List[ClipItem]
    dataset: str
    libversion: str
    scenario: str

    def get_clips_information_dict(self) -> List[Dict]:
        return [clip.dict_clip_information() for clip in self.clip]

    def flat_map_alarms_dict(self) -> List[Dict]:
        return [alarm for clip in self.clip for alarm in clip.get_alarms_dict()]

    def flat_map_distractions_dict(self) -> List[Dict]:
        return [
            distraction
            for clip in self.clip
            for distraction in clip.get_distractions_dict()
        ]
