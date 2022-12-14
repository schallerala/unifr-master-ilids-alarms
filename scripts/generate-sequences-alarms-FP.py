#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pathlib import Path
from time import strftime, gmtime

import pandas as pd
import numpy as np
from tqdm import tqdm


# # Sequence generation
# 
# Generate the same amount of TP and FP:
# 
# * **TP**: The alarms in the alarms.csv
# * **FP**: Combinations of:
#     * _distractions_
#     * only background
# 
# TODO: How could one do that
# Try to distribute the load of sequence across video stages.

# In[2]:


# Student number
np.random.seed(16896375)


# In[3]:


PROJECT_DIR = Path("..")
DATA_DIR = PROJECT_DIR / "data"

ILIDS_META_DIR = DATA_DIR / "ilids-metadata"


# In[4]:


clips_csv = ILIDS_META_DIR / "clips.csv"

clips_df = pd.read_csv(clips_csv, index_col="filename")
clips_df = clips_df.drop(columns=["AlarmEvents", "Duration"])


# In[5]:


videos_csv = ILIDS_META_DIR / "videos.csv"

videos_df = pd.read_csv(videos_csv, index_col="format.filename")
videos_df["format.duration"] = pd.to_timedelta(
    videos_df["format.duration"], unit="second"
)


# In[6]:


alarms_csv = ILIDS_META_DIR / "alarms.csv"

alarms_df = pd.read_csv(alarms_csv, index_col="filename")

alarms_df["AlarmDuration"] = pd.to_timedelta(alarms_df["AlarmDuration"])
alarms_df["StartTime"] = pd.to_timedelta(alarms_df["StartTime"])
alarms_df["EndTime"] = alarms_df["StartTime"] + alarms_df["AlarmDuration"]

alarms_duration_min = alarms_df["AlarmDuration"].dt.seconds.min()
alarms_duration_max = alarms_df["AlarmDuration"].dt.seconds.max()


# In[7]:


hand_distractions_csv = (
    DATA_DIR / "handcrafted-metadata" / "szte_distractions.extended.corrected.csv"
)

distractions_df = pd.read_csv(hand_distractions_csv, index_col="filename")
distractions_df["start time"] = pd.to_timedelta(distractions_df["start time"])
distractions_df["end time"] = pd.to_timedelta(distractions_df["end time"])
distractions_df["duration"] = pd.to_timedelta(distractions_df["duration"])


# In[8]:


len(alarms_df), len(distractions_df)


# In[9]:


alarms_df = alarms_df.rename(columns={"AlarmDuration": "Duration"})
TP = alarms_df[
    [
        "StartTime",
        "EndTime",
        "Duration",
        "Distance",
        "SubjectApproachType",
        "SubjectDescription",
        "SubjectOrientation",
    ]
]
TP["Classification"] = "TP"


# In[10]:


distractions_df = distractions_df.rename(
    columns={
        "distraction": "Distraction",
        "start time": "StartTime",
        "end time": "EndTime",
        "duration": "Duration",
    }
)
distractions_df = distractions_df[["StartTime", "EndTime", "Duration", "Distraction"]]
distractions_df["Classification"] = "FP"


# In[11]:


SEQUENCES = pd.concat([TP, distractions_df])
SEQUENCES.head()


# In[12]:


SEQUENCES.tail()


# In[13]:


def apply_interval(df: pd.DataFrame) -> pd.arrays.IntervalArray:
    return pd.arrays.IntervalArray.from_arrays(
        df["StartTime"], df["EndTime"], closed="both"
    )


# In[14]:


SEQUENCES["Interval"] = apply_interval(SEQUENCES)
SEQUENCES.head()


# In[15]:


def check_in_sequences(df: pd.DataFrame, reference: pd.DataFrame) -> np.ndarray:
    # For matching filename and
    #   startTime <= start <= endTime or
    #   startTime <= end <= endTime

    # Example df to test
    # df = pd.DataFrame(
    #     {
    #         "StartTime": pd.to_timedelta([0, 0, 6 * 60], unit="second"),
    #         "EndTime": pd.to_timedelta([9 * 60, 12, 8 * 60], unit="second"),
    #         "filename": [
    #             "SZTE/SZTEA101a.mov",
    #             "SZTE/SZTEA101a.mov",
    #             "SZTE/SZTEA101a.mov",
    #         ],
    #     }
    # ).set_index("filename")

    matching_filename = df.index.intersection(reference.index)

    if len(matching_filename) == 0:
        return np.array([False] * len(df))

    def check_df_row(row, reference: pd.DataFrame):
        sub_reference = reference.loc[reference.index.intersection([row.name])]

        if len(sub_reference) == 0:
            return False

        return (
            sub_reference["Interval"]
            .array.overlaps(
                pd.Interval(row["StartTime"], row["EndTime"], closed="both")
            )
            .any()
        )

    return df.apply(check_df_row, axis=1, args=(reference,))


# In[16]:


def generate_new_false_positive_intervals(N: int) -> pd.DataFrame:
    video_files_idx = np.random.randint(0, len(videos_df), N)

    video_files = videos_df.index[video_files_idx]
    video_durations = videos_df.iloc[video_files_idx]["format.duration"]
    fp_durations = np.random.randint(alarms_duration_min, alarms_duration_max, N)
    fp_durations_delta = pd.to_timedelta(fp_durations, unit="second")

    video_remaining_proportion = video_durations - fp_durations_delta

    fp_start = (video_remaining_proportion * 0.95) * np.random.random(N)

    fp_df = pd.DataFrame(
        {
            "StartTime": pd.to_timedelta(fp_start, unit="second").dt.floor("S"),
            "Duration": fp_durations_delta,
        },
        index=video_files,
    )
    fp_df["EndTime"] = fp_df["StartTime"] + fp_df["Duration"]
    fp_df["Classification"] = "FP"

    return fp_df


# In[17]:


def drop_invalid_intervals(df: pd.DataFrame, inplace=True) -> pd.DataFrame:
    # In some cases, the generated duration is longer than the selected video's duration.
    # In this case, the 'StartTime' will be negative.
    # Drop them.
    dropping_rows = df[df["StartTime"] < pd.Timedelta(0, "second")].index

    df = df.drop(dropping_rows, inplace=inplace)

    return df


# In[18]:


def drop_intersect_interval(
    df: pd.DataFrame, reference: pd.DataFrame, inplace=True
) -> pd.DataFrame:
    # In case in the sequence to extract from the videos already has an intersecting
    # interval, drop them.
    dropping_rows = df[check_in_sequences(df, reference=reference)].index

    df = df.drop(dropping_rows, inplace=inplace)

    return df


# In[ ]:


TARGET_SEQUENCES = 2 * len(alarms_df)
missing_fp = TARGET_SEQUENCES - len(SEQUENCES)

progress = tqdm(
    total=TARGET_SEQUENCES,
    desc="Generating unique non overlapping sequences",
    initial=len(SEQUENCES),
)
while missing_fp > 0:
    fp_df = generate_new_false_positive_intervals(missing_fp)
    drop_invalid_intervals(fp_df)
    drop_intersect_interval(fp_df, SEQUENCES)

    fp_df["Interval"] = apply_interval(fp_df)

    SEQUENCES = pd.concat([SEQUENCES, fp_df])

    missing_fp = TARGET_SEQUENCES - len(SEQUENCES)

    progress.update(n=len(fp_df))


# In[ ]:


TARGET_SEQUENCES = 2 * len(alarms_df)
missing_fp = TARGET_SEQUENCES - len(SEQUENCES)

progress = tqdm(
    total=TARGET_SEQUENCES,
    desc="Generating unique non overlapping sequences",
    initial=len(SEQUENCES),
)
while missing_fp > 0:
    fp_df = generate_new_false_positive_intervals(missing_fp)
    drop_invalid_intervals(fp_df)
    drop_intersect_interval(fp_df, SEQUENCES)

    fp_df["Interval"] = apply_interval(fp_df)

    SEQUENCES = pd.concat([SEQUENCES, fp_df])

    missing_fp = TARGET_SEQUENCES - len(SEQUENCES)

    progress.update(n=len(fp_df))


# In[ ]:


SEQUENCES.tail()


# In[ ]:


SEQUENCES = SEQUENCES.join(clips_df)
SEQUENCES.index.rename("filename", inplace=True)


# In[ ]:


# Create unique indexes/identifier for later easier extraction of sequences
filename_series = SEQUENCES.index.to_series()
SEQUENCES["filename"] = filename_series

new_index_series = (
    filename_series.apply(lambda f: Path(f).stem)
    + "_"
    + SEQUENCES["StartTime"].dt.seconds.apply(
        lambda secs: strftime("%H_%M_%S", gmtime(secs))
    )
    + filename_series.apply(lambda f: Path(f).suffix)
)

new_index_series.rename("id_sequence", inplace=True)

new_index_series.head()


# In[ ]:


SEQUENCES = SEQUENCES.set_index(new_index_series).sort_index()

# Make sure to place filename colum first, for readability
SEQUENCES = SEQUENCES[pd.Index(["filename"]).append(SEQUENCES.columns.drop("filename"))]

SEQUENCES.head()


# In[ ]:


# Change to way time related column will be serialized in the new csv
SEQUENCES["StartTime"] = SEQUENCES["StartTime"].dt.seconds.apply(
    lambda secs: strftime("%H:%M:%S", gmtime(secs))
)
SEQUENCES["EndTime"] = SEQUENCES["EndTime"].dt.seconds.apply(
    lambda secs: strftime("%H:%M:%S", gmtime(secs))
)
SEQUENCES["Duration"] = SEQUENCES["Duration"].dt.seconds.apply(
    lambda secs: strftime("%H:%M:%S", gmtime(secs))
)
SEQUENCES.drop(columns="Interval", inplace=True)

SEQUENCES.to_csv(hand_distractions_csv.parent / "tp_fp_sequences.csv")

