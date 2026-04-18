from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.gitfetch.git import fetch_github_repo
from app.gitfetch.filerepo import file_system
from app.Agent.node1 import build_judge_graph, node1state
from app.gitfetch.storingdata import storingdata
from app.Agent.generation_graph import generate_readme_graph
from pydantic import BaseModel


import json 
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

graph = build_judge_graph()
readme_gen = generate_readme_graph()


class RepoRequest(BaseModel):
    repo_url: str

@app.get("/")
def root():
    return {"message": "Hello, World!"}



@app.post("/fetchrepo")
def fetch_repo(data: RepoRequest):
    try:


        # # repo = fetch_github_repo(repo_url)
        # print("dont #1")
        # payload = file_system(repo_url)
        # print("dont #2")
        # result = graph.invoke(payload)
        # print("dont #3")
        # data = {
        #     "repo": result["repo"],
        #     "readme_imp": result["readme_imp"]
        # }
        # # print("dont #4")
        # raw_data = storingdata(data)
        # # print("dont #5")


        data = {
            "raw_data":[
                {
                  "path": "backend/requirement.txt",
                  "content": "fastapi\nuvicorn\nrequests\npython-dotenv\nPyGithub\nlanggraph\nlangchain\nlangchain-groq  \npydantic\nredis\n"
                },
                {
                  "path": "backend/Dockerfile",
                  "content": "FROM python:3.11-slim\n\nWORKDIR /app\n\nCOPY requirement.txt .\n\nRUN pip install --no-cache-dir -r requirement.txt\n\nCOPY . .\n\nEXPOSE 8081\n\nCMD [\"uvicorn\",\"app.main:app\",\"--host\", \"0.0.0.0\", \"--port\",\"8081\"]"
                },
                {
                  "path": "docker-compose.yml",
                  "content": "#docker-compose.yml\nversion: \"3.9\"\n\nservices:\n  backend:\n    build: ./backend\n    container_name: doc-agent\n    ports:\n      - \"8081:8081\"\n    env_file:\n      - ./backend/app/.env\n    depends_on:\n      - redis\n    \n\n  redis:\n    image: redis:7-alpine\n    container_name: redis-agent\n    ports:\n      - \"6379:6379\"\n    env_file:\n      - ./backend/app/.env\n    volumes:\n      - redis_data:/data\n\n\nvolumes:\n  redis_data:"
                },
                {
                  "path": "frontend/package.json",
                  "content": "{\n  \"name\": \"frontend\",\n  \"private\": true,\n  \"version\": \"0.0.0\",\n  \"type\": \"module\",\n  \"scripts\": {\n    \"dev\": \"vite\",\n    \"build\": \"tsc -b && vite build\",\n    \"lint\": \"eslint .\",\n    \"preview\": \"vite preview\"\n  },\n  \"dependencies\": {\n    \"@radix-ui/react-dropdown-menu\": \"^2.1.16\",\n    \"@radix-ui/react-slot\": \"^1.2.4\",\n    \"@tailwindcss/vite\": \"^4.1.18\",\n    \"class-variance-authority\": \"^0.7.1\",\n    \"clsx\": \"^2.1.1\",\n    \"lucide-react\": \"^0.562.0\",\n    \"react\": \"^19.2.0\",\n    \"react-dom\": \"^19.2.0\",\n    \"react-router\": \"^7.12.0\",\n    \"tailwind-merge\": \"^3.4.0\",\n    \"tailwindcss\": \"^4.1.18\"\n  },\n  \"devDependencies\": {\n    \"@eslint/js\": \"^9.39.1\",\n    \"@types/node\": \"^24.10.8\",\n    \"@types/react\": \"^19.2.5\",\n    \"@types/react-dom\": \"^19.2.3\",\n    \"@vitejs/plugin-react-swc\": \"^4.2.2\",\n    \"eslint\": \"^9.39.1\",\n    \"eslint-plugin-react-hooks\": \"^7.0.1\",\n    \"eslint-plugin-react-refresh\": \"^0.4.24\",\n    \"globals\": \"^16.5.0\",\n    \"tw-animate-css\": \"^1.4.0\",\n    \"typescript\": \"~5.9.3\",\n    \"typescript-eslint\": \"^8.46.4\",\n    \"vite\": \"^7.2.4\"\n  }\n}\n"
                }
            ]
        }

      

        try:
            result_1= readme_gen.invoke(data)
            reamde_fledge_data = {
                "readme": result_1["readme"]
            }
            
            return reamde_fledge_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/readtestfile")
def read_testfile():
    print("check this testing ")
    raw_file = reading_raw_data()
    print(type(raw_file))
    return raw_file
