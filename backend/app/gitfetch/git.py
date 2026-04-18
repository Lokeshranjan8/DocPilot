from urllib.parse import urlparse
from fastapi import HTTPException
import requests
import os
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUBTOKEN')

def fetch_github_repo(repo: str):

    parsed = urlparse(repo)
    if parsed.scheme != "https":
        raise HTTPException(
           status_code=400,
           detail="Only 'https' URLs are allowed."
        )

    try:
        path = parsed.path.strip("/").split("/")
    except Exception:
        raise HTTPException(
            status_code=400, 
            detail="Invalid URL format. Please provide a valid GitHub repository URL."
        )
    
    if len(path) < 2 or not path[0] or not path[1]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid GitHub repository URL. Expected format: https://github.com/username/repository"
        )
    
    user = path[0]
    repo_name = path[1]
    
    if parsed.netloc and parsed.netloc not in ['github.com', 'www.github.com']:
        raise HTTPException(
            status_code=400,
            detail="URL must be from github.com"
        )
    
    api_url = f"https://api.github.com/repos/{user}/{repo_name}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {"exists": True}
        
        elif response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{user}/{repo_name}' not found. Please check the username and repository name."
            )
        
        elif response.status_code == 401:
            print("GitHub token authentication failed")
            raise HTTPException(
                status_code=500,
                detail="GitHub authentication failed. Please try again later."
            )
        
        elif response.status_code == 403:
            print("GitHub API rate limit exceeded or forbidden")
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Please try again later."
            )
            
    
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to GitHub. Please check your internet connection."
        )
    
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again."
        )