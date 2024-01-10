from typing import Union

import strictyaml as yml

from officialeye.diffobject.difference_modes import DIFF_MODE_OVERRIDE, DIFF_MODE_ADD, DIFF_MODE_REMOVE
from officialeye.diffobject.exception import DiffObjectException
from officialeye.diffobject.specification_entry import DiffObjectSpecificationEntry


class IntegerSpecificationEntry(DiffObjectSpecificationEntry):

    def __init__(self, validator: yml.Validator, /):
        super().__init__(validator)

    def apply_diff(self, current_value: Union[int, None], diff_value: int, diff_mode: str) -> int:
        assert current_value is None or isinstance(current_value, int)
        assert isinstance(diff_value, int)

        if diff_mode == DIFF_MODE_OVERRIDE:
            return diff_value

        if current_value is None:
            raise DiffObjectException(f"Could not apply difference mode '{diff_mode}' because the previous value is not available.")

        if diff_mode == DIFF_MODE_ADD:
            return current_value + diff_value

        if diff_mode == DIFF_MODE_REMOVE:
            return current_value - diff_value

        raise DiffObjectException(f"The integer type is incompatible with difference mode specification '{diff_mode}'.")
