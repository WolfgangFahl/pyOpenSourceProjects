"""
Created on 2022-01-24

@author: wf
"""

import unittest

from osprojects.osproject import Commit, OsProject, Ticket, gitlog2wiki, main
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
