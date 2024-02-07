import abc
from abc import ABC

import cv2

from officialeye._internal.context.singleton import get_internal_afi, get_internal_context
from officialeye._internal.matching.matcher_config import KeypointMatcherConfig
from officialeye._internal.matching.result import MatchingResult


class Matcher(ABC):
    # TODO: remove this module and migrate completely to officialeye._api

    def __init__(self, engine_id: str, template_id: str, img: np.ndarray, /):
        super().__init__()

        self._engine_id = engine_id

        self.template_id = template_id

        # retreive configurations for all keypoint matching engines
        matching_config = self.get_template().get_matching_config()

        assert isinstance(matching_config, dict)

        # get the configuration for the particular engine of interest
        if self._engine_id in matching_config:
            config_dict = matching_config[self._engine_id]
        else:
            get_internal_afi().warn(
                self._context,
                f"Could not find any configuration entries for the '{self._engine_id}' matching engine that is being used."
            )
            config_dict = {}

        self._config = KeypointMatcherConfig(config_dict, engine_id)

        self._img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    @abc.abstractmethod
    def match_keypoint(self, pattern: np.ndarray, keypoint_id: str, /):
        raise NotImplementedError()

    @abc.abstractmethod
    def match_finish(self) -> MatchingResult:
        raise NotImplementedError()

    def get_template(self):
        return get_internal_context().get_template(self.template_id)

    def get_config(self) -> KeypointMatcherConfig:
        return self._config