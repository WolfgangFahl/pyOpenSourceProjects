"""Created on 2022-01-24.

@author: wf
"""

import argparse
import configparser
import datetime
import json
import logging
import os
import subprocess
import sys
from typing import Dict, Iterable, List, Optional, Set, Tuple

from dateutil.parser import parse
from tqdm import tqdm

from osprojects.github_api import GitHubApi, GitHubRepo


class Ticket(object):
    """A Ticket."""

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
        """Inits Ticket from given args."""
        issue = Ticket()
        for k, v in records.items():
            setattr(issue, k, v)
        return issue

    def toWikiMarkup(self) -> str:
        """Returns Ticket in wiki markup."""
        return f"""# {{{{Ticket
|number={self.number}
|title={self.title}
|project={self.project}
|createdAt={self.createdAt if self.createdAt else ""}
|closedAt={self.closedAt if self.closedAt else ""}
|state={self.state}
}}}}"""


class Commit(object):
    """A commit."""

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
        """Returns Commit as wiki markup."""
        params = [
            f"{attr}={getattr(self, attr, '')}" for attr in self.getSamples()[0].keys()
        ]
        markup = f"{{{{commit|{'|'.join(params)}|storemode=subobject|viewmode=line}}}}"
        return markup


class OsProjects:
    """A set of open source projects."""

    def __init__(self):
        """constructor."""
        self.projects = {}
        self.projects_by_url = {}
        self.local_projects = {}
        self.selected_projects = {}
        self.owners = []
        self.github = GitHubApi.get_instance()

    def clear_selection(self):
        self.selected_projects = {}

    def add_selection(self, project):
        is_fork = project.repo_info["fork"]
        if not is_fork:
            self.selected_projects[project.projectUrl()] = project

    def select_projects(self, owners=None, project_id=None, local_only=False):
        """Select projects based on given criteria.

        Args:
            owners (Optional[list[str]]): The owners of the projects to select.
            project_id (Optional[str]): The ID of a specific project to select.
            local_only (bool): Whether to select only local projects.

        Returns:
            Dict[str, OsProject]: A dictionary of selected projects.

        Raises:
            ValueError: If owner or local_only flag is not specified with project_id.
        """
        if project_id:
            if owners:
                for owner in owners:
                    key = f"https://github.com/{owner}/{project_id}"
                    project = self.projects_by_url.get(key)
                    if project:
                        self.add_selection(project)
            elif local_only:
                for _url, project in self.local_projects.items():
                    if project.project_id == project_id:
                        self.add_selection(project)
            else:
                raise ValueError(
                    "Owner or local_only flag must be specified with project_id"
                )

        elif owners:
            for owner in owners:
                if owner in self.projects:
                    for project in self.projects[owner].values():
                        self.add_selection(project)
        elif local_only:
            for project in self.local_projects.values():
                self.add_selection(project)
        else:
            for project in self.projects_by_url.values():
                self.add_selection(project)

        return self.selected_projects

    def filter_projects(self, language=None, local_only=False):
        """Filter the selected projects based on language and locality.

        Args:
            language (str, optional): The programming language to filter by.
            local_only (bool, optional): If True, only return local projects.

        Returns:
            Dict[str, OsProject]: The filtered projects.
        """
        filtered_projects = {}

        for url, project in self.selected_projects.items():
            include_project = True

            if language and project.language != language:
                include_project = False

            if local_only and not project.folder:
                include_project = False

            if include_project:
                filtered_projects[url] = project

        self.selected_projects = filtered_projects
        return self.selected_projects

    def add_projects_of_owner(self, owner: str, cache_expiry: int = 300):
        """Add the projects of the given owner."""
        if not owner in self.projects:
            self.projects[owner] = {}
            repo_infos = self.github.repos_for_owner(owner, cache_expiry)
            for repo_info in repo_infos:
                project_id = repo_info["name"]
                os_project = OsProject(owner=owner, project_id=project_id)
                os_project.repo_info = repo_info
                self.projects[owner][project_id] = os_project
                self.projects_by_url[os_project.projectUrl()] = os_project
        else:
            # owner already known
            pass

    @classmethod
    def from_owners(cls, owners: list[str]):
        osp = cls()
        for owner in owners:
            osp.add_projects_of_owner(owner)
        return osp

    @classmethod
    def get_project_url_from_git_config(cls, project_path: str) -> Optional[str]:
        """Get the project URL from the git config file.

        Args:
            project_path (str): The path to the project directory.

        Returns:
            Optional[str]: The project URL if found, None otherwise.
        """
        config_path = os.path.join(project_path, ".git", "config")
        if not os.path.exists(config_path):
            return None

        config = configparser.ConfigParser()
        config.read(config_path)

        if 'remote "origin"' not in config:
            return None

        url = config['remote "origin"']["url"]
        # remove trailing / if any
        url = url.rstrip("/")
        return url

    @classmethod
    def from_folder(cls, folder_path: str, with_progress: bool = False) -> "OsProjects":
        """Collect all github projects from the given folders.

        Args:
            folder_path (str): The path to the folder containing projects.
            with_progress (bool): Whether to display a progress bar. Defaults to True.

        Returns:
            OsProjects: An instance of OsProjects with collected projects.
        """
        osp = cls()
        owners, repos_by_folder = cls.github_repos_of_folder(folder_path)

        def process_owners(owners_iterable: Iterable[str]):
            for owner in owners_iterable:
                osp.add_projects_of_owner(owner)

        if with_progress:
            process_owners(tqdm(owners, desc="Processing owners"))
        else:
            process_owners(owners)

        for folder, repo in repos_by_folder.items():
            project_url = repo.projectUrl()
            if project_url not in osp.projects_by_url:
                logging.warning(f"{project_url} not found in projects_by_url")
            else:
                local_project = osp.projects_by_url[project_url]
                local_project.folder = folder
                osp.local_projects[project_url] = local_project

        return osp

    @classmethod
    def github_repos_of_folder(
        cls, folder_path: str
    ) -> Tuple[Set[str], Dict[str, GitHubRepo]]:
        """Collect GitHub repositories from a given folder.

        Args:
            folder_path (str): The path to the folder to search for repositories.

        Returns:
            Tuple[Set[str], Dict[str, GitHubRepo]]: A tuple containing a set of owners
            and a dictionary of repositories keyed by folder path.
        """
        all_folders = []
        repos_by_folder: Dict[str, GitHubRepo] = {}
        owners: Set[str] = set()

        for d in os.listdir(folder_path):
            sub_folder = os.path.join(folder_path, d)
            if os.path.isdir(sub_folder):
                all_folders.append(sub_folder)

        for folder in all_folders:
            project_url = cls.get_project_url_from_git_config(folder)
            if project_url:
                github_repo = GitHubRepo.from_url(project_url)
                if github_repo:
                    repos_by_folder[folder] = github_repo
                    owners.add(github_repo.owner)

        return owners, repos_by_folder


class OsProject:
    """A GitHub based opens source project."""

    def __init__(self, owner: str = None, project_id: str = None):
        self.repo_info = None  # might be fetched
        self.folder = None  # set for local projects
        if owner and project_id:
            self.repo = GitHubRepo(owner=owner, project_id=project_id)

    @classmethod
    def fromUrl(cls, url: str) -> "OsProject":
        """Init OsProject from given url."""
        if "github.com" in url:
            os_project = cls()
            os_project.repo = GitHubRepo.from_url(url)
        else:
            raise Exception(f"url '{url}' is not a github.com url ")
        return os_project

    @classmethod
    def fromRepo(cls):
        """Init OsProject from repo in current working directory."""
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"])
        url = url.decode().strip("\n")
        repo = cls.fromUrl(url)
        return repo

    def getIssues(self, limit: int = None, **params) -> List[Ticket]:

        # Fetch the raw issue records using the new getIssueRecords method
        issue_records = self.repo.getIssueRecords(limit=limit, **params)

        issues = []
        for record in issue_records:
            tr = {
                "project": self.repo.project_id,
                "title": record.get("title"),
                "body": record.get("body", ""),
                "createdAt": (
                    parse(record.get("created_at")) if record.get("created_at") else ""
                ),
                "closedAt": (
                    parse(record.get("closed_at")) if record.get("closed_at") else ""
                ),
                "state": record.get("state"),
                "number": record.get("number"),
                "url": f"{self.projectUrl()}/issues/{record.get('number')}",
            }
            issues.append(Ticket.init_from_dict(**tr))

            # Check if we have reached the limit
            if limit is not None and len(issues) >= limit:
                break

        return issues

    def getAllTickets(
        self, limit: int = None, with_sort: bool = True
    ) -> Dict[int, Ticket]:
        """
        Get all Tickets of the project - closed and open ones

        Args:
            limit(int): if set, limit the number of tickets retrieved
            with_sort(bool): if True, sort the tickets by number in descending order

        Returns:
            Dict[int, Ticket]: A dictionary of tickets keyed by their number
        """
        tickets = self.getIssues(state="all", limit=limit)

        # Sort the tickets if with_sort is True
        if with_sort:
            tickets.sort(key=lambda r: getattr(r, "number"), reverse=True)

        # Convert the list of tickets into a dictionary keyed by the ticket number
        tickets_dict = {ticket.number: ticket for ticket in tickets}

        return tickets_dict

    def getComments(self, issue_number: int) -> List[dict]:
        """Fetch all comments for a specific issue number from GitHub."""
        comments_url = self.commentUrl(issue_number)
        gihub_api=GitHubApi.get_instance()
        response = gihub_api.get_response("fetch comments", comments_url)
        return response.json()

    def projectUrl(self):
        return self.repo.projectUrl()

    def commitUrl(self, commit_id: str):
        return f"{self.projectUrl()}/commit/{commit_id}"

    def commentUrl(self, issue_number: int):
        """Construct the URL for accessing comments of a specific issue."""
        return f"{self.repo.github.api_url}/repos/{self.repo.owner}/{self.repo.project_id}/issues/{issue_number}/comments"

    @property
    def project_id(self):
        return self.repo.project_id

    @property
    def owner(self):
        return self.repo.owner

    @property
    def title(self):
        return self.repo_info.get("name") or self.project_id

    @property
    def url(self):
        return (
            self.repo_info.get("html_url")
            or f"https://github.com/{self.repo.owner}/{self.project_id}"
        )

    @property
    def description(self):
        return self.repo_info.get("description") or ""

    @property
    def language(self):
        return self.repo_info.get("language") or "python"

    @property
    def created_at(self):
        created_at = self.repo_info.get("created_at")
        return (
            datetime.datetime.fromisoformat(created_at.rstrip("Z"))
            if created_at
            else None
        )

    @property
    def updated_at(self):
        updated_at = self.repo_info.get("updated_at")
        return (
            datetime.datetime.fromisoformat(updated_at.rstrip("Z"))
            if updated_at
            else None
        )

    @property
    def stars(self):
        return self.repo_info.get("stargazers_count")

    @property
    def forks(self):
        return self.repo_info.get("forks_count")

    @property
    def fqid(self):
        return f"{self.repo.owner}/{self.repo.project_id}"

    def __str__(self):
        return self.fqid

    @staticmethod
    def getSamples():
        samples = [
            {
                "project_id": "pyOpenSourceProjects",
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
            log["project"] = self.project_id
            log["host"] = self.projectUrl()
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


def gitlog2wiki(_argv=None):
    """Cmdline interface to get gitlog entries in wiki markup."""
    parser = argparse.ArgumentParser(description="gitlog2wiki")
    if _argv:
        _args = parser.parse_args(args=_argv)

    osProject = OsProject.fromRepo()
    commits = osProject.getCommits()
    print("\n".join([c.toWikiMarkup() for c in commits]))


def main(_argv=None):
    """Main command line entry point."""
    parser = argparse.ArgumentParser(description="Issue2ticket")
    parser.add_argument("-o", "--owner", help="project owner")
    parser.add_argument("-p", "--project", help="name of the project")
    parser.add_argument(
        "--repo",
        action="store_true",
        help="get needed information form repository of current location",
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
    if args.project and args.owner:
        osProject = OsProject(
            owner=args.owner,
            project_id=args.project,
        )
    else:
        osProject = OsProject.fromRepo()
    tickets = osProject.getIssues(state=args.state)
    print("\n".join([t.toWikiMarkup() for t in tickets]))


if __name__ == "__main__":
    # sys.exit(main())
    sys.exit(gitlog2wiki())
