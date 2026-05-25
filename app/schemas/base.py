from typing import Annotated
import re
from pydantic import BeforeValidator


DATA_URI_PATTERN = re.compile(
    r'^data:([a-zA-Z0-9\-\+\.]+/[a-zA-Z0-9\-\+\.]+)?(;base64)?,[a-zA-Z0-9\+\s\=/]*$'
)

def validate_data_uri(v: str) -> str:
    """如果字符串以 data: 开头，则强行校验其是否符合 Data URI 规范"""
    if isinstance(v, str) and v.startswith("data:"):
        v_clean = v.replace("\n", "").replace("\r", "")
        if not DATA_URI_PATTERN.match(v_clean):
            raise ValueError("不合法的 Data URI 格式")
        return v_clean
    return v

DataUrl = Annotated[str, BeforeValidator(validate_data_uri)]