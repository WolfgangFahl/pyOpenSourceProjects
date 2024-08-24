"""
Created on 2022-01-24

@author: wf
"""

import unittest

from osprojects.osproject import Commit, GitHub, OsProject, Ticket, gitlog2wiki, main
from tests.basetest import BaseTest


class TestOsProject(BaseTest):
    """
    test the OsProject concepts
    """

    def testOsProject(self):
        """
        tests if the projects details, commits and issues/tickets are correctly queried
        """
        osProject = OsProject(owner="WolfgangFahl",project_id="pyOpenSourceProjects")
        tickets = osProject.getAllTickets()
        expectedTicket = self.getSampleById(Ticket, "number", 2)
        expectedTicket.project = osProject
        comparison_ticket_dict = tickets[-2].__dict__
        comparison_ticket_dict.pop("body", None)
        self.assertDictEqual(expectedTicket.__dict__, comparison_ticket_dict)
        commit = Commit()
        ticket = Ticket()
        pass

    def testGetCommits(self):
        """
        tests extraction of commits for a repository
        """
        if self.inPublicCI():
            return
        osProject = OsProject(owner="WolfgangFahl",project_id="pyOpenSourceProjects")
        commits = osProject.getCommits()
        expectedCommit = self.getSampleById(Commit, "hash", "106254f")
        self.assertTrue(len(commits) > 15)
        self.assertDictEqual(expectedCommit.__dict__, commits[0].__dict__)

    def testCmdLine(self):
        """
        tests cmdline of osproject
        """
        testParams = [
            ["-o", "WolfgangFahl", "-p", "pyOpenSourceProjects", "-ts", "github"],
            ["--repo"],
        ]
        for params in testParams:
            output = self.captureOutput(main, params)
            self.assertTrue(len(output.split("\n")) >= 2)  # test number of Tickets
            self.assertIn("{{Ticket", output)

    def testGitlog2IssueCmdline(self):
        """
        tests gitlog2issue
        """
        if self.inPublicCI():
            return
        commit = self.getSampleById(Commit, "hash", "106254f")
        expectedCommitMarkup = commit.toWikiMarkup()
        output = self.captureOutput(gitlog2wiki)
        outputLines = output.split("\n")
        self.assertTrue(expectedCommitMarkup in outputLines)


class TestGitHub(BaseTest):
    """
    tests GitHub class
    """

    def testResolveProjectUrl(self):
        """
        tests the resolving of the project url
        """
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
                giturl = f"{url}.git"
                github=GitHub()
                owner, project = github.resolveProjectUrl(giturl)
                self.assertEqual(expectedOwner, owner)
                self.assertEqual(expectedProject, project)

    def testListProjects(self):
        """
        tests the list_projects_as_os_projects method
        """
        owner = "WolfgangFahl"
        github = GitHub()

        # Test list_projects_as_os_projects
        projects = github.list_projects_as_os_projects(owner)
        debug = self.debug
        #debug = True
        if debug:
            for project in projects:
                print(project)
        self.assertIsInstance(projects, list)
        self.assertTrue(len(projects) > 0, "No projects found for WolfgangFahl")

        # Check if pyOpenSourceProjects is in the list
        pyosp_found = any(project.project_id == "pyOpenSourceProjects" for project in projects)
        self.assertTrue(
            pyosp_found, "pyOpenSourceProjects not found in the list of projects"
        )

        # Test a sample project's structure
        sample_project = projects[0]
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
            all(isinstance(project, OsProject) for project in projects),
            "Not all items are OsProject instances",
        )

        # Test a sample OsProject
        sample_os_project = projects[0]
        self.assertEqual(sample_os_project.owner, owner)
        self.assertIsInstance(sample_os_project.project_id, str)
        self.assertIsInstance(sample_os_project.ticketSystem, GitHub)

    def testGetSpecificProject(self):
        """
        tests getting a specific project
        """
        owner = "WolfgangFahl"
        project_name = "pyOpenSourceProjects"
        github = GitHub()

        project = github.list_projects_as_os_projects(owner, project_name=project_name)[
            0
        ]
        self.assertIsInstance(project, OsProject)
        self.assertEqual(project.project_id, project_name)
        self.assertEqual(project.owner, owner)
        self.assertIsInstance(project.ticketSystem, GitHub)


class TestCommit(BaseTest):
    """
    Tests Commit class
    """

    def testToWikiMarkup(self):
        """
        tests toWikiMarkup
        """
        commit = self.getSampleById(Commit, "hash", "106254f")
        expectedMarkup = "{{commit|host=https://github.com/WolfgangFahl/pyOpenSourceProjects|path=|project=pyOpenSourceProjects|subject=Initial commit|name=GitHub|date=2022-01-24 07:02:55+01:00|hash=106254f|storemode=subobject|viewmode=line}}"
        self.assertEqual(expectedMarkup, commit.toWikiMarkup())


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
