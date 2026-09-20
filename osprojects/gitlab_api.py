"""Created on 2026-03-16.

@author: wf
"""

from dataclasses import dataclass
from typing import ClassVar

from osprojects.git_api import GenericRepo


@dataclass
class GitLabRepo(GenericRepo):
    """Represents a GitLab repository.

    Attributes:
        owner (str): The owner/namespace of the repository.
        project_id (str): The name/id of the repository.
        url (str): The original remote URL.
    """

    forge: ClassVar[str] = "GitLab"
