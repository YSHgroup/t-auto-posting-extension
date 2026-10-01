from pydantic import BaseModel, Field


class SuitabilityResult(BaseModel):
    status: str
    reason: str
    confidence: float = Field(ge=0, le=1)


class RiskItem(BaseModel):
    text: str
    source: str  # observed | inference | recommendation


class GroupAnalysisAIOutput(BaseModel):
    summary: str = ""
    activities: list[str] = Field(default_factory=list)
    member_types: list[str] = Field(default_factory=list)
    partnership: SuitabilityResult
    job: SuitabilityResult
    recommended_post_style: list[str] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)


class PostRecommendationItem(BaseModel):
    post_id: str
    reason: str
    confidence: float = Field(ge=0, le=1)


class PostRecommendationAIOutput(BaseModel):
    recommendations: list[PostRecommendationItem]


class OpportunityCandidate(BaseModel):
    user_id: str
    username: str
    category: str
    evidence: str
    evidence_level: str
    confidence: float = Field(ge=0, le=1)


class OpportunityAIOutput(BaseModel):
    investment: list[OpportunityCandidate] = Field(default_factory=list)
    partnership: list[OpportunityCandidate] = Field(default_factory=list)
