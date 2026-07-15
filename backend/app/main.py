from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.Agent.readme_workflow import generate_readme_graph
# from app.Agent.repository_analyzer import build_judge_graph
# from app.gitfetch.filerepo import file_system
# from app.gitfetch.git import fetch_github_repo
# from app.gitfetch.storingdata import storingdata

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# judge_graph = build_judge_graph()
readme_graph = generate_readme_graph()


class RepoRequest(BaseModel):
    repo_url: str


class ReviewRequest(BaseModel):
    session_id: str
    satisfied: bool
    feedback: str = Field(default="", max_length=4000)


def config(session_id: str):
    return {"configurable": {"thread_id": session_id}}


def review_response(result: dict, session_id: str) -> dict:
    interrupts = result.get("__interrupt__", [])
    if interrupts:
        review = interrupts[0].value
        return {
            "status": "awaiting_review",
            "session_id": session_id,
            "readme": review["readme"],
            "revision": review["revision"],
            "message": review["message"],
        }
    return {
        "status": "completed",
        "session_id": session_id,
        "readme": result.get("readme", ""),
        "revision": result.get("revision", 1),
    }


@app.get("/")
def root():
    return {"message": "DocPilot API"}


@app.post("/fetchrepo")
def fetch_repo(data: RepoRequest):
    try:
        # fetch_github_repo(data.repo_url)
        # repo = file_system(data.repo_url)
        # judged_repo = judge_graph.invoke(repo)
        # raw_data = storingdata(judged_repo)
        raw_data = {
            "raw_data": [
                {
                    "path": "backend/requirement.txt",
                    "content": "fastapi\nuvicorn\nrequests\npython-dotenv\nPyGithub\nlanggraph\nlangchain\nlangchain-groq\npydantic\nredis\n",
                }
            ]
        }

        session_id = str(uuid4())
        result = readme_graph.invoke(raw_data, config(session_id))
        return review_response(result, session_id)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/review")
def review_readme(data: ReviewRequest):
    try:
        result = readme_graph.invoke(
            Command(resume={"satisfied": data.satisfied, "feedback": data.feedback}),
            config(data.session_id),
        )
        return review_response(result, data.session_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail="Review session was not found or could not be resumed") from error
