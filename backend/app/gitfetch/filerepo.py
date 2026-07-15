from github import Github
from urllib.parse import urlparse
from app.Agent.readfile import read_file
from dotenv import load_dotenv
from app.core.redis_cache import set_cache,get_cache
import json
import os 

load_dotenv()
GITHUBTOKEN = os.getenv('GITHUBTOKEN')

if not GITHUBTOKEN:
    raise ValueError("GITHUB_TOKEN not found in environment")

g = Github(GITHUBTOKEN)


def traverse_repo(repo,metadata, path=""):
    contents = repo.get_contents(path)
    for x in contents:
        metadata["files"].append({
            "path": x.path,
            "name": x.name
        })
        if x.type == "dir":
            traverse_repo(repo, metadata, x.path)


    

def file_system(repo_url: str):

    key = f"repourl:{repo_url}"
    cache_data = get_cache(key)
    if cache_data:
        print("returning the data from caches")
        return cache_data


    path = urlparse(repo_url).path.strip("/").split("/")
    user = path[0]
    repo_name = path[1]

    full_repo_name = f"{user}/{repo_name}"

    repo = g.get_repo(full_repo_name)
    
    metadata={"files":[]}

    traverse_repo(repo,metadata)
    
    metadata.update({"repo": repo.full_name})
    set_cache(key,metadata)
    return metadata

