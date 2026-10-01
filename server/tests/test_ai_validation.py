import pytest
from pydantic import ValidationError

from app.schemas.ai_outputs import GroupAnalysisAIOutput, SuitabilityResult


def test_valid_structured_response():
    data = GroupAnalysisAIOutput(
        partnership=SuitabilityResult(status="suitable", reason="ok", confidence=0.8),
        job=SuitabilityResult(status="possibly_suitable", reason="ok", confidence=0.7),
    )
    assert data.partnership.status == "suitable"


def test_invalid_response_raises():
    with pytest.raises(ValidationError):
        GroupAnalysisAIOutput(
            partnership=SuitabilityResult(status="suitable", reason="ok", confidence=2.0),
            job=SuitabilityResult(status="x", reason="ok", confidence=0.5),
        )
