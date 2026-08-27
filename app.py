from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

load_dotenv()

from llm_client import call_model
from observability.router import choose_model
from observability.budget_guard import check_budget, BudgetExceeded
from observability.storage import get_recent_calls, get_total_cost

app = FastAPI(title="LLM Cost & Latency Observability")
templates = Jinja2Templates(directory="dashboard/templates")


class AskRequest(BaseModel):
    prompt: str


class AskResponse(BaseModel):
    model_used: str
    response: str


@app.get("/")
def index():
    return RedirectResponse(url="/dashboard")


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    if not body.prompt:
        raise HTTPException(status_code=400, detail="missing 'prompt'")

    try:
        check_budget()
    except BudgetExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))

    model = choose_model(body.prompt)
    response = call_model(prompt=body.prompt, model=model)

    return AskResponse(model_used=model, response=response.text)


@app.get("/dashboard")
def dashboard(request: Request):
    calls = get_recent_calls()
    total_cost = get_total_cost()
    return templates.TemplateResponse(
        request, "dashboard.html", {"calls": calls, "total_cost": total_cost}
    )


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
