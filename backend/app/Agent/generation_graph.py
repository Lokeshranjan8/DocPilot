from typing_extensions import List, Dict, TypedDict
from langgraph.graph import StateGraph, END , START
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser
from langchain_groq import ChatGroq
import os

from dotenv import load_dotenv
load_dotenv()


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API"),
    temperature=0
)

class Node2State(TypedDict, total=False):
    raw_data: List[Dict[str, str]]
    readme: str


parser = JsonOutputParser()
prompt = ChatPromptTemplate.from_template("""
You are a technical documentation expert. Analyze the project files and create a README.

Project Files:
{files}

Create a single comprehensive README with these sections:

## 🚀 Quick Start
- Prerequisites (versions required)
- Installation steps
- Environment setup
- How to run

## 🛠️ Tech Stack
- Backend technologies
- Frontend technologies  
- Infrastructure (Docker, Redis, etc.)

## 📁 Project Structure
- Key folders and purpose

## ⚙️ Configuration
- Required environment variables
- Configuration files

## 🏃 Running the Project
- Development mode commands
- Production mode commands
- Docker commands

## 📦 Key Dependencies
- Major packages and their purpose

## 🤝 Contributing
- Setup instructions
- How to submit changes
- Coding conventions

## 🎓 Learning Roadmap
- Prerequisites to learn first
- Core technologies path
- Advanced topics

CRITICAL: Return ONLY a single JSON object with this exact structure:
{{
  "readme": "your complete markdown content here as a single string"
}}

Do NOT include multiple code blocks. Do NOT add explanatory text outside the JSON.
Put ALL the markdown content inside the "readme" field as one continuous string.
""")


def readme_gen_func(state: Node2State) -> Node2State:
    files_data = state.get("raw_data", [])

    files_str = "\n\n".join(
        f"FILE: {f['path']}\nCONTENT:\n{f['content']}"
        for f in files_data
    )

    chain = prompt | llm | parser
    readme_text = chain.invoke({"files": files_str})



    state["readme"] = readme_text.get("readme", " ")
    return state




def generate_readme_graph():
    readme_gen = StateGraph(Node2State)

    readme_gen.add_node("readme_gen_func", readme_gen_func)

    readme_gen.add_edge(START, "readme_gen_func")
    readme_gen.add_edge("readme_gen_func", END)

    return readme_gen.compile()