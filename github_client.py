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

    repos = client.get(
        "/user/repos?per_page=100&type=all"
    )


    if not isinstance(repos, list):
        raise Exception(
            f"Cannot fetch repositories: {repos}"
        )


    for r in repos:

        if r["name"].lower() == repo_name.lower():

            return (
                r["owner"]["login"],
                r["name"]
            )


    raise Exception(
        f"Repository '{repo_name}' not found in your GitHub account"
    )

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
        return client.get(f"/users/{username}")

    if action == "repos":
        return client.get(f"/user/repos?per_page=100&visibility={visibility}&sort=updated")


@tool
def github_repository(
    action: str,
    owner: str = None,
    repo: str = None,
    path: str = "",
    base: str = None,
    head: str = None,
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

    if action == "details":
        return client.get(f"/repos/{owner}/{repo}")

    if action == "contents":
        return client.get(f"/repos/{owner}/{repo}/contents/{path}")

    if action == "tags":
        return client.get(f"/repos/{owner}/{repo}/tags")

    if action == "compare":
        return client.get(f"/repos/{owner}/{repo}/compare/{base}...{head}")


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
            sha = client.get(f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")["sha"]
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
    owner: str = None,
    repo: str = None,
    branch: str = "main",
    sha: str = None,
    per_page: int = 30,
):
    """
    View commit history and details.

    Actions:
        - history       → Get commit history for a branch
        - details       → Get a single commit by sha
    """
    client = gh()

    if action == "history":
        return client.get(f"/repos/{owner}/{repo}/commits?sha={branch}&per_page={per_page}")

    if action == "details":
        return client.get(f"/repos/{owner}/{repo}/commits/{sha}")


@tool
def github_issue(
    action: str,
    owner: str = None,
    repo: str = None,
    number: int = None,
    title: str = None,
    body: str = None,
    state: str = "open",
    labels: list = None,
):
    """
    Manage issues.

    Actions:
        - list          → List issues (state: open/closed/all)
        - get           → Get a single issue by number
        - create        → Create issue (requires title, body)
        - update        → Update title/body/state (requires number)
        - comment       → Add a comment (requires number, body)
    """
    client = gh()

    if action == "list":
        return client.get(f"/repos/{owner}/{repo}/issues?state={state}&per_page=50")

    if action == "get":
        return client.get(f"/repos/{owner}/{repo}/issues/{number}")

    if action == "create":
        return client.post(f"/repos/{owner}/{repo}/issues", {
            "title": title,
            "body": body,
            "labels": labels or []
        })

    if action == "update":
        payload = {k: v for k, v in {"title": title, "body": body, "state": state}.items() if v}
        return client.patch(f"/repos/{owner}/{repo}/issues/{number}", payload)

    if action == "comment":
        return client.post(f"/repos/{owner}/{repo}/issues/{number}/comments", {"body": body})


@tool
def github_pull_request(
    action: str = "create",
    repo: str = None,
    head: str = None,
    base: str = "main",
    title: str = None,
    body: str = None,
    number: int = None,
    merge_method: str = "merge",
):
    """
    Manage pull requests.

    The repository owner is automatically detected from the GitHub token.

    IMPORTANT:
    If user says:
        "create PR"
        "open PR"
        "make a pull request"

    Always use:
    action="create"

    Parameters:

    repo:
        Repository name only.
        Example:
        langchain-agent

    head:
        Source branch.
        Example:
        qa

    base:
        Target branch.
        Example:
        master


    Create PR example:

    {
        "action": "create",
        "repo": "langchain-agent",
        "head": "qa",
        "base": "master",
        "title": "Merge qa into master",
        "body": "Changes from qa branch"
    }

    """

    client = gh()

    if not repo:
        return "Error: repository name is required"


    owner, repo = find_repo(repo)


    # safety fallback
    if action is None:
        action = "create"


    if action == "create":

        if not head:
            return "Error: head branch required"

        response = client.post(
            f"/repos/{owner}/{repo}/pulls",
            {
                "title": title or f"Merge {head} into {base}",
                "body": body or "",
                "head": head,
                "base": base
            }
        )

        return response


    if action == "list":

        return client.get(
            f"/repos/{owner}/{repo}/pulls"
        )


    if action == "get":

        return client.get(
            f"/repos/{owner}/{repo}/pulls/{number}"
        )


    if action == "merge":

        return client.put(
            f"/repos/{owner}/{repo}/pulls/{number}/merge",
            {
                "merge_method": merge_method
            }
        )


    return f"Unknown action: {action}"


@tool
def github_search(
    action: str,
    query: str = None,
    sort: str = None,
):
    """
    Search GitHub.

    Actions:
        - repos         → Search repositories (sort: stars/forks/updated)
        - code          → Search code
        - issues        → Search issues and PRs (sort: created/updated/comments)
    """
    client = gh()
    sort_qs = f"&sort={sort}" if sort else ""

    if action == "repos":
        return client.get(f"/search/repositories?q={query}{sort_qs}&per_page=20")

    if action == "code":
        return client.get(f"/search/code?q={query}&per_page=20")

    if action == "issues":
        return client.get(f"/search/issues?q={query}{sort_qs}&per_page=20")


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


