import os
from threading import Lock
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.Agent.readme_workflow import generate_readme_graph
# from app.Agent.repository_analyzer import build_judge_graph
# from app.gitfetch.filerepo import file_system
# from app.gitfetch.git import fetch_github_repo
# from app.gitfetch.storingdata import storingdata

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
SESSION_SECRET = os.getenv("SESSION_SECRET")
SESSION_COOKIE = "docpilot_session"

if not SESSION_SECRET:
    # A persistent value must be supplied in production so sessions survive restarts.
    SESSION_SECRET = "development-only-change-me"

users: dict[str, dict] = {}
github_users: dict[str, str] = {}
users_lock = Lock()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
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


def github_configured() -> None:
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")


def current_user(request: Request) -> dict:
    """Return the signed-in user from the server-side session cookie."""
    from itsdangerous import BadSignature, URLSafeTimedSerializer

    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Sign in with GitHub to continue")
    try:
        user_id = URLSafeTimedSerializer(SESSION_SECRET, salt="docpilot-session").loads(
            token, max_age=60 * 60 * 24 * 7
        )
    except BadSignature as error:
        raise HTTPException(status_code=401, detail="Your session has expired") from error

    with users_lock:
        user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Your local session has expired")
    return user


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


@app.get("/auth/github")
def github_login(request: Request):
    github_configured()
    from itsdangerous import URLSafeTimedSerializer

    state = URLSafeTimedSerializer(SESSION_SECRET, salt="docpilot-oauth-state").dumps("github")
    callback_url = str(request.url_for("github_callback"))
    authorization_url = "https://github.com/login/oauth/authorize?" + urlencode(
        {"client_id": GITHUB_CLIENT_ID, "redirect_uri": callback_url, "scope": "read:user user:email", "state": state}
    )
    return RedirectResponse(authorization_url, status_code=302)


@app.get("/auth/github/callback", name="github_callback")
async def github_callback(code: str, state: str):
    github_configured()
    from itsdangerous import BadSignature, URLSafeTimedSerializer

    try:
        URLSafeTimedSerializer(SESSION_SECRET, salt="docpilot-oauth-state").loads(state, max_age=600)
    except BadSignature as error:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state") from error

    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET, "code": code},
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="GitHub did not grant access")
        profile_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
        profile_response.raise_for_status()
        profile = profile_response.json()

    github_id = str(profile["id"])
    with users_lock:
        user_id = github_users.get(github_id, str(uuid4()))
        user = {
            "id": user_id,
            "github_id": github_id,
            "login": profile["login"],
            "name": profile.get("name"),
            "avatar_url": profile.get("avatar_url"),
            "email": profile.get("email"),
        }
        users[user_id] = user
        github_users[github_id] = user_id

    session = URLSafeTimedSerializer(SESSION_SECRET, salt="docpilot-session").dumps(user_id)
    response = RedirectResponse(FRONTEND_URL, status_code=302)
    response.set_cookie(SESSION_COOKIE, session, max_age=60 * 60 * 24 * 7, httponly=True, samesite="lax")
    return response


@app.get("/auth/me")
def me(user: dict = Depends(current_user)):
    return user


@app.post("/auth/logout")
def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.post("/fetchrepo")
def fetch_repo(data: RepoRequest, _user: dict = Depends(current_user)):
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
def review_readme(data: ReviewRequest, _user: dict = Depends(current_user)):
    try:
        result = readme_graph.invoke(
            Command(resume={"satisfied": data.satisfied, "feedback": data.feedback}),
            config(data.session_id),
        )
        return review_response(result, data.session_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail="Review session was not found or could not be resumed") from error
