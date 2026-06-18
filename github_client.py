"""
GitHub Toolkit for AI Agents
One function per domain, action parameter controls the operation.
"""

import base64
import os
import requests
from langchain_core.tools import tool

from dotenv import load_dotenv

load_dotenv()

class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self):
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            raise ValueError(
                "GITHUB_TOKEN environment variable is not set. "
                "Please set it in your .env file. "
            )
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def request(self, method: str, path: str, body: dict = None):
        r = requests.request(
            method,
            self.BASE + path,
            headers=self.headers,
            json=body
        )
        return r.json() if r.content else {"status": r.status_code}

    def get(self, path):
        return self.request("GET", path)
    def post(self, path, body):
        return self.request("POST", path, body)
    def put(self, path, body=None):
        return self.request("PUT", path, body)
    def patch(self, path, body):
        return self.request("PATCH", path, body)
    def delete(self, path, body=None):
        return self.request("DELETE", path, body)


def gh():
    return GitHubClient()

def find_repo(repo_name: str):

    client = gh()

    # owner/repo provided
    if "/" in repo_name:
        owner, repo = repo_name.split("/", 1)

        data = client.get(f"/repos/{owner}/{repo}")

        if isinstance(data, dict) and data.get("full_name"):
            return owner, repo

        raise Exception(f"Repository '{repo_name}' not found")

    repos = client.get("/user/repos?per_page=100&type=all")

    if not isinstance(repos, list):
        raise Exception(f"Cannot fetch repositories: {repos}")

    for r in repos:
        if r["name"].lower() == repo_name.lower():
            return (
                r["owner"]["login"],
                r["name"]
            )

    raise Exception(
        f"Repository '{repo_name}' not found"
    )

def resolve_repo(owner=None, repo=None):
    """
    Resolve owner automatically from repo name.

    Accepts:
    repo="AdeelMalik22/langchain-agent"
    repo="langchain-agent"
    """

    if not repo:
        raise Exception("Repository name is required")

    if owner:
        return owner, repo

    return find_repo(repo)
# ── Tools ────────────────────────────────────────────────────────────────────

@tool
def github_user(
    action: str,
    username: str = None,
    visibility: str = "all"
):
    """
    Manage GitHub user/account info.

    Actions:
        - profile       → Get authenticated user profile
        - details       → Get any user's public info (requires username)
        - repos         → List repos (visibility: all/public/private)
    """
    client = gh()

    if action == "profile":
        return client.get("/user")

    if action == "details":

        if not username:
            return "Error: username is required"

        return client.get(f"/users/{username}")


    if action == "repos":
        return client.get(
            f"/user/repos?per_page=100&visibility={visibility}&sort=updated"
        )

    return f"Unknown action: {action}"


@tool
def github_repository(
    action: str,
    owner: str=None,
    repo: str=None,
    path: str="",
    base: str=None,
    head: str=None
):
    """
    Manage repository info.

    Actions:
        - details       → Get repo metadata
        - contents      → List files/dirs at path (default: root)
        - tags          → List repo tags
        - compare       → Compare base...head branches or commits
    """
    client = gh()

    try:
        owner, repo = resolve_repo(owner, repo)
    except Exception as e:
        return str(e)

    if action == "details":
        data = client.get(
            f"/repos/{owner}/{repo}"
        )

        return {
            "repository": data.get("name"),
            "owner": data.get("owner", {}).get("login"),

            "description": data.get("description"),

            "visibility": data.get("visibility"),

            "language": data.get("language"),

            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),

            "open_issues": data.get("open_issues_count"),

            "default_branch": data.get("default_branch"),

            "url": data.get("html_url"),

            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),

            "license": (
                data.get("license", {}).get("name")
                if data.get("license")
                else None
            )
        }

    if action=="contents":
        return client.get(
            f"/repos/{owner}/{repo}/contents/{path}"
        )


    if action=="tags":
        return client.get(
            f"/repos/{owner}/{repo}/tags"
        )


    if action=="compare":

        if not base or not head:
            return "Error: base and head required"

        return client.get(
            f"/repos/{owner}/{repo}/compare/{base}...{head}"
        )


    return f"Unknown action: {action}"


@tool
def github_branch(
    action: str,
    owner: str = None,
    repo: str = None,
    branch: str = None,
    source: str = "main",
):
    """
    Manage branches in the authenticated user's GitHub repositories.

    The repository owner is automatically detected from GITHUB_TOKEN.
    Never ask the user for owner.

    Examples:

    Create branch:
    {
     "action": "create",
     "repo": "langchain-agent",
     "branch": "qa"
    }

    List branches:
    {
     "action": "list",
     "repo": "langchain-agent"
    }

    Delete branch:
    {
     "action": "delete",
     "repo": "langchain-agent",
     "branch": "old-feature"
    }
    """
    client = gh()

    if not repo:
        return "Error: repository name is required"

    owner, repo  = find_repo(repo)

    if action == "list":
        return client.get(f"/repos/{owner}/{repo}/branches")

    if action == "create":
        try:
            # Get the SHA of the source branch
            ref_response = client.get(f"/repos/{owner}/{repo}/git/refs/heads/{source}")
            if isinstance(ref_response, dict) and "object" in ref_response:
                sha = ref_response["object"]["sha"]
            elif isinstance(ref_response, dict) and "sha" in ref_response:
                sha = ref_response["sha"]
            else:
                return f"Error: Could not find branch '{source}'. Response: {ref_response}"

            # Create the new branch
            return client.post(f"/repos/{owner}/{repo}/git/refs", {
                "ref": f"refs/heads/{branch}",
                "sha": sha
            })
        except Exception as e:
            return f"Error creating branch '{branch}' from '{source}': {str(e)}"

    if action == "delete":
        return client.delete(f"/repos/{owner}/{repo}/git/refs/heads/{branch}")


@tool
def github_file(
    action: str,
    owner: str = None,
    repo: str = None,
    path: str = None,
    content: str = None,
    message: str = None,
    branch: str = "main",
    ref: str = "main",
):
    """
    Manage files in a repo.

    Actions:
        - read          → Get decoded file content
        - upsert        → Create or update a file (requires content, message)
        - delete        → Delete a file (requires message)
    """
    client = gh()

    try:
        owner, repo = resolve_repo(owner, repo)
    except Exception as e:
        return str(e)

    if action == "read":
        try:
            data = client.get(f"/repos/{owner}/{repo}/contents/{path}?ref={ref}")
            if isinstance(data, dict) and "content" in data:
                return base64.b64decode(data["content"]).decode()
            else:
                return f"Error: Could not read file. Response: {data}"
        except Exception as e:
            return f"Error reading file '{path}': {str(e)}"

    if action == "upsert":
        try:
            existing = requests.get(
                f"{GitHubClient.BASE}/repos/{owner}/{repo}/contents/{path}",
                headers=client.headers
            )
            payload = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch
            }
            if existing.ok:
                payload["sha"] = existing.json()["sha"]
            return client.put(f"/repos/{owner}/{repo}/contents/{path}", payload)
        except Exception as e:
            return f"Error upserting file '{path}': {str(e)}"

    if action == "delete":
        try:
            data = client.get(
                f"/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            )

            if "sha" not in data:
                return f"File not found: {path}"

            sha = data["sha"]
            return client.delete(f"/repos/{owner}/{repo}/contents/{path}", {
                "message": message,
                "sha": sha,
                "branch": branch
            })
        except Exception as e:
            return f"Error deleting file '{path}': {str(e)}"


@tool
def github_commit(
    action: str,
    repo: str,
    branch: str = "master",
    sha: str = None,
    per_page: int = 30
):
    """
    View commit history and details.

    repo:
        Repository name.
        Example:
        langchain-agent

    Actions:
        history:
            show commits

        details:
            show single commit
    """

    client = gh()


    try:
        owner, repo = find_repo(repo)

    except Exception as e:
        return f"Repository error: {e}"


    if action == "history":

        commits = client.get(
            f"/repos/{owner}/{repo}/commits"
            f"?sha={branch}&per_page={per_page}"
        )


        if not isinstance(commits, list):
            return commits


        return [
            {
                "sha": c["sha"][:7],
                "message": c["commit"]["message"],
                "author": c["commit"]["author"]["name"],
                "date": c["commit"]["author"]["date"]
            }
            for c in commits
        ]


    if action == "details":

        if not sha:
            return "sha is required"


        return client.get(
            f"/repos/{owner}/{repo}/commits/{sha}"
        )


    return "Unknown action"


@tool
def github_issue(
    action: str,
    repo: str = None,
    number: int = None,
    title: str = None,
    body: str = None,
    state: str = "open",
    labels: list = None,
):
    """
    Manage GitHub issues.

    Repository owner is automatically detected from GITHUB_TOKEN.

    Examples:

    Create issue:
    {
        "action": "create",
        "repo": "langchain-agent",
        "title": "Bug report",
        "body": "Something is broken"
    }

    List issues:
    {
        "action": "list",
        "repo": "langchain-agent"
    }

    Get issue:
    {
        "action": "get",
        "repo": "langchain-agent",
        "number": 5
    }

    Update issue:
    {
        "action": "update",
        "repo": "langchain-agent",
        "number": 5,
        "title": "Updated title"
    }

    Comment:
    {
        "action": "comment",
        "repo": "langchain-agent",
        "number": 5,
        "body": "Looks good"
    }
    """

    client = gh()

    if not repo:
        return "Error: repository name is required"

    try:
        owner, repo = find_repo(repo)
    except Exception as e:
        return str(e)

    if action == "list":
        return client.get(
            f"/repos/{owner}/{repo}/issues?state={state}&per_page=50"
        )

    if action == "get":

        if not number:
            return "Error: issue number is required"

        return client.get(
            f"/repos/{owner}/{repo}/issues/{number}"
        )

    if action == "create":

        if not title:
            return "Error: issue title is required"

        return client.post(
            f"/repos/{owner}/{repo}/issues",
            {
                "title": title,
                "body": body or "",
                "labels": labels or []
            }
        )

    if action == "update":

        if not number:
            return "Error: issue number is required"

        payload = {}

        if title is not None:
            payload["title"] = title

        if body is not None:
            payload["body"] = body

        if state is not None:
            payload["state"] = state

        return client.patch(
            f"/repos/{owner}/{repo}/issues/{number}",
            payload
        )

    if action == "comment":

        if not number:
            return "Error: issue number is required"

        if not body:
            return "Error: comment body is required"

        return client.post(
            f"/repos/{owner}/{repo}/issues/{number}/comments",
            {"body": body}
        )

    return f"Unknown action: {action}"


@tool
def github_pull_request(
    action: str = "list",
    repo: str = None,
    head: str = None,
    base: str = "main",
    title: str = None,
    body: str = None,
    number: int = None,
    merge_method: str = "merge",
):
    """
    Manage GitHub pull requests.

    Repository owner is automatically detected.

    USER INTENT MAPPING

    Create PR:
        "create pr"
        "open pr"
        "make a pull request"

        =>
        action="create"

    Merge PR:
        "merge pr"
        "merge latest pr"
        "merge pull request"

        =>
        action="merge"

    List PRs:
        "show prs"
        "list prs"

        =>
        action="list"

    Examples:

    Create:
    {
        "action": "create",
        "repo": "langchain-agent",
        "head": "qa",
        "base": "master"
    }

    Merge latest:
    {
        "action": "merge",
        "repo": "langchain-agent"
    }

    Merge specific:
    {
        "action": "merge",
        "repo": "langchain-agent",
        "number": 12
    }
    """

    client = gh()

    if not repo:
        return "Error: repository name is required"

    try:
        owner, repo = find_repo(repo)
    except Exception as e:
        return str(e)

    if not action:
        action = "list"

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------
    if action == "create":

        if not head:
            return "Error: head branch required"

        return client.post(
            f"/repos/{owner}/{repo}/pulls",
            {
                "title": title or f"Merge {head} into {base}",
                "body": body or "",
                "head": head,
                "base": base,
            },
        )

    # --------------------------------------------------
    # LIST
    # --------------------------------------------------
    if action == "list":

        return client.get(
            f"/repos/{owner}/{repo}/pulls?state=open"
        )

    # --------------------------------------------------
    # GET
    # --------------------------------------------------
    if action == "get":

        if not number:
            return "Error: PR number required"

        return client.get(
            f"/repos/{owner}/{repo}/pulls/{number}"
        )

    # --------------------------------------------------
    # MERGE
    # --------------------------------------------------
    if action == "merge":

        # Auto-find latest open PR
        if number is None:

            prs = client.get(
                f"/repos/{owner}/{repo}/pulls?state=open"
            )

            if not isinstance(prs, list):
                return prs

            if len(prs) == 0:
                return "No open pull requests found"

            prs = sorted(
                prs,
                key=lambda x: x["number"],
                reverse=True
            )

            number = prs[0]["number"]

        # Optional validation
        pr = client.get(
            f"/repos/{owner}/{repo}/pulls/{number}"
        )

        if isinstance(pr, dict):

            if pr.get("state") != "open":
                return f"PR #{number} is not open"

            if pr.get("merged"):
                return f"PR #{number} is already merged"

        return client.put(
            f"/repos/{owner}/{repo}/pulls/{number}/merge",
            {
                "merge_method": merge_method
            }
        )

    return f"Unknown action: {action}"


@tool
def github_search(
    action:str,
    query:str=None,
    sort:str=None
):
    """
    Search GitHub.

    Actions:
        - repos         → Search repositories (sort: stars/forks/updated)
        - code          → Search code
        - issues        → Search issues and PRs (sort: created/updated/comments)
    """
    client = gh()

    if not query:
        return "Error: search query required"
    sort_qs = f"&sort={sort}" if sort else ""


    if action=="repos":
        return client.get(
            f"/search/repositories?q={query}{sort_qs}&per_page=20"
        )


    if action=="code":
        return client.get(
            f"/search/code?q={query}&per_page=20"
        )


    if action=="issues":
        return client.get(
            f"/search/issues?q={query}{sort_qs}&per_page=20"
        )


    return f"Unknown action: {action}"


@tool
def github_workflow(
    action: str,
    owner: str = None,
    repo: str = None,
    workflow_id: str = None,
    run_id: int = None,
    branch: str = "main",
    status: str = None,
    inputs: dict = None,
):
    """
    Manage GitHub Actions workflows.

    Actions:
        - list          → List all workflows in a repo
        - runs          → List workflow runs (optionally filter by workflow_id, status)
        - trigger       → Trigger a workflow dispatch (requires workflow_id)
        - status        → Get a specific run's status (requires run_id)
    """
    client = gh()
    try:
        owner, repo = resolve_repo(owner, repo)
    except Exception as e:
        return str(e)

    if action == "list":
        return client.get(f"/repos/{owner}/{repo}/actions/workflows")

    if action == "runs":
        base_path = f"/repos/{owner}/{repo}/actions/"
        base_path += f"workflows/{workflow_id}/runs" if workflow_id else "runs"
        qs = f"?per_page=20{f'&status={status}' if status else ''}"
        return client.get(base_path + qs)

    if action == "trigger":
        return client.post(
            f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            {"ref": branch, "inputs": inputs or {}}
        )

    if action == "status":
        return client.get(f"/repos/{owner}/{repo}/actions/runs/{run_id}")


