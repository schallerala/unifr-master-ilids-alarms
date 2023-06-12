from itertools import combinations


POSITIVE_TEXTS = [
    "a human running",
    "a person running",
    "a picture of a human climbing a ladder",
    "a video of a human approaching a fence",
    "a video of a human approaching",
    "adult",
    "an adult running",
    "black and white picture of a human",
    "going through a fence",
    "grayscale picture of a human",
    "human against a wall",
    "human approaching a fence",
    "human bending down",
    "human climbing a ladder on a fence",
    "human climbing a ladder",
    "human cutting a fence",
    "human cutting",
    "human discretely moving towards a fence",
    "human going through a fence",
    "human going through",
    "human holding a ladder",
    "human kneeling down",
    "human making small steps",
    "human pick locking",
    "human stepping down",
    "human unlocking a door",
    "human walking",
    "human wearing a coat",
    "human wearing dark clothes",
    "human wearing light cloths",
    "human wearing white cloths",
    "human",
    "ladder leaning against a fence",
    "one person",
    "person creep walking",
    "person crip walking",
    "person",
    "putting a knee down",
    "ripping a fence",
    "terrorist",
    "thief",
]

NEGATIVE_TEXTS = [
    "animals",
    "bag",
    "barbed wire",
    "bird flying around",
    "birds flying",
    "black and white picture",
    "black and white scene of horror movie",
    "change of colorimetry",
    "cloudy field with a fence",
    "empty scene",
    "fence",
    "field at midnight",
    "field with green grass",
    "field",
    "foxes",
    "grayscale picture of a fence",
    "horror movie scene",
    "insect flying",
    "insects",
    "picture with artefacts",
    "plastic bag flying",
    "plastic bag laying on the floor",
    "rabbits",
    "video with artefacts",
    "wall",
]

def get_all_composition(lst):
    compositions = []
    length = len(lst)
    for r in range(1, length + 1):
        for combination in combinations(lst, r):
            compositions.append(list(combination))
    return compositions