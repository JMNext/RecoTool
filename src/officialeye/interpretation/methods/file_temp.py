import tempfile
from typing import Dict

# noinspection PyPackageRequirements
import cv2

from officialeye.context.context import Context
from officialeye.interpretation.method import InterpretationMethod
from officialeye.interpretation.serializable import Serializable


class FileTempMethod(InterpretationMethod):

    METHOD_ID = "file_temp"

    def __init__(self, context: Context, config_dict: Dict[str, any]):
        super().__init__(context, FileTempMethod.METHOD_ID, config_dict)

        self._format = self.get_config().get("format", default="png")

    def interpret(self, feature_img: cv2.Mat, feature_id: str, /) -> Serializable:

        with tempfile.NamedTemporaryFile(prefix="officialeye_", suffix=f".{self._format}", delete=False) as fp:
            fp.close()

        cv2.imwrite(fp.name, feature_img)

        return fp.name