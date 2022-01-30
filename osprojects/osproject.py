'''
Created on 2022-01-24

@author: wf
'''
from __future__ import annotations
import datetime
import re
import subprocess
import sys
import requests
import json
from typing import Type, List
from dateutil.parser import parse


class TicketSystem(object):
    """
    platform for hosting OpenSourceProjects and their issues
    """

    @classmethod
    def getIssues(self, project:OsProject, **kwargs) -> List[Ticket]:
        """
        get issues from the TicketSystem for a project
        """
        return NotImplemented

    @staticmethod
    def projectUrl(project:OsProject):
        """
        url of the project
        """
        return NotImplemented

    @staticmethod
    def ticketUrl(project:OsProject):
        """
        url of the ticket/issue list
        """
        return NotImplemented

    @staticmethod
    def commitUrl(project: OsProject, id:str):
        """
        url of the ticket/issue list
        """
        return NotImplemented

class GitHub(TicketSystem):
    """
    wrapper for the GitHub api
    """

    @classmethod
    def getIssues(cls, project:OsProject, **params) -> List[Ticket]:
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
                    "createdAt": parse(record.get('created_at')) if record.get('created_at') else "",
                    "closedAt":  parse(record.get('closed_at')) if record.get('closed_at') else "",
                    "state": record.get('state'),
                    "number": record.get('number'),
                    "url": f"{cls.projectUrl(project)}/issues/{record.get('number')}",
                }
                issues.append(Ticket.init_from_dict(**tr))
            if len(issue_records) < 100:
                nextResults = False
            else:
                params["page"] += 1
        return issues

    @staticmethod
    def projectUrl(project:OsProject):
        return f"https://github.com/{project.owner}/{project.id}"

    @staticmethod
    def ticketUrl(project:OsProject):
        return f"https://api.github.com/repos/{project.owner}/{project.id}/issues"

    @staticmethod
    def commitUrl(project:OsProject, id:str):
        return f"{GitHub.projectUrl(project)}/commit/{id}"

    @staticmethod
    def resolveProjectUrl(url:str) -> (str, str):
        """
        Resolve project url to owner and project name

        Returns:
            (owner, project)
        """
        # https://www.rfc-editor.org/rfc/rfc3986#appendix-B
        pattern = r"((https?:\/\/github\.com\/)|(git@github\.com:))(?P<owner>[^/?#]+)\/(?P<project>[^\./?#]+)(\.git)?"
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

    def __init__(self, owner:str=None, id:str=None, ticketSystem:Type[TicketSystem]=GitHub):
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

    @classmethod
    def fromRepo(cls):
        """
        Init OsProject from repo in current working directory
        """
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"])
        url = url.decode().strip("\n")
        osProject = cls.fromUrl(url)
        return osProject

    @classmethod
    def fromUrl(cls, url:str) -> OsProject:
        """
        Init OsProject from given url
        """
        if "github.com" in url:
            owner, project = GitHub.resolveProjectUrl(url)
            if owner and project:
                return OsProject(owner=owner, id=project, ticketSystem=GitHub)
        raise Exception(f"Could not resolve the url '{url}' to a OsProject object")

    def getIssues(self, **params) -> list:
        tickets=self.ticketSystem.getIssues(self, **params)
        tickets.sort(key=lambda r: getattr(r, "number"), reverse=True)
        return tickets

    def getAllTickets(self, **params):
        """
        Get all Tickets of the project closed ond open ones
        """
        return self.getIssues(state='all', **params)

    def getCommits(self) -> List[Commit]:
        commits=[]
        gitlogCmd=['git', '--no-pager', 'log', '--reverse', r'--pretty=format:{"name":"%cn","date":"%cI","hash":"%h"}']
        gitLogCommitSubject=['git', 'log', '--format=%s', '-n', '1']
        rawCommitLogs=subprocess.check_output(gitlogCmd).decode()
        for rawLog in rawCommitLogs.split("\n"):
            log=json.loads(rawLog)
            if log.get("date", None) is not None:
                log["date"]=datetime.datetime.fromisoformat(log["date"])
            log["project"]=self.id
            log["host"]=self.ticketSystem.projectUrl(self)
            log["path"] = ""
            log["subject"] = subprocess.check_output([*gitLogCommitSubject, log["hash"]])[:-1].decode() # seperate query to avoid json escaping issues
            commit=Commit()
            for k,v in log.items():
                setattr(commit, k, v)
            commits.append(commit)
        return commits


class Ticket(object):
    '''
    a Ticket
    '''

    @staticmethod
    def getSamples():
        samples=[
            {
                "number":2,
                "title": "Get Tickets in Wiki notation from github API",
                "createdAt": datetime.datetime.fromisoformat("2022-01-24 07:41:29+00:00"),
                "closedAt": datetime.datetime.fromisoformat("2022-01-25 07:43:04+00:00"),
                "url": "https://github.com/WolfgangFahl/pyOpenSourceProjects/issues/2",
                "project": "pyOpenSourceProjects",
                "state": "closed"
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
        return f"""# {{{{Ticket
|number={self.number}
|title={self.title}
|project={self.project.id}
|createdAt={self.createdAt if self.createdAt else ""}
|closedAt={self.closedAt if self.closedAt else ""}
|state={self.state}
}}}}"""
    
class Commit(object):
    '''
    a commit
    '''

    @staticmethod
    def getSamples():
        samples=[
            {
                "host":"https://github.com/WolfgangFahl/pyOpenSourceProjects",
                "path": "",
                "project": "pyOpenSourceProjects",
                "subject": "Initial commit",
                "name": "GitHub",  #TicketSystem
                "date": datetime.datetime.fromisoformat("2022-01-24 07:02:55+01:00"),
                "hash": "106254f"
            }
        ]
        return samples

    def toWikiMarkup(self):
        """
        Returns Commit as wiki markup
        """
        params=[f"{attr}={getattr(self, attr, '')}" for attr in self.getSamples()[0].keys()]
        markup=f"{{{{commit|{'|'.join(params)}|storemode=subobject|viewmode=line}}}}"
        return markup

def gitlog2wiki(_argv=None):
    """
    cmdline interface to get gitlog entires in wiki markup
    """
    osProject = OsProject.fromRepo()
    commits=osProject.getCommits()
    print('\n'.join([c.toWikiMarkup() for c in commits]))



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
    if args.project and args.owner:
        osProject = OsProject(owner=args.owner, id=args.project, ticketSystem=ticketSystem)
    else:
        osProject = OsProject.fromRepo()
    tickets = osProject.getIssues(state=args.state)
    print('\n'.join([t.toWikiMarkup() for t in tickets]))

if __name__ == '__main__':
    #sys.exit(main())
    sys.exit(gitlog2wiki())