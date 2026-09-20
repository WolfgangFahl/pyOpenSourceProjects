"""Created on 2026-09-20.

@author: wf
"""

import os
import tempfile
from argparse import Namespace

from osprojects.check_project import CheckProject
from osprojects.forgejo_api import ForgejoRepo
from osprojects.git_api import GenericRepo
from osprojects.github_api import GitHubRepo
from osprojects.osproject import OsProject, OsProjects
from tests.basetest import BaseTest


class TestForgejo(BaseTest):
    """Test Forgejo hosted projects."""

    ssh_url = "ssh://git@forgejo.example.org/Owner/project.git"
    scp_url = "git@forgejo.example.org:Owner/project.git"
    https_url = "https://forgejo.example.org/Owner/project"

    def test_parse_url(self):
        """Test parsing of scheme based and scp like remote URLs."""
        for url in [self.ssh_url, self.scp_url, self.https_url]:
            with self.subTest(url=url):
                parsed = GenericRepo.parse_url(url)
                self.assertEqual("forgejo.example.org", parsed["host"])
                self.assertEqual("Owner", parsed["owner"])
                self.assertEqual("project", parsed["project_id"])
                repo = GenericRepo.from_url(url)
                self.assertEqual(self.https_url, repo.projectUrl())
        self.assertIsNone(GenericRepo.parse_url("not a url"))

    def test_repo_of_url(self):
        """Test the selection of the repo class by forge."""
        github_repo = OsProject.repo_of_url(
            "git@github.com:WolfgangFahl/pyOpenSourceProjects.git"
        )
        self.assertIsInstance(github_repo, GitHubRepo)
        forgejo_repo = OsProject.repo_of_url(self.ssh_url)
        self.assertIsInstance(forgejo_repo, ForgejoRepo)
        self.assertEqual("Forgejo", forgejo_repo.forge)
        self.assertEqual(".forgejo/workflows", forgejo_repo.workflows_dir)

    def test_badges(self):
        """Test the Forgejo badge lines and table."""
        repo = ForgejoRepo.from_url(self.ssh_url)
        badge_lines = repo.badge_lines("project")
        self.assertEqual(5, len(badge_lines))
        self.assertIn(
            f"{self.https_url}/badges/workflows/build.yml/badge.svg", badge_lines[0]
        )
        os_project = OsProject.of_repo(repo)
        args = Namespace(badges=True, debug=False, editor=False)
        checker = CheckProject(parent=None, project=os_project, args=args)
        checker.project_name = "project"
        markup = checker.generate_badge_markdown()
        self.assertIn("| **Forgejo** |", markup)
        for badge_line in badge_lines:
            self.assertIn(badge_line, markup)
        self.assertNotIn("github.com/Owner", markup)

    def test_from_folder(self):
        """Test the registration of a local Forgejo project from a workspace
        folder without any API call."""
        with tempfile.TemporaryDirectory() as workspace:
            git_dir = os.path.join(workspace, "project", ".git")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "config"), "w") as config_file:
                config_file.write(f'[remote "origin"]\n\turl = {self.ssh_url}\n')
            osp = OsProjects.from_folder(workspace, project_id="project")
            self.assertEqual(1, len(osp.local_projects))
            project = osp.local_projects[self.https_url]
            self.assertEqual("Owner", project.owner)
            self.assertEqual(self.https_url, project.url)
            self.assertFalse(project.repo_info["fork"])
            selected = osp.select_projects(project_id="project", local_only=True)
            self.assertEqual(1, len(selected))
            osp.clear_selection()
            selected = osp.select_projects(owners=["Owner"], project_id="project")
            self.assertEqual(1, len(selected))
