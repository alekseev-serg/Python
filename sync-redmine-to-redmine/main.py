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


@dataclass
class Data:
    issues: list[Issue] = field(default_factory=list)


class ReaderRedmine:

    def __init__(self, conf: ReaderConfig):
        self.data = None
        self.project_name = conf.name_project_r
        self.url_redmine = conf.url_r
        self.token_redmine = conf.password
        self.redmine = Redmine(conf.url_r, username=conf.login, password=conf.password)
        self.date_from = conf.data_from
        self.date_to = conf.date_to
        self.id_r = conf.users['id_r']
        self.priority_id = {id_r: id_w for id_r, id_w in
                            zip(conf.priority['priority_id_r'], conf.priority['priority_id_w'])}
        self.status_id = {id_r: id_w for id_r, id_w in zip(conf.status['status_id_r'], conf.status['status_id_w'])}
        # self.issues = self.redmine.issue.filter(project_id=project_name, updated_on=f'><{date_from}|{date_to}',
        #                                         status_id="*")
        self.time_entries_list = [self.redmine.time_entry.filter(project_id=conf.name_project_r,
                                                                 from_date=conf.data_from,
                                                                 user_id=user_id
                                                                 ) for user_id in self.id_r]
        logger.info("Start read redmine")

    def add_data_timelog(self, issue: Issue, timelog):
        issue.timelog.append(Timelog(timelog_id=timelog.id,
                                     author=timelog.user.id,
                                     date_started=timelog.spent_on.strftime("%Y-%m-%d"),
                                     date_updated=timelog.updated_on.strftime("%Y-%m-%d"),
                                     timespent=timelog.hours,
                                     comment=f"{timelog.id} - {timelog.comments}"
                                     )
                             )

    def add_data_issues(self, issues: list, time_entries):
        for time_entry in time_entries:
            for issue in issues:
                if issue.issue_id == time_entry.issue.id:
                    self.add_data_timelog(issue, time_entry)
                    break

            issue = self.redmine.issue.get(time_entry.issue.id)
            issue_data = Issue(issue_id=issue.id,
                               name=issue.id,
                               summary=f"{issue.id} - {issue.subject}",
                               date_created=issue.created_on.strftime("%Y-%m-%d"),
                               author=issue.author.id,
                               priority_id=self.priority_id.get(issue.priority.id),
                               status_id=self.status_id.get(issue.status.id),
                               issuetype_id=issue.tracker.id,
                               progress=issue.done_ratio,
                               description=issue.description
                               )
            self.add_data_timelog(issue_data, time_entry)
            issues.append(issue_data)

    @logger.catch
    def get_data(self) -> Data:
        issues = []

        for time_entries in self.time_entries_list:
            self.add_data_issues(issues, time_entries)

        self.data = Data(issues=issues)
        return self.data


class RedmineWriter:

    def __init__(self, conf: ReaderConfig):
        self.project_name = conf.name_project_w
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
                    self.update_issue(issue, find_issue.id)
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
                # user_id=self.users.get(timelog.author)
            )

    def update_time_entry(self, timelog: Timelog, id_time_entry: int):
        with self.redmine.session(key=self.tokens[timelog.author]):
            self.redmine.time_entry.update(
                resource_id=id_time_entry,
                spent_on=timelog.date_started,
                hours=timelog.timespent,
                comments=timelog.comment,
                # user_id=self.users.get(timelog.author)
            )

    def update_issue(self, issue: Issue, id_issue: int):
        project_id = self.project_name
        if self.sub_project_name:
            project_id = self.sub_project_name
        # with self.redmine.session(key=self.tokens.get(issue.author)):
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

    def create_issue(self, issue: Issue):
        # with self.redmine.session(
        #         key=self.token_redmine if not issue.author in self.tokens else self.tokens.get(issue.author)):
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
def syncotoilurzm():
    from config.config import confProject

    read = ReaderRedmine(confProject)
    read.get_data()
    print(read.data)

    if read.data.issues is not None:
        w = RedmineWriter(confProject)
        w.transfer_issue(read.data)
    else:
        print("Not time entries")


if __name__ == "__main__":
    import uvicorn

    config = uvicorn.Config("main:app", host="0.0.0.0", port=8001, reload=True, log_level="info")
    server = uvicorn.Server(config)
    server.run()
