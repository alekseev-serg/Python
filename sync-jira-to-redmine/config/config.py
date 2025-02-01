from dataclasses import dataclass
import datetime


@dataclass
class ReaderConfig:
    users: dict
    # id_r: list
    # users_rw: dict
    priority: dict
    status: dict
    login: str
    password: str
    token_w: str
    redmine_id_w: str
    url_r: str
    url_w: str = "https://url-remine"
    date_to: datetime = datetime.date.today()
    date_from: datetime = (date_to - datetime.timedelta(days=31))
    name_project: str = None
    sub_name_project: str = None
    jql: str = None


confProject = ReaderConfig(url_r="https://url-jira",
                            login="",
                            password="",
                            jql='''worklogAuthor in (login, login, login, login)''',
                            # Дата с первого дня месяца
                            date_from=(datetime.date.today().replace(day=1)),

                            # Берём из api jira https://url-jira/rest/api/latest/priority
                            priority={
                                "priority_id_r": ["1", "2", "3", "4", "5"],
                                "priority_id_w": [7, 6, 5, 4, 3]
                            },
                            # Так же берём из api jira https://url-jira/rest/api/latest/status
                            status={"status_id_r": ["3"],
                                    "status_id_w": [3]
                                    },

                            # Название проекта в нашем редмайне https://url-remine/projects/
                            name_project="external-portfolio",
                            sub_name_project="external-portfolio",

                            # Токен и id пользователя от которого будут создаваться задачи в нашем редмайне
                            token_w="token-redmine",  #
                            redmine_id_w="584",  #

                            users={"id_r": ["login",
                                            "login",
                                            "login",
                                            "login",
                                            ],

                                   "id_w": [720, 1002, 893, 938],
                                   "token": ["token-redmine",
                                             "token-redmine",
                                             "token-redmine",
                                             "token-redmine"
                                             ]
                                   }
                            )
