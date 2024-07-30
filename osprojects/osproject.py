"""
Created on 2022-01-24

@author: wf
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from typing import List, Optional, Type

import requests
from dateutil.parser import parse


class TicketSystem(object):
    """
    platform for hosting OpenSourceProjects and their issues
    """

    @classmethod
    def getIssues(self, project: OsProject, **kwargs) -> List[Ticket]:
        """
        get issues from the TicketSystem for a project
        """
        return NotImplemented

    @staticmethod
    def projectUrl(project: OsProject):
        """
        url of the project
        """
        return NotImplemented

    @staticmethod
    def ticketUrl(project: OsProject):
        """
        url of the ticket/issue list
        """
        return NotImplemented

    @staticmethod
    def commitUrl(project: OsProject, id: str):
        """
        url of the ticket/issue list
        """
        return NotImplemented


class GitHub(TicketSystem):
    """
    wrapper for the GitHub api
    """

    @classmethod
    def load_access_token(cls) -> str:
        """
        if $HOME/.github/access_token.json exists read the token from there
        """
        # Specify the path to the access token file
        token_file_path = os.path.join(
            os.getenv("HOME"), ".github", "access_token.json"
        )

        # Check if the file exists and read the token
        if os.path.exists(token_file_path):
            with open(token_file_path, "r") as token_file:
                token_data = json.load(token_file)
                return token_data.get("access_token")

        # Return None if no token file is found
        return None

    @classmethod
    def prepare_headers(cls, access_token: str = None) -> dict:
        """
        Prepare authorization headers for GitHub API requests.
        """
        if access_token is None:
            access_token = cls.load_access_token()

        headers = {"Authorization": f"token {access_token}"} if access_token else {}
        return headers

    @classmethod
    def list_projects_as_os_projects(
        cls, owner: str, access_token: str = None, project_name: Optional[str] = None
    ) -> List[OsProject]:
        """
        List all public repositories for a given owner and return them as OsProject instances.

        Args:
            owner (str): The GitHub username or organization name.
            access_token (str, optional): GitHub personal access token for authentication.
            project_name (str, optional): If provided, return only this specific project.

        Returns:
            List[OsProject]: A list of OsProject instances representing the repositories.
        """
        headers = cls.prepare_headers(access_token)

        if project_name:
            url = f"https://api.github.com/repos/{owner}/{project_name}"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch repository: {response.status_code} - {response.text}"
                )
            repos = [response.json()]
        else:
            url = f"https://api.github.com/users/{owner}/repos"
            params = {
                "type": "all",
                "per_page": 100,
            }  # Include all repo types, 100 per page
            all_repos = []
            page = 1

            while True:
                params["page"] = page
                response = requests.get(url, headers=headers, params=params)

                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch repositories: {response.status_code} - {response.text}"
                    )

                repos = response.json()
                if not repos:
                    break  # No more repositories to fetch

                all_repos.extend(repos)
                page += 1

            repos = all_repos

        return [
            OsProject(
                owner=owner,
                id=repo["name"],
                ticketSystem=cls,
                title=repo["name"],
                url=repo["html_url"],
                description=repo["description"],
                language=repo["language"],
                created_at=datetime.datetime.fromisoformat(
                    repo["created_at"].rstrip("Z")
                ),
                updated_at=datetime.datetime.fromisoformat(
                    repo["updated_at"].rstrip("Z")
                ),
                stars=repo["stargazers_count"],
                forks=repo["forks_count"],
            )
            for repo in repos
        ]

    @classmethod
    def get_project(
        cls, owner: str, project_id: str, access_token: str = None
    ) -> OsProject:
        """
        Get a specific project as an OsProject instance.

        Args:
            owner (str): The GitHub username or organization name.
            project_id (str): The name of the project.
            access_token (str, optional): GitHub personal access token for authentication.

        Returns:
            OsProject: An OsProject instance representing the repository.
        """
        projects = cls.list_projects_as_os_projects(
            owner, access_token, project_name=project_id
        )
        if projects:
            return projects[0]
        raise Exception(f"Project {owner}/{project_id} not found")

    @classmethod
    def getIssues(
        cls, project: OsProject, access_token: str = None, limit: int = None, **params
    ) -> List[Ticket]:
        payload = {}
        headers = cls.prepare_headers(access_token)
        issues = []
        nextResults = True
        params["per_page"] = 100
        params["page"] = 1
        fetched_count = 0  # Counter to track the number of issues fetched
        while nextResults:
            response = requests.request(
                "GET",
                GitHub.ticketUrl(project),
                headers=headers,
                data=payload,
                params=params,
            )
            if response.status_code == 403 and "rate limit" in response.text:
                raise Exception("rate limit - you might want to use an access token")
            issue_records = json.loads(response.text)
            for record in issue_records:
                tr = {
                    "project": project,
                    "title": record.get("title"),
                    "body": record.get("body", ""),
                    "createdAt": (
                        parse(record.get("created_at"))
                        if record.get("created_at")
                        else ""
                    ),
                    "closedAt": (
                        parse(record.get("closed_at"))
                        if record.get("closed_at")
                        else ""
                    ),
                    "state": record.get("state"),
                    "number": record.get("number"),
                    "url": f"{cls.projectUrl(project)}/issues/{record.get('number')}",
                }
                issues.append(Ticket.init_from_dict(**tr))
                fetched_count += 1
                # Check if we have reached the limit
                if limit is not None and fetched_count >= limit:
                    nextResults = False
                    break

            if len(issue_records) < 100:
                nextResults = False
            else:
                params["page"] += 1
        return issues

    @classmethod
    def getComments(
        cls, project: OsProject, issue_number: int, access_token: str = None
    ) -> List[dict]:
        """
        Fetch all comments for a specific issue number from GitHub.
        """
        headers = cls.prepare_headers(access_token)
        comments_url = GitHub.commentUrl(project, issue_number)
        response = requests.get(comments_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Failed to fetch comments: {response.status_code} - {response.text}"
            )
        return []

    @staticmethod
    def projectUrl(project: OsProject):
        return f"https://github.com/{project.owner}/{project.id}"

    @staticmethod
    def ticketUrl(project: OsProject):
        return f"https://api.github.com/repos/{project.owner}/{project.id}/issues"

    @staticmethod
    def commitUrl(project: OsProject, id: str):
        return f"{GitHub.projectUrl(project)}/commit/{id}"

    @staticmethod
    def commentUrl(project: OsProject, issue_number: int):
        """
        Construct the URL for accessing comments of a specific issue.
        """
        return f"https://api.github.com/repos/{project.owner}/{project.id}/issues/{issue_number}/comments"

    @staticmethod
    def resolveProjectUrl(url: str) -> (str, str):
        """
        Resolve project url to owner and project name

        Returns:
            (owner, project)
        """
        # https://www.rfc-editor.org/rfc/rfc3986#appendix-B
        pattern = r"((https?:\/\/github\.com\/)|(git@github\.com:))(?P<owner>[^/?#]+)\/(?P<project>[^\./?#]+)(\.git)?"
        match = re.match(pattern=pattern, string=url)
        owner = match.group("owner")
        project = match.group("project")
        if owner and project:
            return owner, project


class Jira(TicketSystem):
    """
    wrapper for Jira api
    """


class OsProject(object):
    """
    an Open Source Project
    """

    def __init__(
        self,
        owner: str = None,
        id: str = None,
        ticketSystem: Type[TicketSystem] = None,
        title: str = None,
        url: str = None,
        description: str = None,
        language: str = None,
        created_at: datetime.datetime = None,
        updated_at: datetime.datetime = None,
        stars: int = 0,
        forks: int = 0,
    ):
        """
        Constructor
        """
        self.owner = owner
        self.id = id
        self.ticketSystem = ticketSystem or GitHub
        self.title = title
        self.url = url
        self.description = description
        self.language = language
        self.created_at = created_at
        self.updated_at = updated_at
        self.stars = stars
        self.forks = forks

    def __str__(self):
        return f"{self.owner}/{self.id}"

    @staticmethod
    def getSamples():
        samples = [
            {
                "id": "pyOpenSourceProjects",
                "owner": "WolfgangFahl",
                "title": "pyOpenSourceProjects",
                "url": "https://github.com/WolfgangFahl/pyOpenSourceProjects",
                "description": "Helper Library to organize open source Projects",
                "language": "Python",
                "created_at": datetime.datetime(year=2022, month=1, day=24),
                "updated_at": datetime.datetime(year=2022, month=1, day=24),
                "stars": 5,
                "forks": 2,
            }
        ]
        return samples

    @classmethod
    def fromRepo(cls):
        """
        Init OsProject from repo in current working directory
        """
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"])
        url = url.decode().strip("\n")
        return cls.fromUrl(url)

    @classmethod
    def fromUrl(cls, url: str) -> OsProject:
        """
        Init OsProject from given url
        """
        if "github.com" in url:
            owner, project_id = GitHub.resolveProjectUrl(url)
            if owner and project_id:
                github = GitHub()
                project = github.get_project(owner, project_id)
                return project
        raise Exception(f"Could not resolve the url '{url}' to a OsProject object")

    def getIssues(self, **params) -> list:
        tickets = self.ticketSystem.getIssues(self, **params)
        tickets.sort(key=lambda r: getattr(r, "number"), reverse=True)
        return tickets

    def getAllTickets(self, limit: int = None, **params):
        """
        Get all Tickets of the project -  closed and open ones

        Args:
            limit(int): if set limit the number of tickets retrieved
        """
        issues = self.getIssues(state="all", limit=limit, **params)
        return issues

    def getCommits(self) -> List[Commit]:
        commits = []
        gitlogCmd = [
            "git",
            "--no-pager",
            "log",
            "--reverse",
            r'--pretty=format:{"name":"%cn","date":"%cI","hash":"%h"}',
        ]
        gitLogCommitSubject = ["git", "log", "--format=%s", "-n", "1"]
        rawCommitLogs = subprocess.check_output(gitlogCmd).decode()
        for rawLog in rawCommitLogs.split("\n"):
            log = json.loads(rawLog)
            if log.get("date", None) is not None:
                log["date"] = datetime.datetime.fromisoformat(log["date"])
            log["project"] = self.id
            log["host"] = self.ticketSystem.projectUrl(self)
            log["path"] = ""
            log["subject"] = subprocess.check_output(
                [*gitLogCommitSubject, log["hash"]]
            )[
                :-1
            ].decode()  # seperate query to avoid json escaping issues
            commit = Commit()
            for k, v in log.items():
                setattr(commit, k, v)
            commits.append(commit)
        return commits


class Ticket(object):
    """
    a Ticket
    """

    @staticmethod
    def getSamples():
        samples = [
            {
                "number": 2,
                "title": "Get Tickets in Wiki notation from github API",
                "createdAt": datetime.datetime.fromisoformat(
                    "2022-01-24 07:41:29+00:00"
                ),
                "closedAt": datetime.datetime.fromisoformat(
                    "2022-01-25 07:43:04+00:00"
                ),
                "url": "https://github.com/WolfgangFahl/pyOpenSourceProjects/issues/2",
                "project": "pyOpenSourceProjects",
                "state": "closed",
            }
        ]
        return samples

    @classmethod
    def init_from_dict(cls, **records):
        """
        inits Ticket from given args
        """
        issue = Ticket()
        for k, v in records.items():
            setattr(issue, k, v)
        return issue

    def toWikiMarkup(self) -> str:
        """
        Returns Ticket in wiki markup
        """
        return f"""# {{{{Ticket
|number={self.number}
|title={self.title}
|project={self.project.id}
|createdAt={self.createdAt if self.createdAt else ""}
|closedAt={self.closedAt if self.closedAt else ""}
|state={self.state}
}}}}"""


class Commit(object):
    """
    a commit
    """

    @staticmethod
    def getSamples():
        samples = [
            {
                "host": "https://github.com/WolfgangFahl/pyOpenSourceProjects",
                "path": "",
                "project": "pyOpenSourceProjects",
                "subject": "Initial commit",
                "name": "GitHub",  # TicketSystem
                "date": datetime.datetime.fromisoformat("2022-01-24 07:02:55+01:00"),
                "hash": "106254f",
            }
        ]
        return samples

    def toWikiMarkup(self):
        """
        Returns Commit as wiki markup
        """
        params = [
            f"{attr}={getattr(self, attr, '')}" for attr in self.getSamples()[0].keys()
        ]
        markup = f"{{{{commit|{'|'.join(params)}|storemode=subobject|viewmode=line}}}}"
        return markup


def gitlog2wiki(_argv=None):
    """
    cmdline interface to get gitlog entries in wiki markup
    """
    parser = argparse.ArgumentParser(description="gitlog2wiki")
    if _argv:
        _args = parser.parse_args(args=_argv)

    osProject = OsProject.fromRepo()
    commits = osProject.getCommits()
    print("\n".join([c.toWikiMarkup() for c in commits]))


def main(_argv=None):
    """
    main command line entry point
    """
    parser = argparse.ArgumentParser(description="Issue2ticket")
    parser.add_argument("-o", "--owner", help="project owner or organization")
    parser.add_argument("-p", "--project", help="name of the project")
    parser.add_argument(
        "--repo",
        action="store_true",
        help="get needed information form repository of current location",
    )
    parser.add_argument(
        "-ts",
        "--ticketsystem",
        default="github",
        choices=["github", "jira"],
        help="platform the project is hosted",
    )
    parser.add_argument(
        "-s",
        "--state",
        choices=["open", "closed", "all"],
        default="all",
        help="only issues with the given state",
    )
    parser.add_argument("-V", "--version", action="version", version="gitlog2wiki 0.1")

    args = parser.parse_args(args=_argv)
    # resolve ticketsystem
    ticketSystem = GitHub
    if args.ticketsystem == "jira":
        ticketSystem = Jira
    if args.project and args.owner:
        osProject = OsProject(
            owner=args.owner, id=args.project, ticketSystem=ticketSystem
        )
    else:
        osProject = OsProject.fromRepo()
    tickets = osProject.getIssues(state=args.state)
    print("\n".join([t.toWikiMarkup() for t in tickets]))


if __name__ == "__main__":
    # sys.exit(main())
    sys.exit(gitlog2wiki())
