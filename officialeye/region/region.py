import abc
from typing import Tuple

# noinspection PyPackageRequirements
import cv2


_LABEL_COLOR_DEFAULT = (0, 0, 0xff)


class TemplateRegion:
    def __init__(self, feature_dict: dict, template, /):
        self._template = template
        self.id = str(feature_dict["id"])
        self.x = int(feature_dict["x"])
        self.y = int(feature_dict["y"])
        self.w = int(feature_dict["w"])
        self.h = int(feature_dict["h"])

    @abc.abstractmethod
    def draw(self, img: cv2.Mat) -> cv2.Mat:
        raise NotImplementedError()

    def _draw(self, img: cv2.Mat, /, *, rect_color: Tuple[int, int, int], label_color=_LABEL_COLOR_DEFAULT) -> cv2.Mat:
        img = cv2.rectangle(img, (self.x, self.y), (self.x + self.w, self.y + self.h), rect_color, 4)
        label_origin = (self.x + 10, self.y + 30)
        img = cv2.putText(img, self.id, label_origin, cv2.FONT_HERSHEY_SIMPLEX, 1, label_color, 2, cv2.LINE_AA)
        return img

    def to_image(self, *, grayscale: bool = False):
        img = self._template.load_source_image()
        img_cropped = img[self.y:self.y + self.h, self.x:self.x + self.w]
        if grayscale:
            return cv2.cvtColor(img_cropped, cv2.COLOR_BGR2GRAY)
        return img_cropped