"""Created on 2024-08-27.

@author: wf
"""

import os
import unittest

from osprojects.osproject import GitHubRepo, OsProject, OsProjects
from tests.basetest import BaseTest


class TestGitHub(BaseTest):
    """Tests GitHub class."""

    def setUp(self, debug=True, profile=True):
        BaseTest.setUp(self, debug=debug, profile=profile)

    def test_GitHubRepo_from_url(self):
        """Tests the creating GitHubRepos from the project url."""
        urlCases = [
            {
                "owner": "WolfgangFahl",
                "project": "pyOpenSourceProjects",
                "variants": [
                    "https://github.com/WolfgangFahl/pyOpenSourceProjects",
                    "http://github.com/WolfgangFahl/pyOpenSourceProjects",
                    "git@github.com:WolfgangFahl/pyOpenSourceProjects",
                ],
            },
            {
                "owner": "ad-freiburg",
                "project": "qlever",
                "variants": ["https://github.com/ad-freiburg/qlever"],
            },
        ]
        for urlCase in urlCases:
            urlVariants = urlCase["variants"]
            expectedOwner = urlCase["owner"]
            expectedProject = urlCase["project"]
            for url in urlVariants:
                github_repo = GitHubRepo.from_url(url)
                self.assertEqual(expectedOwner, github_repo.owner)
                self.assertEqual(expectedProject, github_repo.project_id)

    def testOsProjects(self):
        """Tests the list_projects_as_os_projects method."""
        owner = "WolfgangFahl"
        project_id = "pyOpenSourceProjects"
        osprojects = OsProjects.from_owners([owner])

        debug = self.debug
        # debug = True
        if debug:
            index = 0
            for owner, projects in osprojects.projects.items():
                for project in projects:
                    index += 1
                    print(f"{index:3}:{owner}:{project}")
        self.assertTrue(owner in osprojects.projects)
        projects = osprojects.projects[owner]
        self.assertIsInstance(projects, dict)
        self.assertTrue(len(projects) > 0, "No projects found for WolfgangFahl")
        # Check if pyOpenSourceProjects is in the list
        self.assertTrue(project_id in projects)
        pyosp_found = projects[project_id]
        self.assertTrue(
            pyosp_found, "pyOpenSourceProjects not found in the list of projects"
        )

        # Test a sample project's structure
        sample_project = projects["py-yprinciple-gen"]
        expected_attributes = {
            "project_id",
            "owner",
            "title",
            "url",
            "description",
            "language",
            "created_at",
            "updated_at",
            "stars",
            "forks",
        }
        self.assertTrue(
            all(hasattr(sample_project, attr) for attr in expected_attributes),
            "OsProject instance is missing expected attributes",
        )

        # Check if all items are OsProject instances
        self.assertTrue(
            all(isinstance(project, OsProject) for project in projects.values()),
            "Not all items are OsProject instances",
        )

    @unittest.skipIf(
        BaseTest.inPublicCI(),
        "Tests querying wikidata which is often blocked on public CI",
    )
    def test_projects_from_folder(self):
        """Test projects from a specific folder."""
        debug = self.debug
        # debug=True
        home_dir = os.path.expanduser("~")
        folder_path = os.path.join(home_dir, "py-workspace")
        osprojects = OsProjects.from_folder(folder_path)
        count = len(osprojects.local_projects)
        if debug:
            print(f"found {count} local projects")
        self.assertTrue(count > 30)
        pass
