#!/usr/bin/env python
"""Created on 2024-07-30.

@author: wf
"""
import argparse
import logging
import os
import traceback
from argparse import Namespace

from osprojects.check_project import CheckProject
from osprojects.osproject import OsProjects


class CheckOS:
    """Checker for a set of open source projects."""

    def __init__(
        self, args: Namespace, osprojects: OsProjects, max_python_version_minor=12
    ):
        self.args = args
        self.verbose = args.verbose
        self.workspace = args.workspace
        self.osprojects = osprojects
        self.checks = []
        # python 3.12 is max version
        self.max_python_version_minor = max_python_version_minor

    @classmethod
    def from_args(cls, args: Namespace):
        osprojects = OsProjects.from_folder(args.workspace, with_progress=True)
        return cls(args, osprojects)

    def select_projects(self):
        try:
            if self.args.project:
                if self.args.owners:
                    return self.osprojects.select_projects(
                        owners=self.args.owners, project_id=self.args.project
                    )
                elif self.args.local:
                    return self.osprojects.select_projects(
                        project_id=self.args.project, local_only=True
                    )
                else:
                    raise ValueError("--local or --owner needed with --project")
            elif self.args.owners:
                return self.osprojects.select_projects(owners=self.args.owners)
            elif self.args.local:
                return self.osprojects.select_projects(local_only=True)
            else:
                raise ValueError(
                    "Please provide --owner and --project, or use --local option."
                )
        except ValueError as e:
            print(f"Error: {str(e)}")
            return []

    def filter_projects(self):
        if self.args.language:
            self.osprojects.filter_projects(language=self.args.language)
        if self.args.local:
            self.osprojects.filter_projects(local_only=True)

    def check_projects(self):
        """Select, filter, and check all projects based on the provided
        arguments."""
        self.select_projects()
        self.filter_projects()

        for i, (_url, project) in enumerate(
            self.osprojects.selected_projects.items(), 1
        ):
            checker = CheckProject(self, project, self.args)
            checker.check(f"{i:3}:")
            if self.args.badges:
                print(checker.generate_badge_markdown())


    def handle_exception(self, ex: Exception):
        CheckOS.show_exception(ex, self.args.debug)

    @staticmethod
    def show_exception(ex: Exception, debug: bool = False):
        err_msg = f"Error: {str(ex)}"
        logging.error(err_msg)
        if debug:
            print(traceback.format_exc())


def main(_argv=None):
    """Main command line entry point."""
    parser = argparse.ArgumentParser(description="Check open source projects")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="add debug output",
    )
    parser.add_argument(
        "-b",
        "--badges",
        action="store_true",
        help="create and output standard README.md badges markup",
    )
    parser.add_argument(
        "-e",
        "--editor",
        action="store_true",
        help="open default editor on failed files",
    )
    parser.add_argument("-o", "--owners", nargs="+", help="project owners")
    parser.add_argument("-p", "--project", help="name of the project")
    parser.add_argument("-l", "--language", help="filter projects by language")
    parser.add_argument(
        "--local", action="store_true", help="check only locally available projects"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show verbose output"
    )
    parser.add_argument(
        "-ws",
        "--workspace",
        help="(Eclipse) workspace directory",
        default=os.path.expanduser("~/py-workspace"),
    )

    args = parser.parse_args(args=_argv)

    try:
        checker = CheckOS.from_args(args)
        checker.check_projects()
    except Exception as ex:
        CheckOS.show_exception(ex, debug=args.debug)
        raise ex


if __name__ == "__main__":
    main()
