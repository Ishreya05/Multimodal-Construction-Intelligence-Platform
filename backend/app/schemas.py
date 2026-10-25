from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Finding(StrictModel):
    category: Literal["hazard", "ppe", "crack", "observation"]
    title: str = Field(min_length=2, max_length=140)
    severity: Literal["low", "moderate", "high", "critical", "unknown"]
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(max_length=600)
    possible_causes: list[str] = Field(default_factory=list, max_length=8)
    recommended_actions: list[str] = Field(default_factory=list, max_length=10)

class AnalysisResponse(StrictModel):
    mode: Literal["ai", "demo"]
    disclaimer: str
    summary: str
    findings: list[Finding]
    immediate_actions: list[str]
    missing_information: list[str]

class ProjectInput(StrictModel):
    project_type: str = Field(default="Residential", max_length=80)
    area_sqft: float = Field(default=1000, gt=0, le=1_000_000)
    floors: int = Field(default=1, ge=1, le=100)
    location: str = Field(default="India", max_length=160)
    quality: Literal["economy", "standard", "premium"] = "standard"
    notes: str = Field(default="", max_length=4000)

class MaterialLine(StrictModel):
    material: str
    quantity: float
    unit: str
    rate: float
    amount: float

class EstimateResponse(StrictModel):
    disclaimer: str
    area_sqft: float
    items: list[MaterialLine]
    subtotal: float
    contingency: float
    total: float
    currency: str = "INR"

class ScheduleTask(StrictModel):
    task: str
    duration_days: int = Field(ge=1)
    start_day: int = Field(ge=1)
    end_day: int = Field(ge=1)
    dependency: str | None = None

class ScheduleResponse(StrictModel):
    disclaimer: str
    total_duration_days: int
    tasks: list[ScheduleTask]

class ValuationRequest(StrictModel):
    area_sqft: float = Field(gt=0, le=10_000_000)
    location: str = Field(min_length=2, max_length=160)
    property_type: str = Field(default="Residential", max_length=80)
    condition: Literal["poor", "fair", "good", "excellent"] = "good"
    rate_per_sqft: float | None = Field(default=None, gt=0, le=10_000_000)
    comparable_values: list[float] = Field(default_factory=list, max_length=20)

class ValuationResponse(StrictModel):
    disclaimer: str
    location: str
    area_sqft: float
    rate_per_sqft: float
    estimated_value: float
    low_estimate: float
    high_estimate: float
    method: str
    currency: str = "INR"

class DesignBriefRequest(StrictModel):
    project_type: str = "Residential house"
    area_sqft: float = Field(default=1200, gt=0, le=1_000_000)
    floors: int = Field(default=1, ge=1, le=100)
    style: str = "Contemporary Indian"
    rooms: list[str] = Field(default_factory=lambda: ["living room", "kitchen", "2 bedrooms", "2 bathrooms"], max_length=30)
    requirements: str = Field(default="", max_length=4000)

class DesignBriefResponse(StrictModel):
    disclaimer: str
    concept_title: str
    brief: str
    room_program: list[str]
    visualization_prompt: str
    professional_checks: list[str]
