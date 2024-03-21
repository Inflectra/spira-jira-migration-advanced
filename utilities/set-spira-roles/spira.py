import requests
from urllib3.exceptions import InsecureRequestWarning
import json
from urllib.parse import urlparse
import urllib.parse
from typing import Dict

# Disable the warnings when https verify is off, instead only warn once in console on higher level
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)  # type: ignore


class Spira:
    def __init__(self, base_url, basic_auth, verify=True):
        if base_url[-1] == "/":
            self.base_url = base_url
        else:
            self.base_url = base_url + "/"

        self.host = urlparse(base_url).netloc

        self.verify = verify

        self.construct_base_header(basic_auth)

    def construct_base_header(self, basic_auth):
        self.headers = {
            "Host": self.host,
            "username": basic_auth[0],
            "api-key": basic_auth[1],
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    def add_user_with_role_to_project(self, project_id, body):
        add_user_and_role_url = self.base_url + "projects/" + str(project_id) + "/users"

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            add_user_and_role_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )

        return response

    def update_user_with_role_to_project(self, project_id, body):
        update_user_and_role_url = (
            self.base_url + "projects/" + str(project_id) + "/users"
        )

        payload = json.dumps(body)

        response = requests.request(
            "PUT",
            update_user_and_role_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )

        return response

    def remove_user_with_role_from_project(self, project_id, user_id):
        remove_user_with_role_from_project_url = (
            self.base_url + "projects/" + str(project_id) + "/users/" + str(user_id)
        )

        response = requests.request(
            "DELETE",
            remove_user_with_role_from_project_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response

    def create_user(
        self,
        body,
        project_id=None,
        project_role_id=None,
        password=None,
        password_question=None,
        password_answer=None,
    ):
        params = {
            "password": password,
            "password_question": password_question,
            "password_answer": password_answer,
            "project_id": project_id,
            "project_role_id": project_role_id,
        }
        create_user_url = self.base_url + "users?" + urllib.parse.urlencode(params)
        payload = json.dumps(body)

        response = requests.request(
            "POST",
            create_user_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )

        return response

    def get_all_users(self, include_inactive=True, start_row=1, number_rows=5000):
        params = {
            "include_inactive": include_inactive,
            "start_row": start_row,
            "number_rows": number_rows,
        }
        get_all_users_url = (
            self.base_url + "users/all?" + urllib.parse.urlencode(params)
        )

        response = requests.request(
            "GET", get_all_users_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_all_project_users(self, project_id):
        get_all_project_users_url = (
            self.base_url + "projects/" + str(project_id) + "/users"
        )

        response = requests.request(
            "GET", get_all_project_users_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_all_project_roles(self):
        get_all_project_roles_url = self.base_url + "project-roles"

        response = requests.request(
            "GET", get_all_project_roles_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_projects(self) -> Dict:
        get_projects_url = self.base_url + "projects"

        response = requests.request(
            "GET", get_projects_url, headers=self.headers, verify=self.verify
        )

        return response.json()
