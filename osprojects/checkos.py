#!/usr/bin/env python
"""
Created on 2024-07-30

@author: wf
"""
from dataclasses import dataclass
import argparse
from argparse import Namespace
import os
from typing import List

from osprojects.osproject import GitHub, OsProject

@dataclass
class Check:
    ok: bool=False
    msg: str=""

    @property
    def marker(self) -> str:
        return f"✅ {self.msg}" if self.ok else f"❌  {self.msg}"

class CheckOS:
    """
    check the open source projects
    """

    def __init__(self, args:Namespace,project:OsProject):
        self.args=args
        self.verbose= args.verbose
        self.workspace = args.workspace
        self.project=project
        self.project_path = os.path.join(self.workspace, project.id)


    def check_local(self)->Check:
        local=Check(ok=os.path.exists(self.project_path),msg=f"{self.project_path}")
        return local

    def check_readme(self) -> List[Check]:
        checks=[]
        readme_path = os.path.join(self.project_path, "README.md")
        readme_exists=Check(ok=os.path.exists(readme_path),msg=readme_path)
        checks.append(readme_exists)
        if readme_exists.ok:
            with open(readme_path, "r") as readme_file:
                readme_content = readme_file.read()
                badge_lines = [
                "[![pypi](https://img.shields.io/pypi/pyversions/{self.project.id})](https://pypi.org/project/{self.project.id}/)",
                "[![Github Actions Build](https://github.com/{self.project.fqid}/actions/workflows/build.yml/badge.svg)](https://github.com/{self.project.fqid}/actions/workflows/build.yml)",
                "[![PyPI Status](https://img.shields.io/pypi/v/{self.project.id}.svg)](https://pypi.python.org/pypi/{self.project.id}/)",
                "[![GitHub issues](https://img.shields.io/github/issues/{self.project.fqid}.svg)](https://github.com/{self.project.fqid}/issues)",
                "[![GitHub closed issues](https://img.shields.io/github/issues-closed/{self.project.fqid}.svg)](https://github.com/{self.project.fqid}/issues/?q=is%3Aissue+is%3Aclosed)",
                "[![API Docs](https://img.shields.io/badge/API-Documentation-blue)](https://{self.project.fqid}.github.io/{self.project.id}/)",
                "[![License](https://img.shields.io/github/license/{self.project.fqid}.svg)](https://www.apache.org/licenses/LICENSE-2.0)"
            ]
            for line in badge_lines:
                formatted_line = line.format(self=self)
                checks.append(Check(ok=formatted_line in readme_content, msg=formatted_line))


        return checks

    def check(self) -> List[Check]:
        """
        Check the given project and print results
        """
        checks = []
        checks.append(self.check_local())
        checks.extend(self.check_readme())

        ok_checks = [check for check in checks if check.ok]
        not_ok_checks = [check for check in checks if not check.ok]

        print(f"{self.project} ✅: {len(ok_checks)}/❌: {len(not_ok_checks)} {self.project.url}")

        sorted_checks = ok_checks + not_ok_checks

        for i,check in enumerate(sorted_checks):
            print(f"    {i+1:3}{check.marker}:{check.msg}")
        return checks

def main(_argv=None):
    """
    main command line entry point
    """
    parser = argparse.ArgumentParser(description="Check open source projects")
    parser.add_argument(
        "-o", "--owner", help="project owner or organization", required=True
    )
    parser.add_argument("-p", "--project", help="name of the project")
    parser.add_argument("-l", "--language", help="filter projects by language")
    parser.add_argument(
        "--local", action="store_true", help="check only locally available projects"
    )
    parser.add_argument(
        "-v","--verbose", action="store_true", help="show verbose output"
    )
    parser.add_argument(
        "-ws",
        "--workspace",
        help="(Eclipse) workspace directory",
        default=os.path.expanduser("~/py-workspace"),
    )

    args = parser.parse_args(args=_argv)

    github = GitHub()
    if args.project:
        # Check specific project
        projects = [
            github.list_projects_as_os_projects(args.owner, project_name=args.project)
        ]
    else:
        # Check all projects
        projects = github.list_projects_as_os_projects(args.owner)

    if args.language:
        projects = [p for p in projects if p.language == args.language]

    if args.local:
        local_projects = []
        for project in projects:
            checker = CheckOS(args=args,project=project)
            if checker.check_local().ok:
                local_projects.append(project)
        projects=local_projects


    for project in projects:
        checker = CheckOS(args=args,project=project)
        checker.check()

if __name__ == "__main__":
    main()
