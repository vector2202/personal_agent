import json
import urllib.request
import urllib.error
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class GitHubPortfolioInput(BaseModel):
    username: str = Field(..., description="GitHub username to discover projects from.")
    topic_filter: Optional[str] = Field(default=None, description="Optional topic or tag to filter repositories.")
    limit: int = Field(default=5, ge=1, le=30, description="Maximum number of repositories to return.")

class GitHubPortfolioDiscoverer(BaseSkill):
    """
    Skill to discover and summarize a developer's GitHub projects, languages, topics, and metrics.
    Provides live career context directly into the agent.
    """

    @property
    def name(self) -> str:
        return "github_portfolio_discoverer"

    @property
    def description(self) -> str:
        return "Fetches and analyzes GitHub repositories, career portfolio, topics, and primary technologies for a developer."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return GitHubPortfolioInput

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)
        url = f"https://api.github.com/users/{data.username}/repos?sort=updated&per_page={data.limit * 2}"
        
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PersonalAgent-CareerContext/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                repos = json.loads(response.read().decode("utf-8"))

            results: List[Dict[str, Any]] = []
            for repo in repos:
                if repo.get("fork", False):
                    continue

                topics = repo.get("topics", [])
                if data.topic_filter and data.topic_filter.lower() not in [t.lower() for t in topics]:
                    continue

                results.append({
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description"),
                    "primary_language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "topics": topics,
                    "updated_at": repo.get("updated_at"),
                    "html_url": repo.get("html_url")
                })

                if len(results) >= data.limit:
                    break

            return {
                "success": True,
                "username": data.username,
                "count": len(results),
                "repositories": results
            }
        except urllib.error.HTTPError as e:
            return {"success": False, "error": f"GitHub API error {e.code}: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch GitHub portfolio: {str(e)}"}
