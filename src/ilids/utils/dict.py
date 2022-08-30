from functools import reduce
from typing import Any, Dict, OrderedDict, Union


def deep_get(dictionary: Union[Dict, OrderedDict], keys: str) -> Any:
    """Inspiration https://stackoverflow.com/a/46890853/3771148"""
    return reduce(lambda d, key: d[key], keys.split("."), dictionary)
