"""Created on 2026-09-20.

@author: wf
"""

from dataclasses import dataclass
from typing import ClassVar, Dict, List, Tuple

import requests

from osprojects.git_api import GenericRepo


@dataclass
class ForgejoRepo(GenericRepo):
    """Represents a Forgejo repository.

    Forgejo serves its own badges under <project>/badges/... and runs
    Forgejo Actions from .forgejo/workflows. The API of a Forgejo instance
    may be restricted to signed in users, so all checks work without it.

    Attributes:
        owner (str): The owner/organization of the repository.
        project_id (str): The name/id of the repository.
        url (str): The original remote URL.
    """

    forge: ClassVar[str] = "Forgejo"
    workflows_dir: ClassVar[str] = ".forgejo/workflows"
    required_workflows: ClassVar[Tuple[str, ...]] = ("build.yml",)
    os_needle: ClassVar[str] = "runs-on: ubuntu-latest"

    # host -> is a Forgejo instance
    host_cache: ClassVar[Dict[str, bool]] = {}

    @classmethod
    def is_forgejo_host(cls, host: str, timeout: float = 5.0) -> bool:
        """Check whether the given host runs Forgejo.

        Hosts named after the forge are accepted without a request. Other
        hosts are probed once for the Forgejo specific API path which answers
        with a status of its own (200 open, 401/403 restricted) where any
        other forge answers 404.

        Args:
            host: the host name of the git remote
            timeout: seconds to wait for the probe

        Returns:
            True if the host runs Forgejo
        """
        is_forgejo = False
        if "forgejo" in host or "codeberg" in host:
            is_forgejo = True
        elif host in cls.host_cache:
            is_forgejo = cls.host_cache[host]
        else:
            try:
                response = requests.get(
                    f"https://{host}/api/forgejo/v1/version", timeout=timeout
                )
                is_forgejo = response.status_code in (200, 401, 403)
            except requests.RequestException:
                is_forgejo = False
            cls.host_cache[host] = is_forgejo
        return is_forgejo

    def badge_url(self, badge: str) -> str:
        """The URL of a badge served by the Forgejo instance.

        Args:
            badge: the badge path e.g. issues/open.svg

        Returns:
            the badge URL
        """
        url = f"{self.projectUrl()}/badges/{badge}"
        return url

    def badge_lines(self, project_name: str) -> List[str]:
        """The badge markdown lines a README.md of a Forgejo project must
        contain.

        Args:
            project_name: the name of the python package

        Returns:
            list of badge markdown lines
        """
        project_url = self.projectUrl()
        badge_lines = [
            f"[![Forgejo Actions Build]({self.badge_url('workflows/build.yml/badge.svg')})]({project_url}/actions)",
            f"[![Release]({self.badge_url('release.svg')})]({project_url}/releases)",
            f"[![Open issues]({self.badge_url('issues/open.svg')})]({project_url}/issues)",
            f"[![Closed issues]({self.badge_url('issues/closed.svg')})]({project_url}/issues?state=closed)",
            f"[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)]({project_url}/src/branch/main/LICENSE)",
        ]
        return badge_lines

    def badge_markdown(self, project_name: str) -> str:
        """The badge table markdown for a README.md of a Forgejo project.

        Args:
            project_name: the name of the python package

        Returns:
            markdown of the badge table
        """
        lines = self.badge_lines(project_name)
        markup = f"""| | |
| :--- | :--- |
| **Forgejo** | {" ".join(lines[0:4])} |
| **License** | {lines[4]} |
| **Code** | [![style-black](https://img.shields.io/badge/%20style-black-000000.svg)](https://github.com/psf/black) [![imports-isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/) |
| **Docs** | [![formatter-docformatter](https://img.shields.io/badge/%20formatter-docformatter-fedcba.svg)](https://github.com/PyCQA/docformatter) [![style-google](https://img.shields.io/badge/%20style-google-3666d6.svg)](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) |"""
        return markup
