from typing_extensions import List, Dict, TypedDict
from langgraph.graph import StateGraph, END , START
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
import os

from dotenv import load_dotenv
load_dotenv()

# STATE
class node1state(TypedDict,total=False):
    repo: str
    files: List[Dict[str, str]]
    readme_imp: List[str]

# LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API"),
    temperature=0
)

parser = JsonOutputParser()
prompt = ChatPromptTemplate.from_template("""
You are a repository analyzer that identifies ONLY the most essential files for README documentation.


CRITICAL FILES TO INCLUDE:

**Dependency Management (ALWAYS include if present):**
- package.json, yarn.lock, pnpm-lock.yaml, requirement.txt, requirements.txt
- Pipfile, Pipfile.lock, poetry.lock, pyproject.toml
- Gemfile, Gemfile.lock, go.mod, go.sum
- pom.xml, build.gradle, build.gradle.kts
- Cargo.toml, Cargo.lock, composer.json, composer.lock

**Containerization (ALWAYS include if present):**
- Dockerfile (anywhere), docker-compose.yml, docker.compose.yml, compose.yml, .dockerignore

**Environment/Configuration (root or one level deep only):**
- .env.example, .env.sample, env.example
- config.yml, config.yaml (root level only)
- Makefile, CMakeLists.txt, setup.py, setup.cfg

**CI/CD (main workflow files only):**
- .github/workflows/main.yml, .github/workflows/ci.yml, .github/workflows/deploy.yml
- .gitlab-ci.yml, Jenkinsfile

STRICT EXCLUSIONS - NEVER INCLUDE:

**Source Code & Deep Nested Files:**
- Any .py, .js, .ts, .tsx, .jsx files inside: src/, app/, components/, pages/, lib/, utils/, core/
- Files 3+ levels deep (e.g., backend/app/core/config.py) UNLESS it's Dockerfile or docker-compose
- Example excludes: backend/app/Agent/node1.py, frontend/src/components/ui/button.tsx
- never include package-lock.json

**Tests & Documentation:**
- test*.*, *test.*, *.spec.*, *.test.*, tests.py, anything in __tests__/ or tests/
- README.md, LICENSE, CONTRIBUTING.md, docs/

**Build Outputs & IDE:**
- node_modules/, dist/, build/, __pycache__/, .venv/, venv/, target/, out/
- .gitignore, .git/, .vscode/, .idea/, *.swp, .DS_Store

**UI & Config Components:**
- Anything in: components/ui/, pages/, public/
- Deep config files: backend/app/core/config.py (too nested)
- TypeScript configs: tsconfig.*.json, vite.config.ts, eslint.config.js
- Component configs: components.json

AVAILABLE FILES:
{file_paths}

INSTRUCTIONS:
1. Scan the file paths provided above
2. Select ONLY files matching critical criteria from the EXACT paths given
3. Return paths EXACTLY as they appear (e.g., "backend/requirement.txt" not "requirements.txt")
4. Maximum 8 files for single service, 12 for multi-service projects
5. Prioritize: dependencies → containers → environment files

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON
- Use EXACT paths from the input
- NO explanations, NO markdown, NO extra text
- Just the JSON object

Return format:
{{
  "readme_imp": [
    "backend/requirement.txt",
    "backend/Dockerfile",
    "docker.compose.yml",
    "frontend/package.json"
  ]
}}

Now analyze and return ONLY the JSON object.
""")




# def functions:
def judge_files(state: node1state) -> node1state:
    file_paths = [f["path"] for f in state["files"]]

    chain = prompt | llm | parser
    result = chain.invoke({"file_paths": file_paths})

    state["readme_imp"] = result.get("readme_imp", [])
    return state


def build_judge_graph():
    graph = StateGraph(node1state)

    graph.add_node("judge_files", judge_files)

    graph.add_edge(START, "judge_files")
    graph.add_edge("judge_files", END)


    return graph.compile()