from typing_extensions import Dict, List, TypedDict
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API"),
    temperature=0,
)


class ReadmeState(TypedDict, total=False):
    raw_data: List[Dict[str, str]]
    readme: str
    feedback: str
    satisfied: bool
    revision: int


parser = JsonOutputParser()
prompt = ChatPromptTemplate.from_template("""
You are a technical documentation expert. Create or improve a README from the project files.

Project Files:
{files}

Existing README:
{existing_readme}

Previous reviewer feedback:
{feedback}

Create a useful, accurate README with these sections when the files support them:
- Quick Start
- Tech Stack
- Project Structure
- Configuration
- Running the Project
- Key Dependencies
- Contributing
- Learning Roadmap

If an existing README is provided, use it as the baseline. Improve its clarity, completeness, structure, and accuracy while preserving useful project-specific details. Use only details supported by the existing README or project files. If reviewer feedback is present, apply it without inventing project details.

Return only valid JSON:
{{
  "readme": "complete markdown content"
}}
""")


def generate_readme(state: ReadmeState) -> ReadmeState:
    raw_data = state.get("raw_data", [])
    readme_files = [
        file for file in raw_data
        if file["path"].rsplit("/", 1)[-1].lower() == "readme.md" and file.get("content")
    ]
    files = "\n\n".join(
        f"FILE: {file['path']}\nCONTENT:\n{file['content']}"
        for file in raw_data
        if file.get("content") and file not in readme_files
    )
    result = (prompt | llm | parser).invoke({
        "files": files,
        "existing_readme": "\n\n".join(file["content"] for file in readme_files) or "No existing README was provided.",
        "feedback": state.get("feedback") or "No feedback yet.",
    })
    return {
        "readme": result.get("readme", ""),
        "revision": state.get("revision", 0) + 1,
    }


def review_readme(state: ReadmeState) -> ReadmeState:
    response = interrupt({
        "type": "readme_review",
        "message": "Is this README satisfactory? Send satisfied=true to finish, or satisfied=false with feedback to revise it.",
        "readme": state["readme"],
        "revision": state.get("revision", 1),
    })
    return {
        "satisfied": bool(response.get("satisfied")),
        "feedback": str(response.get("feedback") or ""),
    }


def next_step(state: ReadmeState) -> str:
    return "done" if state.get("satisfied") else "revise"


def generate_readme_graph():
    graph = StateGraph(ReadmeState)
    graph.add_node("generate_readme", generate_readme)
    graph.add_node("review_readme", review_readme)
    graph.add_edge(START, "generate_readme")
    graph.add_edge("generate_readme", "review_readme")
    graph.add_conditional_edges(
        "review_readme",
        next_step,
        {"done": END, "revise": "generate_readme"},
    )
    return graph.compile(checkpointer=MemorySaver())
