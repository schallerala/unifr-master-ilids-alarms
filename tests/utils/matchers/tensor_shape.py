from typing import Optional, Sequence, Tuple, TypeVar, Union

import torch
from hamcrest import is_
from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.description import Description
from hamcrest.core.matcher import Matcher

T = TypeVar("T")


class TensorShapeComparison(BaseMatcher[torch.Tensor]):
    def __init__(self, matcher: Matcher[Sequence[int]]) -> None:
        self.matcher = matcher

    def matches(
        self, item: torch.Tensor, mismatch_description: Optional[Description] = None
    ) -> bool:
        return self.matcher.matches(
            tuple((dim for dim in item.shape)), mismatch_description
        )

    def describe_mismatch(
        self, item: torch.Tensor, mismatch_description: Description
    ) -> None:
        return self.matcher.describe_mismatch(item, mismatch_description)

    def describe_to(self, description: Description):
        description.append_description_of(self.matcher)


def is_tensor_with_shape(
    matcher: Union[Tuple, Matcher[torch.Tensor]]
) -> Matcher[torch.Tensor]:
    if isinstance(matcher, tuple):
        return TensorShapeComparison(is_(matcher))

    return TensorShapeComparison(matcher)
