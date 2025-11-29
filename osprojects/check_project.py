"""Created on 2024-08-28.

@author: wf
"""

import os
import tomllib
from dataclasses import dataclass
from typing import List

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from packaging import version

# original at ngwidgets - use redundant local copy ...
from osprojects.editor import Editor
from osprojects.github_api import GitHubAction


@dataclass
class Check:
    ok: bool = False
    path: str = None
    msg: str = ""
    content: str = None

    @property
    def marker(self) -> str:
        return f"✅" if self.ok else f"❌"

    @classmethod
    def file_exists(cls, path) -> "Check":
        ok = os.path.exists(path)
        content = None
        if ok and os.path.isfile(path):
            with open(path, "r") as f:
                content = f.read()
        check = Check(ok, path, msg=path, content=content)
        return check


class CheckProject:
    """Checker for an individual open source project."""

    def __init__(self, parent, project, args):
        self.parent = parent
        self.project = project
        self.args = args
        self.checks: List[Check] = []
        self.project_path = project.folder
        self.project_name = None
        self.requires_python = None
        self.min_python_version_minor = None
        self.max_python_version_minor = 13  # python 3.13 is max version

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def ok_checks(self) -> List[Check]:
        ok_checks = [check for check in self.checks if check.ok]
        return ok_checks

    @property
    def failed_checks(self) -> List[Check]:
        failed_checks = [check for check in self.checks if not check.ok]
        return failed_checks

    def add_error(self, ex, path: str):
        self.parent.handle_exception(ex)
        self.add_check(False, msg=f"{str(ex)}", path=path)

    def add_check(
        self, ok, msg: str = "", path: str = None, negative: bool = False
    ) -> Check:
        if not path:
            raise ValueError("path parameter missing")
        marker = ""
        if negative:
            ok = not ok
            marker = "⚠ ️"
        check = Check(ok=ok, path=path, msg=f"{marker}{msg}{path}")
        self.checks.append(check)
        return check

    def add_content_check(
        self, content: str, needle: str, path: str, negative: bool = False
    ) -> Check:
        ok = needle in content
        check = self.add_check(ok, msg=f"{needle} in ", path=path, negative=negative)
        return check

    def add_path_check(self, path) -> Check:
        # Check if path exists
        path_exists = Check.file_exists(path)
        self.checks.append(path_exists)
        return path_exists

    def generate_badge_markdown(self) -> str:
        """Generate README.md badge table markup."""
        project_name = self.project_name
        owner = self.project.owner
        project_id = self.project.project_id

        markup= f"""| | |
    | :--- | :--- |
    | **PyPi** | [![PyPI Status](https://img.shields.io/pypi/v/{project_name}.svg)](https://pypi.python.org/pypi/{project_name}/) [![License](https://img.shields.io/github/license/{owner}/{project_id}.svg)](https://www.apache.org/licenses/LICENSE-2.0) [![pypi](https://img.shields.io/pypi/pyversions/{project_name})](https://pypi.org/project/{project_name}/) [![format](https://img.shields.io/pypi/format/{project_name})](https://pypi.org/project/{project_name}/) [![downloads](https://img.shields.io/pypi/dd/{project_name})](https://pypi.org/project/{project_name}/) |
    | **GitHub** | [![Github Actions Build](https://github.com/{owner}/{project_id}/actions/workflows/build.yml/badge.svg)](https://github.com/{owner}/{project_id}/actions/workflows/build.yml) [![Release](https://img.shields.io/github/v/release/{owner}/{project_id})](https://github.com/{owner}/{project_id}/releases) [![Contributors](https://img.shields.io/github/contributors/{owner}/{project_id})](https://github.com/{owner}/{project_id}/graphs/contributors) [![Last Commit](https://img.shields.io/github/last-commit/{owner}/{project_id})](https://github.com/{owner}/{project_id}/commits/) [![GitHub issues](https://img.shields.io/github/issues/{owner}/{project_id}.svg)](https://github.com/{owner}/{project_id}/issues) [![GitHub closed issues](https://img.shields.io/github/issues-closed/{owner}/{project_id}.svg)](https://github.com/{owner}/{project_id}/issues/?q=is%3Aissue+is%3Aclosed) |
    | **Code** | [![style-black](https://img.shields.io/badge/%20style-black-000000.svg)](https://github.com/psf/black) [![imports-isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/) |
    | **Docs** | [![API Docs](https://img.shields.io/badge/API-Documentation-blue)](https://{owner}.github.io/{project_id}/) [![formatter-docformatter](https://img.shields.io/badge/%20formatter-docformatter-fedcba.svg)](https://github.com/PyCQA/docformatter) [![style-google](https://img.shields.io/badge/%20style-google-3666d6.svg)](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) |"""
        return markup



    def check_local(self) -> Check:
        local = Check.file_exists(self.project_path)
        return local

    def check_github_workflows(self):
        """Check the github workflow files."""
        workflows_path = os.path.join(self.project_path, ".github", "workflows")
        workflows_exist = self.add_path_check(workflows_path)

        if workflows_exist.ok:
            required_files = ["build.yml", "upload-to-pypi.yml"]
            for file in required_files:
                file_path = os.path.join(workflows_path, file)
                file_exists = self.add_path_check(file_path)

                if file_exists.ok:
                    content = file_exists.content

                    if file == "build.yml":
                        min_python_version_minor = int(
                            self.requires_python.split(".")[-1]
                        )
                        self.add_check(
                            min_python_version_minor == self.min_python_version_minor,
                            msg=f"{min_python_version_minor} (build.yml)!={self.min_python_version_minor} (pyprojec.toml)",
                            path=file_path,
                        )
                        python_versions = f"""python-version: [ {', '.join([f"'3.{i}'" for i in range(self.min_python_version_minor, self.max_python_version_minor+1)])} ]"""
                        self.add_content_check(
                            content,
                            python_versions,
                            file_path,
                        )
                        self.add_content_check(
                            content,
                            "os: [ubuntu-latest, macos-latest, windows-latest]",
                            file_path,
                        )
                        self.add_content_check(
                            content, "uses: actions/checkout@v4", file_path
                        )
                        self.add_content_check(
                            content,
                            "uses: actions/setup-python@v5",
                            file_path,
                        )

                        self.add_content_check(
                            content, "sphinx", file_path, negative=True
                        )
                        scripts_ok = (
                            "scripts/install" in content
                            and "scripts/test" in content
                            or "scripts/installAndTest" in content
                        )
                        self.add_check(scripts_ok, "install and test", file_path)

                    elif file == "upload-to-pypi.yml":
                        self.add_content_check(content, "id-token: write", file_path)
                        self.add_content_check(
                            content, "uses: actions/checkout@v4", file_path
                        )
                        self.add_content_check(
                            content,
                            "uses: actions/setup-python@v5",
                            file_path,
                        )
                        self.add_content_check(
                            content,
                            "uses: pypa/gh-action-pypi-publish@release/v1",
                            file_path,
                        )

    def check_scripts(self):
        scripts_path = os.path.join(self.project_path, "scripts")
        scripts_exist = self.add_path_check(scripts_path)
        if scripts_exist.ok:
            required_files = ["blackisort", "test", "install", "doc", "release"]
            for file in required_files:
                file_path = os.path.join(scripts_path, file)
                file_exists = self.add_path_check(file_path)
                if file_exists.ok:
                    content = file_exists.content
                    if file == "doc":
                        self.add_content_check(
                            content, "sphinx", file_path, negative=True
                        )
                        self.add_content_check(
                            content, "WF 2024-07-30 - updated", file_path
                        )
                    if file == "test":
                        self.add_content_check(content, "WF 2024-08-03", file_path)
                    if file == "release":
                        self.add_content_check(content, "scripts/doc -d", file_path)

    def check_readme(self):
        readme_path = os.path.join(self.project_path, "README.md")
        readme_exists = self.add_path_check(readme_path)
        if not hasattr(self, "project_name"):
            self.add_check(
                False,
                "project_name from pyproject.toml needed for README.md check",
                self.project_path,
            )
            return
        if readme_exists.ok:
            readme_content = readme_exists.content
            badge_lines = [
                "[![pypi](https://img.shields.io/pypi/pyversions/{self.project_name})](https://pypi.org/project/{self.project_name}/)",
                "[![Github Actions Build](https://github.com/{self.project.fqid}/actions/workflows/build.yml/badge.svg)](https://github.com/{self.project.fqid}/actions/workflows/build.yml)",
                "[![PyPI Status](https://img.shields.io/pypi/v/{self.project_name}.svg)](https://pypi.python.org/pypi/{self.project_name}/)",
                "[![GitHub issues](https://img.shields.io/github/issues/{self.project.fqid}.svg)](https://github.com/{self.project.fqid}/issues)",
                "[![GitHub closed issues](https://img.shields.io/github/issues-closed/{self.project.fqid}.svg)](https://github.com/{self.project.fqid}/issues/?q=is%3Aissue+is%3Aclosed)",
                "[![API Docs](https://img.shields.io/badge/API-Documentation-blue)](https://{self.project.owner}.github.io/{self.project.project_id}/)",
                "[![License](https://img.shields.io/github/license/{self.project.fqid}.svg)](https://www.apache.org/licenses/LICENSE-2.0)",
            ]
            for line in badge_lines:
                formatted_line = line.format(self=self)
                self.add_content_check(
                    content=readme_content,
                    needle=formatted_line,
                    path=readme_path,
                )
            self.add_content_check(
                readme_content, "readthedocs", readme_path, negative=True
            )

    def check_pyproject_toml(self) -> bool:
        """pyproject.toml."""
        toml_path = os.path.join(self.project_path, "pyproject.toml")
        toml_exists = self.add_path_check(toml_path)
        if toml_exists.ok:
            content = toml_exists.content
            toml_dict = tomllib.loads(content)
            project_check = self.add_check(
                "project" in toml_dict, "[project]", toml_path
            )
            if project_check.ok:
                self.project_name = toml_dict["project"]["name"]
                requires_python_check = self.add_check(
                    "requires-python" in toml_dict["project"],
                    "requires-python",
                    toml_path,
                )
                if requires_python_check.ok:
                    self.requires_python = toml_dict["project"]["requires-python"]
                    min_python_version = version.parse(
                        self.requires_python.replace(">=", "")
                    )
                    min_version_needed = "3.9"
                    version_ok = min_python_version >= version.parse(min_version_needed)
                    self.add_check(
                        version_ok, f"requires-python>={min_version_needed}", toml_path
                    )
                    self.min_python_version_minor = int(
                        str(min_python_version).split(".")[-1]
                    )
                    for minor_version in range(
                        self.min_python_version_minor, self.max_python_version_minor + 1
                    ):
                        needle = f"Programming Language :: Python :: 3.{minor_version}"
                        self.add_content_check(content, needle, toml_path)
            self.add_content_check(content, "hatchling", toml_path)
            self.add_content_check(
                content, "[tool.hatch.build.targets.wheel.sources]", toml_path
            )
        return toml_exists.ok

    def check_git(self) -> bool:
        """Check git repository information using GitHub class.

        Returns:
            bool: True if git owner matches project owner and the repo is not a fork
        """
        owner_match = False
        is_fork = False
        try:
            local_owner = self.project.owner
            remote_owner = self.project.repo_info["owner"]["login"]
            is_fork = self.project.repo_info["fork"]
            owner_match = local_owner.lower() == remote_owner.lower() and not is_fork
            self.add_check(
                owner_match,
                f"Git owner ({remote_owner}) matches project owner ({local_owner}) and is not a fork",
                self.project_path,
            )

            local_project_id = self.project.project_id
            remote_repo_name = self.project.repo_info["name"]
            repo_match = local_project_id.lower() == remote_repo_name.lower()
            self.add_check(
                repo_match,
                f"Git repo name ({remote_repo_name}) matches project id ({local_project_id})",
                self.project_path,
            )

            # Check if there are uncommitted changes (this still requires local git access)
            local_repo = Repo(self.project_path)
            self.add_check(
                not local_repo.is_dirty(), "uncomitted changes for", self.project_path
            )

            # Check latest GitHub Actions workflow run
            latest_run = GitHubAction.get_latest_workflow_run(self.project)
            if latest_run:
                self.add_check(
                    latest_run["conclusion"] == "success",
                    f"Latest GitHub Actions run: {latest_run['conclusion']}",
                    latest_run["html_url"],
                )
            else:
                self.add_check(
                    False,
                    "No GitHub Actions runs found",
                    self.project.repo.ticketUrl(),
                )

        except InvalidGitRepositoryError:
            self.add_check(False, "Not a valid git repository", self.project_path)
        except NoSuchPathError:
            self.add_check(
                False, "Git repository path does not exist", self.project_path
            )
        except Exception as ex:
            self.add_error(ex, self.project_path)

        return owner_match and not is_fork

    def check(self, title: str):
        """Check the given project and print results."""
        self.check_local()
        self.check_git()
        if self.check_pyproject_toml():
            self.check_github_workflows()
            self.check_readme()
            self.check_scripts()

        # ok_count=len(ok_checks)
        failed_count = len(self.failed_checks)
        summary = (
            f"❌ {failed_count:2}/{self.total:2}"
            if failed_count > 0
            else f"✅ {self.total:2}/{self.total:2}"
        )
        print(f"{title}{summary}:{self.project}→{self.project.url}")
        if failed_count > 0:
            # Sort checks by path
            sorted_checks = sorted(self.checks, key=lambda c: c.path or "")

            # Group checks by path
            checks_by_path = {}
            for check in sorted_checks:
                if check.path not in checks_by_path:
                    checks_by_path[check.path] = []
                checks_by_path[check.path].append(check)

            # Display results
            for path, path_checks in checks_by_path.items():
                path_failed = sum(1 for c in path_checks if not c.ok)
                if path_failed > 0 or self.args.debug:
                    print(f"❌ {path}: {path_failed}")
                    i = 0
                    for check in path_checks:
                        show = not check.ok or self.args.debug
                        if show:
                            i += 1
                            print(f"    {i:3}{check.marker}:{check.msg}")

                    if self.args.editor and path_failed > 0:
                        if os.path.isfile(path):
                            # @TODO Make editor configurable
                            Editor.open(path, default_editor_cmd="/usr/local/bin/atom")
                        else:
                            Editor.open_filepath(path)
