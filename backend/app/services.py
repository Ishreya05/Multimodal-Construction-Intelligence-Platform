import base64, json, re, statistics
from typing import Any
import httpx
from .config import settings
from .schemas import AnalysisResponse, Finding, ProjectInput, EstimateResponse, MaterialLine, ScheduleResponse, ScheduleTask, ValuationRequest, ValuationResponse, DesignBriefRequest, DesignBriefResponse

DISCLAIMER = "Prototype decision support only. Not a professional inspection, structural diagnosis, certified estimate, code review, or formal valuation. Verify with qualified local professionals."

def _safe_json(text: str) -> dict[str, Any]:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start: raise ValueError("AI provider returned no JSON object")
    return json.loads(text[start:end+1])

async def _ask_vision(images: list[tuple[str, bytes]], prompt: str) -> dict[str, Any] | None:
    if not settings.ai_api_key or not images: return None
    content: list[dict[str, Any]] = [{"type":"text", "text":prompt}]
    for mime, raw in images[:5]:
        b64 = base64.b64encode(raw).decode("ascii")
        content.append({"type":"image_url", "image_url":{"url":f"data:{mime};base64,{b64}"}})
    body = {"model":settings.ai_model,"temperature":0.1,"messages":[{"role":"system","content":"You assist with construction project decision support. Never claim certification or certainty. Treat images as limited evidence, distinguish visible evidence from inference, recommend a qualified professional for potentially serious issues. Return only JSON matching the requested schema."},{"role":"user","content":content}],"response_format":{"type":"json_object"}}
    url = settings.ai_base_url.rstrip("/") + "/chat/completions"
    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        response = await client.post(url, headers={"Authorization":f"Bearer {settings.ai_api_key}","Content-Type":"application/json"}, json=body)
        response.raise_for_status()
        data = response.json()
    return _safe_json(data["choices"][0]["message"]["content"])

def demo_analysis(text: str, project: ProjectInput, image_count: int) -> AnalysisResponse:
    lowered = text.lower()
    findings = []
    if any(w in lowered for w in ["crack", "裂", "fissure"]):
        findings.append(Finding(category="crack", title="Crack mentioned in project description", severity="unknown", confidence=0.35, evidence="The text description mentions a crack; no visual diagnosis is available in demo mode.", possible_causes=["Shrinkage", "Thermal movement", "Settlement", "Material or workmanship issues"], recommended_actions=["Record crack location, width, length, and whether it is changing", "Photograph with a scale and date", "Ask a qualified structural professional to assess it; treat widening, diagonal, or load-bearing-element cracks as urgent"]))
    if any(w in lowered for w in ["height", "scaffold", "scaffolding", "edge", "fall"]):
        findings.append(Finding(category="hazard", title="Potential fall hazard needs site verification", severity="high", confidence=0.4, evidence="The text includes work-at-height or edge-related terms; actual site conditions are unverified.", possible_causes=["Unprotected edges", "Incomplete access platform"], recommended_actions=["Restrict access to exposed edges until inspected", "Verify guardrails, fall protection, scaffold tags, and safe access with the site safety lead"]))
    if any(w in lowered for w in ["helmet", "ppe", "without gloves", "no safety"]):
        findings.append(Finding(category="ppe", title="PPE compliance should be checked", severity="moderate", confidence=0.4, evidence="The description mentions PPE or missing safety equipment; image inspection is not performed in demo mode.", possible_causes=["Missing or unsuitable PPE", "Inconsistent site enforcement"], recommended_actions=["Check task-specific PPE requirements and fit", "Pause the affected task if required protection is missing"]))
    if not findings:
        findings.append(Finding(category="observation", title="No specific issue identified from text alone", severity="unknown", confidence=0.15, evidence=f"Demo mode received {image_count} image(s), but does not run computer vision. Text: {text[:300] or 'No description provided.'}", possible_causes=[], recommended_actions=["Use the AI provider configuration for image interpretation", "Have a competent person inspect the site in person"]))
    return AnalysisResponse(mode="demo", disclaimer=DISCLAIMER+" Demo mode does not inspect image pixels.", summary="Demo-mode review generated from text keywords only; uploaded images were not analyzed.", findings=findings, immediate_actions=["Do not use this demo output to declare an area safe", "Escalate any suspected imminent danger to the site supervisor and follow the site emergency procedure"], missing_information=["Exact site location and context", "Image evidence interpreted by a vision-capable model", "Dimensions, material, age, and change history where cracks are involved"])

async def analyze(text: str, project: ProjectInput, images: list[tuple[str, bytes]]) -> AnalysisResponse:
    prompt = "Analyze the construction context and images cautiously. Return JSON with keys mode, disclaimer, summary, findings, immediate_actions, missing_information. Each finding: category (hazard/ppe/crack/observation), title, severity (low/moderate/high/critical/unknown), confidence 0..1, evidence, possible_causes (array), recommended_actions (array). Never infer unseen facts. If evidence is insufficient say unknown. Context: " + json.dumps({"description":text,"project":project.model_dump()})
    if settings.ai_api_key and images:
        try:
            raw = await _ask_vision(images, prompt)
            raw["mode"] = "ai"; raw["disclaimer"] = DISCLAIMER + " AI image interpretations can be wrong."
            return AnalysisResponse.model_validate(raw)
        except Exception as exc:
            # Do not leak provider keys or response bodies. Fall back transparently.
            result = demo_analysis(text, project, len(images))
            result.summary = "AI analysis was unavailable or returned invalid output; showing text-only demo fallback."
            result.disclaimer += " Configure and verify the AI provider if image analysis is required."
            return result
    return demo_analysis(text, project, len(images))

# Editable illustrative rates in INR. Replace with local supplier/contractor quotes.
RATES = {"cement_bags_per_sqft": 0.40, "steel_kg_per_sqft": 3.5, "sand_cuft_per_sqft": 1.8, "aggregate_cuft_per_sqft": 1.2, "brick_units_per_sqft": 8.0, "labour_per_sqft": 450.0}
UNIT_RATES = {"cement bag": 420.0, "steel kg": 68.0, "sand cu ft": 65.0, "aggregate cu ft": 55.0, "brick unit": 10.0, "labour sq ft": 450.0}
def estimate(project: ProjectInput) -> EstimateResponse:
    quality_factor = {"economy":0.88,"standard":1.0,"premium":1.25}[project.quality]
    specs = [("Cement", project.area_sqft*RATES["cement_bags_per_sqft"], "bags", UNIT_RATES["cement bag"]),("Reinforcement steel", project.area_sqft*RATES["steel_kg_per_sqft"], "kg", UNIT_RATES["steel kg"]),("Sand", project.area_sqft*RATES["sand_cuft_per_sqft"], "cu ft", UNIT_RATES["sand cu ft"]),("Aggregate", project.area_sqft*RATES["aggregate_cuft_per_sqft"], "cu ft", UNIT_RATES["aggregate cu ft"]),("Bricks/blocks", project.area_sqft*RATES["brick_units_per_sqft"], "units", UNIT_RATES["brick unit"]),("Labour allowance", project.area_sqft, "sq ft", UNIT_RATES["labour sq ft"])]
    items = [MaterialLine(material=n, quantity=round(q,2), unit=u, rate=round(r*quality_factor,2), amount=round(q*r*quality_factor,2)) for n,q,u,r in specs]
    subtotal=sum(x.amount for x in items); contingency=round(subtotal*0.10,2)
    return EstimateResponse(disclaimer=DISCLAIMER+" Quantities are rough thumb-rule allowances and omit design-specific items, taxes, permits, services, and local market variation.",area_sqft=project.area_sqft,items=items,subtotal=round(subtotal,2),contingency=contingency,total=round(subtotal+contingency,2))

def schedule(project: ProjectInput) -> ScheduleResponse:
    factor = max(1, round(project.area_sqft/1000)) * (1 + max(0, project.floors-1)*0.35)
    base=[("Planning, surveys and approvals",7,None),("Site preparation and excavation",7,"Planning, surveys and approvals"),("Foundation and plinth",14,"Site preparation and excavation"),("Structural frame",21,"Foundation and plinth"),("Roofing and waterproofing",10,"Structural frame"),("Electrical and plumbing rough-in",12,"Structural frame"),("Masonry and partitions",18,"Structural frame"),("Plastering and screed",12,"Masonry and partitions"),("Finishes, fixtures and painting",21,"Plastering and screed"),("Testing, snagging and handover",7,"Finishes, fixtures and painting")]
    tasks=[]; day=1; ends={}
    for name,duration,dep in base:
        duration=max(1,round(duration*factor)); start=(ends.get(dep,0)+1) if dep else day
        # Parallel trades start after structural prerequisites; simple planning approximation.
        if name=="Electrical and plumbing rough-in": start=ends.get("Structural frame",0)+1
        end=start+duration-1; ends[name]=end; tasks.append(ScheduleTask(task=name,duration_days=duration,start_day=start,end_day=end,dependency=dep))
    total=max(t.end_day for t in tasks)
    return ScheduleResponse(disclaimer=DISCLAIMER+" Illustrative high-level schedule only; sequencing and duration require contractor and site review.",total_duration_days=total,tasks=tasks)

def valuation(req: ValuationRequest) -> ValuationResponse:
    if req.comparable_values:
        rate=statistics.median(req.comparable_values)/req.area_sqft if max(req.comparable_values)>req.area_sqft*100 else statistics.median(req.comparable_values)
        method="Median of user-supplied comparable values/rates; confirm comparable units and area basis."
    elif req.rate_per_sqft:
        rate=req.rate_per_sqft; method="User-supplied rate per square foot."
    else:
        rate=settings.default_rate_per_sqft; method="Configurable default rate; not live market data."
    condition_factor={"poor":0.75,"fair":0.88,"good":1.0,"excellent":1.08}[req.condition]
    value=req.area_sqft*rate*condition_factor
    return ValuationResponse(disclaimer=DISCLAIMER+" This is not an appraisal and does not use live transaction data. Confirm whether comparable values are total prices or per-sq-ft rates.",location=req.location,area_sqft=req.area_sqft,rate_per_sqft=round(rate*condition_factor,2),estimated_value=round(value,2),low_estimate=round(value*.9,2),high_estimate=round(value*1.1,2),method=method,currency="INR")

def design_brief(req: DesignBriefRequest) -> DesignBriefResponse:
    rooms = req.rooms or ["living area", "kitchen", "bedrooms", "bathrooms"]
    prompt=(f"Create a photorealistic architectural concept image of a {req.style} {req.project_type}, approximately {req.area_sqft:g} sq ft across {req.floors} floor(s). " f"Include a clear entry, daylight-conscious openings, climate-responsive shading, realistic Indian context and materials, and these spaces: {', '.join(rooms)}. " f"Requirements: {req.requirements or 'Prioritize circulation, ventilation, accessibility, and efficient space planning.'} " "Concept visualization only; do not imply code approval or construction-ready drawings.")
    return DesignBriefResponse(disclaimer=DISCLAIMER+" This output is a concept brief/prompt, not a rendered image, CAD drawing, or construction document.",concept_title=f"{req.style} {req.project_type} concept",brief=f"Develop a {req.style.lower()} concept for a {req.area_sqft:g} sq ft project with {req.floors} floor(s). Organize spaces for practical circulation, daylight, cross-ventilation, maintainability, and local climate. Verify setbacks, structure, accessibility, fire safety, and applicable codes with licensed professionals.",room_program=rooms,visualization_prompt=prompt,professional_checks=["Licensed architect to verify layout, local bylaws and setbacks","Structural engineer to design foundations and framing","MEP professionals to review electrical, plumbing and ventilation","Confirm fire safety, accessibility, energy and permit requirements"])
