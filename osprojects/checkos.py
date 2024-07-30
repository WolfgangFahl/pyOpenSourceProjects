#!/usr/bin/env python
"""
Created on 2024-07-30

@author: wf
"""
import argparse
import os

from osprojects.osproject import GitHub, OsProject


class CheckOS:
    """
    check the open source projects
    """

    def __init__(self, workspace: str):
        self.workspace = workspace

    def marker(self, state: bool) -> str:
        return "✅" if state else "❌"

    def check(self, project: OsProject, verbose: bool = True):
        project_path = os.path.join(self.workspace, project.id)
        marker = self.marker(os.path.exists(project_path))
        if verbose:
            print(f"{project}: {marker}")
        return marker


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
        "-ws",
        "--workspace",
        help="(Eclipse) workspace directory",
        default=os.path.expanduser("~/py-workspace"),
    )

    args = parser.parse_args(args=_argv)
    checker = CheckOS(workspace=args.workspace)

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

    for project in projects:
        checker.check(project)


if __name__ == "__main__":
    main()
