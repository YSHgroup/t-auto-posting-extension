import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def parse_with_retry(
    raw_json: str,
    model: type[T],
    fix_callback,
) -> T:
    try:
        data = json.loads(raw_json)
        return model.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as first_err:
        logger.warning("AI validation failed, attempting correction: %s", first_err)
        corrected = await fix_callback(raw_json, str(first_err))
        try:
            data = json.loads(corrected)
            return model.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as second_err:
            raise ValueError(f"AI structured output invalid: {second_err}") from second_err
