'''
Created on 2022-01-24

@author: wf
'''
from __future__ import annotations
import datetime
import re
import subprocess
import sys
from typing import Type

import requests
import json


class TicketSystem(object):
    """
    platform for hosting OpenSourceProjects and their issues
    """

    @classmethod
    def getIssues(self, project, **kwargs):
        """
        get issues from the TicketSystem for a project
        """
        return NotImplemented

    @staticmethod
    def projectUrl(project):
        """
        url of the project
        """
        return NotImplemented

    @staticmethod
    def ticketUrl(project):
        """
        url of the ticket/issue list
        """
        return NotImplemented

class GitHub(TicketSystem):
    """
    wrapper for the GitHub api
    """

    @classmethod
    def getIssues(cls, project, **params):
        payload = {}
        headers = {}
        issues = []
        nextResults = True
        params["per_page"] = 100
        params["page"] = 1
        while nextResults:
            response = requests.request("GET", GitHub.ticketUrl(project), headers=headers, data=payload, params=params)
            issue_records = json.loads(response.text)
            for record in issue_records:
                tr = {
                    "project": project,
                    "title": record.get('title'),
                    "createdAt": record.get('created_at'),
                    "closedAt": record.get('closed_at'),
                    "state": record.get('state'),
                    "number": record.get('number'),
                    "url": record.get('url'),
                }
                issues.append(Ticket.init_from_dict(**tr))
            if len(issue_records) < 100:
                nextResults = False
            else:
                params["page"] += 1
        return issues

    @staticmethod
    def projectUrl(project):
        return f"https://api.github.com/repos/{project.owner}/{project.id}"

    @staticmethod
    def ticketUrl(project):
        return f"{GitHub.projectUrl(project)}/issues"

    @staticmethod
    def resolveProjectUrl(url:str) -> (str, str):
        """
        Resolve project url to owner and project name

        Returns:
            (owner, project)
        """
        pattern = r"((https?:\/\/github\.com\/)|(git@github\.com:))(?P<owner>\w+)\/(?P<project>\w+)(\.git)?"
        match=re.match(pattern=pattern, string=url)
        owner=match.group("owner")
        project=match.group("project")
        if owner and project:
            return owner, project



class Jira(TicketSystem):
    """
    wrapper for Jira api
    """


class OsProject(object):
    '''
    an Open Source Project
    '''

    def __init__(self, owner:str, id:str, ticketSystem:Type[TicketSystem]=GitHub):
        '''
        Constructor
        '''
        self.owner=owner
        self.id=id
        self.ticketSystem=ticketSystem

    @staticmethod
    def getSamples():
        samples=[
            {
                "id":"pyOpenSourceProjects",
                "state":"",
                "owner":"WolfgangFahl",
                "title":"pyOpenSourceProjects",
                "url":"https://github.com/WolfgangFahl/pyOpenSourceProjects",
                "version":"",
                "desciption":"Helper Library to organize open source Projects",
                "date":datetime.datetime(year=2022, month=1, day=24),
                "since":"",
                "until":"",
            }
        ]
        return samples

    @staticmethod
    def fromUrl(url=str) -> OsProject:
        if "github.com" in url:
            owner, project = GitHub.resolveProjectUrl(url)
            if owner and project:
                return OsProject(owner=owner, id=project, ticketSystem=GitHub)
        raise Exception(f"Could not resolve the url '{url}' to a OsProject object")

    def getIssues(self, **params) -> list:
        return self.ticketSystem.getIssues(self, **params)

    def getAllTickets(self, **params):
        """
        Get all Tickets of the project closed ond open ones
        """
        return self.getIssues(state='all', **params)
        
class Ticket(object):
    '''
    a Ticket
    '''

    @staticmethod
    def getSamples():
        samples=[
            {
                "number":2,
                "title":"Get Tickets in Wiki notation from github API",
                "createdAt": datetime.datetime(year=2022, month=1, day=24, hour=7, minute=41, second=29),
                "closedAt": None,  # Not closed yet
                "url":"https://github.com/WolfgangFahl/pyOpenSourceProjects/issues/1",
                "project":"pyOpenSourceProjects",
                "state":"closed"
            }
        ]
        return samples

    @classmethod
    def init_from_dict(cls, **records):
        """
        inits Ticket from given args
        """
        issue = Ticket()
        for k, v in records.items():
            setattr(issue, k, v)
        return issue

    def toWikiMarkup(self) -> str:
        """
        Returns Ticket in wiki markup
        """
        return f"* {{{{Ticket|number={self.number}|title={self.title}|project={self.project.id}|state={self.state}}}}}"
    
class Commit(object):
    '''
    a commit
    '''


def main(_argv=None):
    import argparse

    parser = argparse.ArgumentParser(description='Issue2ticket')
    parser.add_argument('-o', '--owner', help='project owner or organization')
    parser.add_argument('-p', '--project', help='name of the project')
    parser.add_argument('--repo',action='store_true' , help='get needed information form repository of current location')
    parser.add_argument('-ts', '--ticketsystem', default="github", choices=["github", "jira"], help='platform the project is hosted')
    parser.add_argument('-s', '--state', choices=["open", "closed", "all"], default="all", help='only issues with the given state')

    args = parser.parse_args(args=_argv)
    # resolve ticketsystem
    ticketSystem=GitHub
    if args.ticketsystem == "jira":
        ticketSystem=Jira
    if args.repo:
        url=subprocess.check_output(["git","config", "--get", "remote.origin.url"])
        url=url.decode().strip("\n")
        osProject=OsProject.fromUrl(url)
    elif args.project and args.owner:
        osProject = OsProject(owner=args.owner, id=args.project, ticketSystem=ticketSystem)
    else:
        print("Project information must either be provided with --owner and --project or --repo.")
        sys.exit(0)
    tickets = osProject.getIssues(state=args.state)
    print('\n'.join([t.toWikiMarkup() for t in tickets]))

if __name__ == '__main__':
    sys.exit(main())
