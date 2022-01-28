'''
Created on 2022-01-24

@author: wf
'''
import io
import unittest
from contextlib import redirect_stdout
from tests.basetest import BaseTest
from osprojects.osproject import OsProject, Commit, Ticket, main, GitHub


class TestOsProject(BaseTest):
    '''
    test the OsProject concepts
    '''


    def testOsProject(self):
        '''
        tests if the projects details, commits and issues/tickets are correctly queried
        '''
        osProject=self.getSampleById(OsProject,"id", "pyOpenSourceProjects")
        tickets=osProject.getAllTickets()
        expectedTicket=self.getSampleById(Ticket, "number", 2)
        expectedTicket.project=osProject
        self.assertDictEqual(expectedTicket.__dict__, tickets[1].__dict__)
        commit=Commit()
        ticket=Ticket()
        pass

    def testCmdLine(self):
        """
        tests cmdline of osproject
        """
        testParams=[
            ["-o", "WolfgangFahl", "-p", "pyOpenSourceProjects", "-ts", "github"],
            ["--repo"],
        ]
        for params in testParams:
            f = io.StringIO()
            with redirect_stdout(f):
                main(params)
            f.seek(0)
            output=f.read()
            self.assertTrue(len(output.split("\n"))>=2) # test number of Tickets
            self.assertIn("{{Ticket", output)

class TestGitHub(BaseTest):
    """
    tests GitHub class
    """

    def testResolveProjectUrl(self):
        """
        tests the resolving of the project url
        """
        urlVariants=[
            "https://github.com/WolfgangFahl/pyOpenSourceProjects",
            "http://github.com/WolfgangFahl/pyOpenSourceProjects",
            "git@github.com:WolfgangFahl/pyOpenSourceProjects"
        ]
        urlVariants=[*urlVariants, *[f"{u}.git" for u in urlVariants]]
        for url in urlVariants:
            owner, project = GitHub.resolveProjectUrl(url)
            self.assertEqual("WolfgangFahl", owner)
            self.assertEqual("pyOpenSourceProjects", project)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()