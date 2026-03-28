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
        # Match HTTPS: https://host/owner/repo
        https_pattern = r"https?://[^/]+/(?P<owner>[^/]+)/(?P<project_id>[^/.]+)"
        match = re.match(https_pattern, url)

        if not match:
            # Match SSH: [user@]host:path - extract last two path components as owner/repo
            ssh_pattern = r"(?:[^@]+@)?[^:]+:(?P<path>.+?)(?:\.git)?$"
            ssh_match = re.match(ssh_pattern, url)
            if ssh_match:
                path = ssh_match.group("path")
                # Split path and take last two components
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2:
                    owner = parts[-2]
                    project_id = parts[-1]
                    repo = cls(owner=owner, project_id=project_id, url=url)
                    return repo

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
        # Match SSH URLs: user@host:path or host:path
        ssh = re.match(r"(?:[^@]+@)?(?P<host>[^:]+):(?P<path>.+?)(?:\.git)?$", self.url)
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
