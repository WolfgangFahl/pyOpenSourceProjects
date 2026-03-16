"""Created on 2026-03-16.

@author: wf
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class GenericRepo:
    """Represents a generic git repository hosted on any forge.

    Parses owner and project_id from any standard git remote URL
    (SSH: git@host:owner/repo.git or HTTPS: https://host/owner/repo.git).

    Attributes:
        owner (str): The owner of the repository.
        project_id (str): The name/id of the repository.
        url (str): The original remote URL.
    """

    owner: str
    project_id: str
    url: str

    @classmethod
    def from_url(cls, url: str) -> Optional["GenericRepo"]:
        """Parse owner and project_id from any standard git remote URL.

        Args:
            url: SSH or HTTPS git remote URL.

        Returns:
            GenericRepo instance or None if the URL cannot be parsed.
        """
        pattern = (
            r"(?:https?://[^/]+/|git@[^:]+:)(?P<owner>[^/]+)/(?P<project_id>[^/.]+)"
        )
        match = re.match(pattern, url)
        repo = None
        if match:
            repo = cls(
                owner=match.group("owner"),
                project_id=match.group("project_id"),
                url=url,
            )
        return repo

    def projectUrl(self) -> str:
        """Return a browsable HTTPS project URL derived from the remote URL."""
        ssh = re.match(r"git@(?P<host>[^:]+):(?P<path>.+?)(?:\.git)?$", self.url)
        if ssh:
            url = f"https://{ssh.group('host')}/{ssh.group('path')}"
        else:
            url = re.sub(r"\.git$", "", self.url)
        return url

    def getIssueRecords(self, limit: int = None, **params) -> List[Dict]:
        """Not implemented for generic repos."""
        raise NotImplementedError(
            f"getIssueRecords is not supported for generic repo '{self.projectUrl()}'"
        )
