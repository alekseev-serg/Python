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
    url_w: str = "https://url-redmine"
    date_to: datetime = datetime.date.today()
    data_from: datetime = (date_to - datetime.timedelta(days=31))
    name_project_r: str = None
    name_project_w: str = None
    sub_name_project: str = None
    jql: str = None


confProject = ReaderConfig(url_r="https://external-redmine-project",
                           login="login",  # данные для авторизации в redmine заказчика
                           password="pass",
                           data_from=(datetime.date.today() - datetime.timedelta(days=10)),
                           priority={
                               "priority_id_r": [1, 2, 3, 4, 5],
                               "priority_id_w": [7, 6, 5, 4, 3]
                           },
                           status={"status_id_r": [3],
                                   "status_id_w": [3]
                                   },
                           name_project_r="",  # название проекта в redmine заказчика
                           name_project_w="external-project",  # название проекта в нашем redmine
                           token_w="",  # Токен в нашем redmine
                           redmine_id_w="307",  # id в нашем redmine
                           users={"id_r": [1510, 1509],
                                  "id_w": [1043, 914],
                                  "token": ["token-redmine",
                                            "token-redmine",
                                            ]
                                  }
                           )
