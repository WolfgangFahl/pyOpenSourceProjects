'''
Created on 2022-01-24

@author: wf
'''
import unittest
from tests.basetest import BaseTest
from osprojects.osproject import OsProject, Commit, Ticket

class TestOsProject(BaseTest):
    '''
    test the OsProject concepts
    '''


    def testOsProject(self):
        '''
        tests if the projects details, commits and issues/tickets are correctly queried
        '''
        osProject=OsProject(owner="WolfgangFahl", id="pyOpenSourceProjects")
        tickets=osProject.getAllTickets()
        self.assertTrue(len(tickets)>=2)
        commit=Commit()
        ticket=Ticket()
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()