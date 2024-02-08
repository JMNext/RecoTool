from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Dict

import cv2
import numpy as np

from officialeye._api.template.feature import IFeature
from officialeye._api.template.match import IMatch
from officialeye.error.errors.general import ErrOperationNotSupported, ErrObjectNotInitialized

if TYPE_CHECKING:
    from officialeye._api.template.template_interface import ITemplate
    from officialeye._api.template.matching_result import IMatchingResult


class SupervisionResult:

    def __init__(self, matching_result: IMatchingResult, /, **kwargs):

        self._matching_result: IMatchingResult = matching_result

        # offset in the template's coordinates
        self._delta: np.ndarray | None = None
        # offset in the target image's coordinates
        self._delta_prime: np.ndarray | None = None

        self._transformation_matrix: np.ndarray | None = None

        # keys: matches
        # values: weights assigned by the supervision engine to each match (assigning is optional)
        # the higher the weight, the more we trust the correctness of the match and the greater its individual impact should be.
        # by default, the weight is 1.
        self._match_weights: Dict[IMatch, float] = {}

        # an optional value the supervision engine can set, representing how confident the engine is that the result is of high quality
        self._score = 0.0

        self.set(**kwargs)

    def set(self, /, *, delta: np.ndarray | None = None, delta_prime: np.ndarray | None = None,
            transformation_matrix: np.ndarray | None = None, score: float | None = None):

        if delta is not None:
            assert delta.shape == (2,)
            self._delta = delta

        if delta_prime is not None:
            assert delta_prime.shape == (2,)
            self._delta_prime = delta_prime

        if transformation_matrix is not None:
            assert transformation_matrix.shape == (2, 2)
            self._transformation_matrix = transformation_matrix

        if score is not None:
            self._score = score

    def set_match_weight(self, match: IMatch, weight: float, /):
        assert weight >= 0
        self._match_weights[match] = weight

    def get_match_weight(self, match: IMatch, /) -> float:

        if match in self._match_weights:
            return self._match_weights[match]

        return 1.0

    @property
    def template(self) -> ITemplate:
        raise ErrOperationNotSupported(
            "while trying to access the template from a public API's instance of a supervision result.",
            "This operation is illegal."
        )

    @property
    def matching_result(self) -> IMatchingResult:
        return self._matching_result

    def get_score(self) -> float:
        assert self._score >= 0.0
        return self._score

    @property
    def delta(self) -> np.ndarray:

        if self._delta is None:
            raise ErrObjectNotInitialized(
                "while trying to access the 'delta' parameter of the supervision result instance.",
                "This parameter has not been set."
            )

        return self._delta.copy()

    @property
    def delta_prime(self) -> np.ndarray:

        if self._delta_prime is None:
            raise ErrObjectNotInitialized(
                "while trying to access the 'delta_prime' parameter of the supervision result instance.",
                "This parameter has not been set."
            )

        return self._delta_prime.copy()

    @property
    def transformation_matrix(self) -> np.ndarray:

        if self._transformation_matrix is None:
            raise ErrObjectNotInitialized(
                "while trying to access the 'transformation_matrix' parameter of the supervision result instance.",
                "This parameter has not been set."
            )

        return self._transformation_matrix.copy()

    def translate(self, template_point: np.ndarray, /) -> np.ndarray:
        """
        Translates the given template point into a target point. That is, given a position in the template's coordinate system, this function
        outputs the corresponding position in the target image's coordinate system, according to the affine transformation model.
        """
        assert template_point.shape == (2,)
        return self._transformation_matrix @ (template_point - self._delta) + self._delta_prime

    def get_weighted_mse(self, /) -> float:
        error = 0.0
        singificant_match_count = 0

        for match in self._matching_result.get_all_matches():

            match_weight = self.get_match_weight(match)

            if match_weight < sys.float_info.epsilon:
                continue

            singificant_match_count += 1

            s = match.get_original_template_point()

            # calculate prediction
            p = self.translate(s)

            # calculate destination
            d = match.target_point

            current_error = p - d
            current_error_value = np.dot(current_error, current_error)

            error += current_error_value * match_weight

        return error / singificant_match_count

    def warp_feature(self, feature: IFeature, target: np.ndarray, /) -> np.ndarray:

        target_tl = self.translate(feature.top_left)
        target_tr = self.translate(feature.top_right)
        target_bl = self.translate(feature.bottom_left)
        target_br = self.translate(feature.bottom_right)

        dest_tl = np.array([0, 0], dtype=np.float64)
        dest_tr = np.array([feature.w, 0], dtype=np.float64)
        dest_br = np.array([feature.w, feature.h], dtype=np.float64)
        dest_bl = np.array([0, feature.h], dtype=np.float64)

        source_points = [target_tl, target_tr, target_br, target_bl]
        destination_points = [dest_tl, dest_tr, dest_br, dest_bl]

        homography = cv2.getPerspectiveTransform(np.float32(source_points), np.float32(destination_points))

        return cv2.warpPerspective(
            target,
            np.float32(homography),
            (feature.w, feature.h),
            flags=cv2.INTER_LINEAR
        )