from __future__ import annotations

from concurrent.futures import Future
from typing import List, TYPE_CHECKING

import cv2

from officialeye._api.analysis_result import AnalysisResult
from officialeye._api.image import Image
# noinspection PyProtectedMember
from officialeye._internal.api import template_load, template_analyze
# noinspection PyProtectedMember
from officialeye._internal.template.template_data import TemplateData
from officialeye._api.template.region import Keypoint, Feature


if TYPE_CHECKING:
    from officialeye._api.context import Context


class Template:

    def __init__(self, context: Context, /, *, path: str):
        self._context = context
        self._path = path

        self._data: TemplateData | None = None

    def load(self):
        """
        Loads the template into memory for further processing.

        If you prefer lazy-evaluation, do not call this method.
        Instead, run the desired operations with the template, and the necessary resources will be loaded on-the-fly.
        Use this method only if you really want to preload the template.
        """

        if self._data is not None:
            # data has already been loaded, nothing to do
            return

        # noinspection PyProtectedMember
        future = self._context._submit_task(template_load, "Loading template...", self._path)

        self._data = future.result()

        assert self._data is not None

    def analyze_async(self, /, *, target: Image, interpretation_target: Image | None = None) -> Future:
        # noinspection PyProtectedMember
        return self._context._submit_task(
            template_analyze,
            "Running analysis...",
            self._path,
            target_path=target._path,
            interpretation_target_path=None if interpretation_target is None else interpretation_target._path
        )

    def analyze(self, /, **kwargs) -> AnalysisResult:
        future = self.analyze_async(**kwargs)
        return future.result()

    def get_image(self) -> cv2.Mat:
        self.load()
        return cv2.imread(self._data.source, cv2.IMREAD_COLOR)

    def get_mutated_image(self) -> cv2.Mat:
        img = self.get_image()
        return self._data.apply_source_mutators(img)

    @property
    def identifier(self) -> str:
        self.load()
        return self._data.identifier

    @property
    def name(self) -> str:
        self.load()
        return self._data.name

    @property
    def width(self) -> int:
        self.load()
        return self._data.width

    @property
    def height(self) -> int:
        self.load()
        return self._data.height

    @property
    def keypoints(self) -> List[Keypoint]:
        self.load()
        return self._data.keypoints

    @property
    def features(self) -> List[Feature]:
        self.load()
        return self._data.features
