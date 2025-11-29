"""Created on 2024-08-27.

@author: wf
"""

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List
from urllib.parse import urlparse

import requests


class GitHubApi:
    """
    access to GitHubApi - needed for rate limit handling avoidance
    via access token
    """

    githubapi_instance: "GitHubApi" = None

    @classmethod
    def get_instance(cls) -> "GitHubApi":
        """Singleton access."""
        if cls.githubapi_instance is None:
            cls.githubapi_instance = cls()
        return cls.githubapi_instance

    def __init__(self):
        """constructor."""
        home_dir = os.path.expanduser("~")
        self.base_dir = os.path.join(home_dir, ".github")
        os.makedirs(self.base_dir, exist_ok=True)
        self.cache_dir = os.path.join(self.base_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.log_dir = os.path.join(self.base_dir, "log")
        os.makedirs(self.log_dir, exist_ok=True)
        self.access_token = self.load_access_token()
        self.headers = (
            {"Authorization": f"token {self.access_token}"} if self.access_token else {}
        )
        self.api_url = "https://api.github.com"

    def load_access_token(self) -> str:
        """If $HOME/.github/access_token.json exists read the token from
        there."""
        # Specify the path to the access token file
        token_file_path = os.path.join(self.base_dir, "access_token.json")

        # Check if the file exists and read the token
        if os.path.exists(token_file_path):
            with open(token_file_path, "r") as token_file:
                token_data = json.load(token_file)
                return token_data.get("access_token")

        # Return None if no token file is found
        return None

    def get_response(self, title: str, url: str, params={}, allow_redirects=True):
        """Get response from GitHub API or Google Docs API.

        Args:
            title (str): Description of the request
            url (str): URL to send the request to
            params (dict): Query parameters for the request
            allow_redirects (bool): Whether to follow redirects

        Returns:
            requests.Response: The response object
        """
        response = requests.get(
            url, headers=self.headers, params=params, allow_redirects=allow_redirects
        )

        if response.status_code == 302 and not allow_redirects:
            # Return the redirect URL if we're not following redirects
            return response.headers["Location"]

        if response.status_code not in [200, 302]:
            err_msg = (
                f"Failed to {title} for {url}: {response.status_code} - {response.text}"
            )
            raise Exception(err_msg)

        return response

    def repos_for_owner(self, owner: str, cache_expiry: int = 300) -> list[dict]:
        """Retrieve all repositories for the given owner, using cache if
        available and valid, or via API otherwise.

        This method first checks if the repository data is available in the cache. If not, it fetches the
        data from the GitHub API and caches it for future use.

        Args:
            owner (str): The username of the owner whose repositories are being retrieved.
            cache_expiry (int, optional): The cache expiry time in seconds. Defaults to 60 seconds (1 minute).

        Returns:
            list[dict]: A list of dictionaries representing repositories.
        """
        # Attempt to retrieve from cache
        cache_file, cache_content, cache_age = self.repos_for_owner_from_cache(owner)

        # Use cache if it exists and is not expired
        if cache_content is not None and (
            cache_age is None or cache_age < cache_expiry
        ):
            return cache_content

        # If cache is not available or expired, retrieve from API
        repos = self.repos_for_owner_via_api(owner)

        # Cache the result
        with open(cache_file, "w") as f:
            json.dump(repos, f)

        return repos

    def repos_for_owner_from_cache(
        self, owner: str
    ) -> tuple[str, list[dict] | None, float | None]:
        """Retrieve repositories for the given owner from the cache.

        Args:
            owner (str): The username of the owner whose repositories are being retrieved.

        Returns:
            tuple[str, list[dict] | None, float | None]: A tuple containing:
                - cache_file (str): The path to the cache file.
                - cache_content (list[dict] | None): A list of dictionaries representing repositories if cached data exists, None otherwise.
                - cache_age (float | None): The age of the cache in seconds if cached data exists, None otherwise.
        """
        cache_file = os.path.join(self.cache_dir, f"{owner}_repos.json")
        cache_content = None
        cache_age = None

        # Check if cached data exists and is still valid
        if os.path.exists(cache_file):
            cache_age = time.time() - os.path.getmtime(cache_file)
            with open(cache_file, "r") as f:
                cache_content = json.load(f)

        return cache_file, cache_content, cache_age

    def repos_for_owner_via_api(self, owner: str) -> list[dict]:
        """Retrieve all repositories for the given owner directly from the
        GitHub API.

        Args:
            owner (str): The username of the owner whose repositories are being retrieved.

        Returns:
            list[dict]: A list of dictionaries representing repositories retrieved from the GitHub API.
        """
        url = f"{self.api_url}/users/{owner}/repos"
        params = {
            "type": "all",
            "per_page": 100,
        }  # Include all repo types, 100 per page
        all_repos = []
        page = 1

        while True:
            params["page"] = page
            response = self.get_response("fetch repositories", url, params)
            repos = response.json()
            if not repos:
                break  # No more repositories to fetch

            all_repos.extend(repos)
            page += 1

        repos = all_repos
        return repos


@dataclass
class GitHubRepo:
    """Represents a GitHub Repository.

    Attributes:
        owner (str): The owner of the repository.
        project_id (str): The name/id of the repository.
    """

    owner: str
    project_id: str

    def __post_init__(self):
        self.github = GitHubApi.get_instance()

    @classmethod
    def from_url(cls, url: str) -> (str, str):
        """Resolve project url to owner and project name.

        Returns:
            (owner, project)
        """
        # https://www.rfc-editor.org/rfc/rfc3986#appendix-B
        pattern = r"((https?:\/\/github\.com\/)|(git@github\.com:))(?P<owner>[^/?#]+)\/(?P<project_id>[^\./?#]+)(\.git)?"
        match = re.match(pattern=pattern, string=url)
        repo = None
        if match:
            owner = match.group("owner")
            project_id = match.group("project_id")
            if owner and project_id:
                repo = cls(owner=owner, project_id=project_id)
            else:
                pass
        else:
            pass
        return repo

    def ticketUrl(self):
        return f"{self.github.api_url}/repos/{self.owner}/{self.project_id}/issues"

    def projectUrl(self):
        return f"https://github.com/{self.owner}/{self.project_id}"

    def getIssueRecords(self, limit: int = None, **params) -> List[Dict]:
        all_issues_records = []
        nextResults = True
        params["per_page"] = 100
        params["page"] = 1
        fetched_count = 0  # Counter to track the number of issues fetched
        while nextResults:
            response = self.github.get_response(
                "fetch tickets", self.ticketUrl(), params
            )
            issue_records = json.loads(response.text)
            all_issues_records.extend(issue_records)
            fetched_count += 1
            # Check if we have reached the limit
            if limit is not None and fetched_count >= limit:
                nextResults = False
                break

            if len(issue_records) < 100:
                nextResults = False
            else:
                params["page"] += 1
        return all_issues_records


@dataclass
class GitHubAction:
    """Represents a GitHub Action with its identifying information and log
    content.

    Attributes:
        repo (GitHubRepo): The repository associated with this action.
        run_id (int): The ID of the workflow run.
        job_id (int): The ID of the job within the run.
        log_content (str): The log content of the action.
    """

    repo: GitHubRepo
    run_id: int
    job_id: int
    log_content: str = field(default=None, repr=False)
    do_cache: bool = True

    def __post_init__(self):
        self.log_id = (
            f"{self.repo.owner}_{self.repo.project_id}_{self.run_id}_{self.job_id}"
        )
        self.log_file = os.path.join(
            self.repo.github.log_dir, f"action_log_{self.log_id}.txt"
        )
        # If log file exists, read the content
        if os.path.exists(self.log_file):
            with open(self.log_file, "r", encoding="utf-8") as f:
                self.log_content = f.read()

    @classmethod
    def from_url(cls, url: str) -> "GitHubAction":
        """Create a GitHubAction instance from a GitHub Actions URL and fetch
        its logs.

        Args:
            url (str): The GitHub Actions URL.

        Returns:
            GitHubAction: An instance of GitHubAction containing parsed information.

        Raises:
            ValueError: If the URL format is invalid or missing required components.
        """
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split("/")

        if len(path_parts) < 8 or path_parts[3] != "actions" or path_parts[4] != "runs":
            raise ValueError("Invalid GitHub Actions URL format")

        try:
            repo = GitHubRepo(owner=path_parts[1], project_id=path_parts[2])
            return cls(repo=repo, run_id=int(path_parts[5]), job_id=int(path_parts[7]))
        except (IndexError, ValueError) as e:
            raise ValueError(f"Failed to parse GitHub Actions URL: {e}")

    @classmethod
    def get_latest_workflow_run(cls, project):
        """Get the latest GitHub Actions workflow run for a given project.

        Args:
            project (OsProject): The project to check for the latest workflow run.

        Returns:
            dict: Information about the latest workflow run, or None if not found.
        """
        url = f"https://api.github.com/repos/{project.owner}/{project.project_id}/actions/runs"
        response = project.repo.github.get_response("fetch latest workflow run", url)
        runs = response.json().get("workflow_runs", [])
        run = None
        if runs:
            run = runs[0]  # Return the latest run
        return run

    def fetch_logs(self):
        """Fetch the logs for this GitHub Action."""
        if self.log_content is None:
            api_url = f"https://api.github.com/repos/{self.repo.owner}/{self.repo.project_id}/actions/jobs/{self.job_id}/logs"
            log_response = self.repo.github.get_response(
                "fetch job logs", api_url, allow_redirects=True
            )
            self.log_content = log_response.content.decode("utf-8-sig")
            if self.do_cache:
                self.save_logs()

    def save_logs(self):
        """Save the log content to a local file."""
        if self.log_content is None:
            raise ValueError("No log content to save. Make sure to fetch logs first.")
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(self.log_content)
