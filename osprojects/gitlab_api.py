"""Created on 2026-03-16.

@author: wf
"""

import re
from dataclasses import dataclass
from typing import Optional

from osprojects.git_api import GenericRepo


@dataclass
class GitLabRepo(GenericRepo):
    """Represents a GitLab repository.

    Attributes:
        owner (str): The owner/namespace of the repository.
        project_id (str): The name/id of the repository.
        url (str): The original remote URL.
    """

    @classmethod
    def from_url(cls, url: str) -> Optional["GitLabRepo"]:
        """Parse owner and project_id from a GitLab remote URL.

        Args:
            url: SSH or HTTPS GitLab remote URL.

        Returns:
            GitLabRepo instance or None if the URL cannot be parsed.
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
