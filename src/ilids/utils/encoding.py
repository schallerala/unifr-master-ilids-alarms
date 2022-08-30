from pathlib import Path

from chardet.universaldetector import UniversalDetector


def get_file_encoding(
    file_path: Path, detector: UniversalDetector = UniversalDetector()
) -> str:
    detector.reset()

    for line in open(file_path, "rb"):
        detector.feed(line)
        if detector.done:
            return detector.close().get("encoding")

    return "utf-8"
