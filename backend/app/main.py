from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from .config import settings
from .schemas import ProjectInput, ValuationRequest, DesignBriefRequest
from .services import analyze, estimate, schedule, valuation, design_brief

app = FastAPI(title=settings.app_name, version="1.0.0", description="Construction decision-support prototype. Outputs require professional verification.")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=False, allow_methods=["GET","POST"], allow_headers=["*"])
ALLOWED = {"image/jpeg","image/png","image/webp"}

@app.get("/health")
def health():
    return {"status":"ok","service":settings.app_name,"ai_configured":bool(settings.ai_api_key)}

@app.post("/api/analyze")
async def analyze_endpoint(description: str = Form(default=""), project_json: str = Form(default='{"project_type":"Residential","area_sqft":1000,"floors":1,"location":"India","quality":"standard","notes":""}'), images: list[UploadFile] = File(default=[])):
    if len(description)>4000: raise HTTPException(413,"Description must be 4,000 characters or fewer")
    try: project=ProjectInput.model_validate_json(project_json)
    except (ValidationError, ValueError): raise HTTPException(422,"project_json is invalid; send a valid ProjectInput JSON object")
    if len(images)>5: raise HTTPException(413,"Upload at most 5 images")
    content=[]
    for image in images:
        if image.content_type not in ALLOWED: raise HTTPException(415,f"Unsupported image type for {image.filename or 'upload'}; use JPEG, PNG or WebP")
        data=await image.read(settings.max_upload_mb*1024*1024+1)
        if len(data)>settings.max_upload_mb*1024*1024: raise HTTPException(413,f"Each image must be at most {settings.max_upload_mb} MB")
        if not data: raise HTTPException(400,"An uploaded image is empty")
        content.append((image.content_type,data))
    return await analyze(description, project, content)

@app.post("/api/estimate")
def estimate_endpoint(project: ProjectInput): return estimate(project).model_dump()
@app.post("/api/schedule")
def schedule_endpoint(project: ProjectInput): return schedule(project).model_dump()
@app.post("/api/valuation")
def valuation_endpoint(request: ValuationRequest): return valuation(request).model_dump()
@app.post("/api/design-brief")
def design_endpoint(request: DesignBriefRequest): return design_brief(request).model_dump()
