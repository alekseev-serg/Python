import datetime
from dataclasses import dataclass, field
from redminelib import Redmine
from jira import JIRA
import os
import json
from loguru import logger
from fastapi import FastAPI
import subprocess
from config.config import ReaderConfig

# load_dotenv()
logger.add('python.log', format="{time} {level} {message}", retention="5 days", rotation="100 MB")

# Create `FastAPI` application
app = FastAPI()


@dataclass
class Timelog:
    timelog_id: int = None
    author: str = None
    date_started: str = None
    date_updated: str = None
    timespent: int = 0
    comment: str = None


@dataclass
class Issue:
    timelog: list[Timelog] = field(default_factory=list)
    issue_id: str = None
    name: str = None
    summary: str = None
    date_created: str = None
    author: str = None
    priority_id: int = 4
    status_id: int = 1
    issuetype_id: int = 0
    time_estimate_seconds: int = 0
    time_spent_seconds: int = 0
    progress: int = 0
    description: str = None
    fixed_version_id: int = 0


@dataclass
class Data:
    issues: list[Issue] = field(default_factory=list)


class ReaderJira:

    @logger.catch
    def __init__(self, conf: ReaderConfig):
        self.data = None
        self.url_jira = conf.url_r
        self.login_jira = conf.login
        self.pass_jira = conf.password
        self.jira = JIRA(options={'server': conf.url_r}, basic_auth=(conf.login, conf.password))
        self.issues = self.jira.search_issues(conf.jql, maxResults=10000)
        self.date_from = conf.date_from
        self.users_rw = {id_r: id_w for id_r, id_w in zip(conf.users['id_r'], conf.users['id_w'])}
        self.id_r = conf.users['id_r']
        self.status_id = {id_r: id_w for id_r, id_w in zip(conf.status['status_id_r'], conf.status['status_id_w'])}
        logger.info("Start read jira")

    def add_data_timelog(self, worklogs) -> list[Timelog]:
        comment = 'None'
        timelogs_data = []
        author_wl = ''
        for w in worklogs:

            if hasattr(w.author, 'name'):
                if not self.users_rw.get(w.author.name):
                    continue
                author_wl = w.author.name

            # if hasattr(w.author, 'emailAddress'):
            #     if not self.users_rw.get(w.author.emailAddress.split('@')[0]):
            #         continue
            #     author_wl = w.author.emailAddress.split('@')[0]

            elif hasattr(w.author, 'accountId'):
                if not self.users_rw.get(w.author.accountId):
                    continue
                author_wl = w.author.accountId

            date_worklog_updated = w.updated.split('T')[0]
            date_worklog_started = w.started.split('T')[0]
            print(date_worklog_started)
            print(self.date_from.strftime('%Y-%m-%d'))
            if date_worklog_started < self.date_from.strftime('%Y-%m-%d'):
                continue

            if hasattr(w, 'comment'):
                comment = w.comment

            time_spent = w.timeSpentSeconds / 3600
            timelogs_data.append(Timelog(timelog_id=w.id,
                                         author=author_wl,
                                         date_started=date_worklog_started,
                                         date_updated=date_worklog_updated,
                                         timespent=time_spent,
                                         comment=f"{w.id} - {comment}"
                                         )
                                 )

        return timelogs_data

    @logger.catch
    def get_data(self) -> Data:
        issues_data = []
        for issue in self.issues:
            progress = 0
            # estimate_seconds = 0
            # time_spent_seconds = 0
            worklogs = self.jira.worklogs(issue.key)
            # if worklogs:
            # estimate_seconds = 0 if issue.fields.timeestimate is None else issue.fields.timeestimate
            # time_spent_seconds = 0 if issue.fields.timespent is None else issue.fields.timespent

            date_issue_created = issue.fields.created.split('T')

            timelog = self.add_data_timelog(worklogs)
            if timelog == []:
                continue

            author = self.login_jira
            if hasattr(issue.fields.assignee, 'name'):
                if issue.fields.assignee.name in self.id_r:
                    author = issue.fields.assignee.name
            elif hasattr(issue.fields.assignee, 'emailAddress'):
                if issue.fields.assignee.emailAddress in self.id_r:
                    author = issue.fields.assignee.emailAddress.split('@')[0]
            elif hasattr(issue.fields.assignee, 'accountId'):
                if issue.fields.assignee.accountId in self.id_r:
                    author = issue.fields.assignee.accountId
            elif not timelog:
                continue

            status = 1
            if self.status_id.get(issue.fields.status.statusCategory.id):
                status = 3

            fixed_version_id = None
            print(issue.fields)
            if hasattr(issue.fields, 'fixed_version'):
                fixed_version_id = issue.fields.fixed_version.id

            issues_data.append(Issue(timelog=timelog,
                                     issue_id=issue.id,
                                     name=issue.key,
                                     summary=f"{issue.key} - {issue.fields.summary}",
                                     date_created=date_issue_created[0],
                                     author=author,
                                     priority_id=4,
                                     status_id=status,
                                     issuetype_id=issue.fields.issuetype.id,
                                     # time_estimate_seconds=round(estimate_seconds / 3600, 1),
                                     # time_spent_seconds=round(time_spent_seconds / 3600, 1),
                                     progress=progress,
                                     description=issue.fields.description,
                                     fixed_version_id=fixed_version_id
                                     )
                               )

            print(f"Add - {issue}, S - {status}, T - {len(timelog)}")
        self.data = Data(issues=issues_data)
        return self.data


class RedmineWriter:

    def __init__(self, conf: ReaderConfig):
        self.project_name = conf.name_project
        self.sub_project_name = conf.sub_name_project
        self.url_redmine = conf.url_w
        self.redmine_id_w = conf.redmine_id_w
        self.users_redmine = conf.users
        self.redmine = Redmine(self.url_redmine, key=conf.token_w)
        self.issues = self.redmine.issue.filter(project_id=self.project_name)
        self.users = {id_r: id_w for id_r, id_w in zip(self.users_redmine['id_r'], self.users_redmine['id_w'])}
        self.tokens = {id_r: token for id_r, token in zip(self.users_redmine['id_r'], self.users_redmine['token'])}
        logger.info("Start write redmine")

    @logger.catch
    def transfer_issue(self, data: Data):

        for issue in data.issues:
            for find_issue in self.redmine.issue.filter(project_id=self.project_name, status_id='*'):
                if issue.summary == find_issue.subject:
                    fixed_version = None
                    if hasattr(find_issue, "fixed_version"):
                        fixed_version = find_issue.fixed_version.id
                    self.update_issue(issue, find_issue.id, fixed_version)
                    break
            else:
                self.create_issue(issue)

    def create_time_entry(self, timelog: Timelog, id_issue: int):
        with self.redmine.session(key=self.tokens[timelog.author]):
            self.redmine.time_entry.create(
                issue_id=id_issue,
                spent_on=timelog.date_started,
                hours=float(timelog.timespent),
                comments=timelog.comment,
            )

    def update_time_entry(self, timelog: Timelog, id_time_entry: int):
        with self.redmine.session(key=self.tokens[timelog.author]):
            self.redmine.time_entry.update(
                resource_id=id_time_entry,
                spent_on=timelog.date_started,
                hours=timelog.timespent,
                comments=timelog.comment,
            )

    def update_issue(self, issue: Issue, id_issue: int, fixed_version_id):
        project_id = self.project_name
        if self.sub_project_name:
            project_id = self.sub_project_name

        version_status = 'open'
        if fixed_version_id:
            version = self.redmine.version.get(fixed_version_id)

            if version.status == 'closed':
                self.redmine.version.update(fixed_version_id, status='open')
                version_status = 'closed'

            if version.status == 'locked':
                self.redmine.version.update(fixed_version_id, status='open')
                version_status = 'locked'

        self.redmine.issue.update(
            project_id=project_id,
            resource_id=id_issue,
            subject=issue.summary,
            description=issue.description,
            status_id=issue.status_id,
            priority_id=issue.priority_id,
            done_ratio=issue.progress,
        )

        time_entries = self.redmine.time_entry.filter(issue_id=id_issue)

        for td in issue.timelog:
            for tr in time_entries:
                print(td.date_started, tr.spent_on)
                if str(td.timelog_id) in str(tr.comments):
                    if td.timespent != tr.hours:
                        self.update_time_entry(td, tr.id)
                    elif td.date_started != tr.spent_on:
                        self.update_time_entry(td, tr.id)
                    break
            else:
                self.create_time_entry(td, id_issue)

        if fixed_version_id:
            self.redmine.version.update(fixed_version_id, status=version_status)

    def create_issue(self, issue: Issue):
        issue_created = self.redmine.issue.create(
            project_id=self.project_name,
            subject=issue.summary,
            description=issue.description,
            status_id=issue.status_id,
            priority_id=issue.priority_id,
            assigned_to_id=self.users.get(issue.author) if self.users.get(issue.author) else self.redmine_id_w,
            start_date=issue.date_created,
            estimated_hours=issue.time_estimate_seconds,
            done_ratio=issue.progress,
        )
        for t in issue.timelog:
            self.create_time_entry(t, issue_created.id)


@app.get('/api/v1/activate/project')
def syncFSK():
    from config.config import confProject

    read = ReaderJira(confProject)
    read.get_data()

    if read.data is not None:
        w = RedmineWriter(confProject)
        w.transfer_issue(read.data)
    else:
        print("Not time entries")



if __name__ == "__main__":
    import uvicorn

    config = uvicorn.Config("main:app", host="0.0.0.0", port=8001, reload=True, log_level="info")
    server = uvicorn.Server(config)
    server.run()
