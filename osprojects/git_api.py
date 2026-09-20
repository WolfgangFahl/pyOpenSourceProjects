"""Created on 2026-03-16.

@author: wf
"""

import re
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Optional, Tuple


@dataclass
class GenericRepo:
    """Represents a generic git repository hosted on any forge.

    Parses owner and project_id from any standard git remote URL
    (scheme: ssh://git@host/owner/repo.git or https://host/owner/repo.git,
    scp like: git@host:owner/repo.git).

    Attributes:
        owner (str): The owner of the repository.
        project_id (str): The name/id of the repository.
        url (str): The original remote URL.
    """

    owner: str
    project_id: str
    url: str

    # forge name used in messages
    forge: ClassVar[str] = "git"
    # directory holding the CI workflow files
    workflows_dir: ClassVar[str] = ".github/workflows"
    # workflow files a project must have
    required_workflows: ClassVar[Tuple[str, ...]] = ("build.yml",)
    # the runs-on/os expectation of build.yml
    os_needle: ClassVar[str] = "runs-on: ubuntu-latest"

    @classmethod
    def parse_url(cls, url: str) -> Optional[Dict[str, str]]:
        """Parse host and path components from a git remote URL.

        Args:
            url: scheme based or scp like git remote URL.

        Returns:
            dict with host, owner, project_id and path or None if the URL
            cannot be parsed.
        """
        scheme_pattern = r"^[a-z+]+://(?:[^@/]+@)?(?P<host>[^/:]+)(?::\d+)?/(?P<path>.+?)(?:\.git)?/?$"
        scp_pattern = r"^(?:[^@/]+@)?(?P<host>[^:/]+):(?P<path>.+?)(?:\.git)?/?$"
        parsed = None
        match = re.match(scheme_pattern, url) or re.match(scp_pattern, url)
        if match:
            path = match.group("path")
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 2:
                parsed = {
                    "host": match.group("host"),
                    "path": "/".join(parts),
                    "owner": parts[-2],
                    "project_id": parts[-1],
                }
        return parsed

    @classmethod
    def from_url(cls, url: str) -> Optional["GenericRepo"]:
        """Parse owner and project_id from any standard git remote URL.

        Args:
            url: SSH or HTTPS git remote URL.

        Returns:
            GenericRepo instance or None if the URL cannot be parsed.
        """
        repo = None
        parsed = cls.parse_url(url)
        if parsed:
            repo = cls(
                owner=parsed["owner"],
                project_id=parsed["project_id"],
                url=url,
            )
        return repo

    @property
    def host(self) -> str:
        """The host name of the forge."""
        parsed = self.parse_url(self.url)
        host = parsed["host"] if parsed else ""
        return host

    def projectUrl(self) -> str:
        """Return a browsable HTTPS project URL derived from the remote URL."""
        parsed = self.parse_url(self.url)
        if parsed:
            url = f"https://{parsed['host']}/{parsed['path']}"
        else:
            url = re.sub(r"\.git$", "", self.url)
        return url

    def local_repo_info(self) -> Dict:
        """Repository information as the forge API would deliver it, derived
        from the remote URL only - for forges without an accessible API."""
        repo_info = {
            "name": self.project_id,
            "owner": {"login": self.owner},
            "fork": False,
            "html_url": self.projectUrl(),
            "description": "",
            "language": None,
        }
        return repo_info

    def badge_lines(self, project_name: str) -> List[str]:
        """The badge markdown lines a README.md of this forge must contain.

        Args:
            project_name: the name of the python package

        Returns:
            list of badge markdown lines
        """
        badge_lines = []
        return badge_lines

    def badge_markdown(self, project_name: str) -> str:
        """The badge table markdown for a README.md of this forge.

        Args:
            project_name: the name of the python package

        Returns:
            markdown of the badge table
        """
        markup = "\n".join(self.badge_lines(project_name))
        return markup

    def getIssueRecords(self, limit: int = None, **params) -> List[Dict]:
        """Not implemented for generic repos."""
        raise NotImplementedError(
            f"getIssueRecords is not supported for generic repo '{self.projectUrl()}'"
        )
