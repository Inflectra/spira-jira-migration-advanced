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

    # Get all tasks the current user owns
    def get_tasks(self) -> Dict:
        get_tasks_url = self.base_url + "tasks"

        response = requests.request(
            "GET", get_tasks_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    # Get all tasks created from a certain date
    def get_all_tasks(
        self,
        project_id,
        start_row=1,
        number_of_rows=100000,
        creation_date="2020-01-01T00:00:00.000",
    ):
        params = {
            "start_row": start_row,
            "number_of_rows": number_of_rows,
            "creation_date": creation_date,
        }

        get_all_tasks_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/tasks/new?"
            + urllib.parse.urlencode(params)
        )

        response = requests.request(
            "GET", get_all_tasks_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    # Get all task types
    def get_task_types(self, project_template_id) -> Dict:
        get_task_types_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/tasks/types"
        )

        response = requests.request(
            "GET", get_task_types_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    # Create a new task on the supplied project with the supplied task body
    def create_task(self, project_id, body) -> Dict:
        new_task_url = self.base_url + "projects/" + str(project_id) + "/tasks"

        payload = json.dumps(body)

        response = requests.request(
            "POST", new_task_url, headers=self.headers, data=payload, verify=self.verify
        )

        return response.json()

    def get_requirement_types(self, project_template_id) -> Dict:
        get_requirement_types_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/requirements/types"
        )

        response = requests.request(
            "GET", get_requirement_types_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    # Create a new requirement
    def create_requirement(self, project_id, body) -> Dict:
        new_requirement_url = (
            self.base_url + "projects/" + str(project_id) + "/requirements"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_requirement_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    # Create a new requirement
    def create_child_requirement(self, project_id, parentid, body) -> Dict:
        new_requirement_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/requirements/parent/"
            + str(parentid)
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_requirement_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    # Get all requirements
    def get_all_requirements(self, project_id, starting_row=1, number_of_rows=100000):
        params = {"starting_row": starting_row, "number_of_rows": number_of_rows}

        get_all_requirements_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/requirements?"
            + urllib.parse.urlencode(params)
        )

        response = requests.request(
            "GET", get_all_requirements_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    # Get all incident types
    def get_incident_types(self, project_template_id) -> Dict:
        get_incident_types_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/incidents/types"
        )

        response = requests.request(
            "GET", get_incident_types_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    # Create a new incident
    def create_incident(self, project_id, body) -> Dict:
        new_incident_url = self.base_url + "projects/" + str(project_id) + "/incidents"

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_incident_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    # Create a new release
    def create_release(self, project_id, body) -> Dict:
        new_releases_url = self.base_url + "projects/" + str(project_id) + "/releases"

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_releases_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    # Create a new child release
    def create_child_release(self, project_id, parent_id, body) -> Dict:
        new_parent_releases_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/releases/"
            + str(parent_id)
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_parent_releases_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    # Create a new component
    def create_component(self, project_id, body) -> Dict:
        new_component_url = (
            self.base_url + "projects/" + str(project_id) + "/components"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_component_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    # Create a new customlist at project template level
    def create_project_template_customlist(self, project_template_id, body) -> Dict:
        new_customlist_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/custom-lists"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_customlist_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    # Create a new customlist at system level
    def create_system_customlist(self, body) -> Dict:
        new_system_customlist_url = self.base_url + "/system/custom-lists"

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_system_customlist_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    # Create a incidents
    def get_all_incidents(
        self,
        project_id,
        start_row=1,
        number_rows=100000,
        creation_date="2020-01-01T00:00:00.000",
    ):
        params = {
            "start_row": start_row,
            "number_rows": number_rows,
            "creation_date": creation_date,
        }

        get_all_incidents_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/incidents/recent?"
            + urllib.parse.urlencode(params)
        )

        response = requests.request(
            "GET", get_all_incidents_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    # Create a new task comment
    def create_task_comment(self, project_id, task_id, body) -> Dict:
        new_task_comment_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/tasks/"
            + str(task_id)
            + "/comments"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_task_comment_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )

        return response.json()

    # Create a new incident comment
    def create_incident_comment(self, project_id, incident_id, body) -> Dict:
        new_incident_comment_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/incidents/"
            + str(incident_id)
            + "/comments"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_incident_comment_url,
            headers=self.headers,
            data="[" + payload + "]",
            verify=self.verify,
        )

        return response.json()

    # Create a new requirement comment
    def create_requirement_comment(self, project_id, requirement_id, body) -> Dict:
        new_requirement_comment_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/requirements/"
            + str(requirement_id)
            + "/comments"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            new_requirement_comment_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )

        return response.json()

    def get_all_document_folders(self, project_id) -> Dict:
        get_all_document_folders = (
            self.base_url + "projects/" + str(project_id) + "/document-folders"
        )

        response = requests.request(
            "GET",
            get_all_document_folders,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def add_document_folder(self, project_id, body) -> Dict:
        add_document_folder_url = (
            self.base_url + "projects/" + str(project_id) + "/document-folders"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            add_document_folder_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    def delete_document_folder(self, project_id, folder_id) -> Dict:
        delete_document_folder_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/document-folders/"
            + str(folder_id)
        )

        response = requests.request(
            "DELETE",
            delete_document_folder_url,
            headers=self.headers,
            verify=self.verify,
        )
        return response.json()

    def get_all_documents(self, project_id) -> Dict:
        get_all_documents_url = (
            self.base_url + "projects/" + str(project_id) + "/documents"
        )

        response = requests.request(
            "GET",
            get_all_documents_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_document(self, project_id, document_id) -> Dict:
        get_all_documents_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/documents/"
            + str(document_id)
        )

        response = requests.request(
            "GET",
            get_all_documents_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def add_document(self, project_id, body) -> Dict:
        add_document_url = (
            self.base_url + "projects/" + str(project_id) + "/documents/file"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            add_document_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        return response.json()

    def add_artifact_document_association(
        self, project_id, artifact_type_id, artifact_id, document_id
    ) -> Dict:
        attach_document_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/artifact-types/"
            + str(artifact_type_id)
            + "/artifacts/"
            + str(artifact_id)
            + "/documents/"
            + str(document_id)
        )

        response = requests.request(
            "POST",
            attach_document_url,
            headers=self.headers,
            verify=self.verify,
        )
        return response.json()

    def remove_artifact_document_association(
        self, project_id, artifact_type_id, artifact_id, document_id
    ) -> Dict:
        detach_document_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/artifact-types/"
            + str(artifact_type_id)
            + "/artifacts/"
            + str(artifact_id)
            + "/documents/"
            + str(document_id)
        )

        response = requests.request(
            "DELETE",
            detach_document_url,
            headers=self.headers,
            verify=self.verify,
        )
        return response.json()

    def delete_document(self, project_id, document_id) -> Dict:
        delete_document_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/documents/"
            + str(document_id)
        )

        response = requests.request(
            "DELETE",
            delete_document_url,
            headers=self.headers,
            verify=self.verify,
        )
        return response.json()

    def get_projects(self) -> Dict:
        get_projects_url = self.base_url + "projects"

        response = requests.request(
            "GET", get_projects_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_all_project_templates(self):
        get_all_project_templates_url = self.base_url + "project-templates"

        response = requests.request(
            "GET",
            get_all_project_templates_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_project_template(self, project_template_id):
        get_project_template_url = (
            self.base_url + "project-templates/" + str(project_template_id)
        )

        response = requests.request(
            "GET", get_project_template_url, headers=self.headers, verify=self.verify
        )

        return response.json()

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

    def get_project_template_custom_properties(
        self, project_template_id, artifact_type_name
    ):
        get_project_template_custom_properties_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/custom-properties/"
            + artifact_type_name
        )

        response = requests.request(
            "GET",
            get_project_template_custom_properties_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_project_template_custom_lists(self, project_template_id):
        get_project_template_custom_list_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/custom-lists"
        )

        response = requests.request(
            "GET",
            get_project_template_custom_list_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_project_template_custom_list_values(self, project_template_id, list_id):
        get_project_template_custom_list_values_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/custom-lists/"
            + str(list_id)
        )

        response = requests.request(
            "GET",
            get_project_template_custom_list_values_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_system_level_custom_lists(self):
        get_system_level_custom_lists_url = self.base_url + "/system/custom-lists"

        response = requests.request(
            "GET",
            get_system_level_custom_lists_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_system_level_custom_list_values(self, list_id):
        get_system_level_custom_list_values_url = (
            self.base_url + "/system/custom-lists/" + str(list_id)
        )

        response = requests.request(
            "GET",
            get_system_level_custom_list_values_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_all_releases(self, project_id, active_only=False):
        params = {"active_only": active_only}

        get_all_releases_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/releases?"
            + urllib.parse.urlencode(params)
        )

        response = requests.request(
            "GET", get_all_releases_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_all_components(self, project_id, active_only=False, include_deleted=False):
        params = {
            "active_only": active_only,
            "include_deleted": include_deleted,
        }

        get_all_components_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/components?"
            + urllib.parse.urlencode(params)
        )

        response = requests.request(
            "GET", get_all_components_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_requirement_importances(self, project_template_id):
        get_requirement_importances_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/requirements/importances"
        )

        response = requests.request(
            "GET",
            get_requirement_importances_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_incident_priorities(self, project_template_id):
        get_incident_priorities_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/incidents/priorities"
        )

        response = requests.request(
            "GET", get_incident_priorities_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_task_priorities(self, project_template_id):
        get_task_priorities_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/tasks/priorities"
        )

        response = requests.request(
            "GET", get_task_priorities_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def add_association(self, project_id, body) -> Dict:
        create_association_url = (
            self.base_url + "projects/" + str(project_id) + "/associations"
        )
        payload = json.dumps(body)
        response = requests.request(
            "POST",
            create_association_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )
        if response.ok:
            return response.json()
        else:
            return response  # type: ignore

    def get_requirement_statuses(self, project_template_id):
        get_requirement_statuses_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/requirements/statuses"
        )

        response = requests.request(
            "GET",
            get_requirement_statuses_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_incident_statuses(self, project_template_id):
        get_incident_statuses_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/incidents/statuses"
        )

        response = requests.request(
            "GET", get_incident_statuses_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_task_statuses(self, project_template_id):
        get_task_statuses_url = (
            self.base_url
            + "project-templates/"
            + str(project_template_id)
            + "/tasks/statuses"
        )

        response = requests.request(
            "GET", get_task_statuses_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def delete_requirement(self, project_id, requirement_id):
        delete_requirement_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/requirements/"
            + str(requirement_id)
        )

        response = requests.request(
            "DELETE", delete_requirement_url, headers=self.headers, verify=self.verify
        )

        return response.status_code

    def delete_incident(self, project_id, incident_id):
        delete_incident_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/incidents/"
            + str(incident_id)
        )

        response = requests.request(
            "DELETE", delete_incident_url, headers=self.headers, verify=self.verify
        )

        return response.status_code

    def delete_task(self, project_id, task_id):
        delete_task_url = (
            self.base_url + "projects/" + str(project_id) + "/tasks/" + str(task_id)
        )

        response = requests.request(
            "DELETE", delete_task_url, headers=self.headers, verify=self.verify
        )

        return response.status_code

    def delete_component(self, project_id, component_id):
        delete_component_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/components/"
            + str(component_id)
        )

        response = requests.request(
            "DELETE", delete_component_url, headers=self.headers, verify=self.verify
        )

        return response.status_code

    def delete_release(self, project_id, release_id):
        delete_release_url = (
            self.base_url
            + "projects/"
            + str(project_id)
            + "/releases/"
            + str(release_id)
        )

        response = requests.request(
            "DELETE", delete_release_url, headers=self.headers, verify=self.verify
        )

        return response.status_code

    def get_all_programs(self) -> Dict:
        get_all_programs_url = self.base_url + "programs"

        response = requests.request(
            "GET", get_all_programs_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_program(self, program_id) -> Dict:
        get_program_url = self.base_url + "programs/" + program_id

        response = requests.request(
            "GET", get_program_url, headers=self.headers, verify=self.verify
        )

        return response.json()

    def get_system_custom_properties(self, artifact) -> Dict:
        get_system_custom_property_url = (
            self.base_url + "system/custom-properties/" + artifact
        )

        response = requests.request(
            "GET",
            get_system_custom_property_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def create_program_milestone(self, program_id, body):
        create_program_milestone_url = (
            self.base_url + "programs/" + str(program_id) + "/milestones"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            create_program_milestone_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )

        return response.json()

    def get_all_program_milestones(self, program_id):
        get_all_program_milestones_url = (
            self.base_url + "programs/" + str(program_id) + "/milestones"
        )

        response = requests.request(
            "GET",
            get_all_program_milestones_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def create_capability(self, program_id, body):
        create_capability_url = (
            self.base_url + "programs/" + str(program_id) + "/capabilities"
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            create_capability_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )

        return response.json()

    def create_child_capability(self, program_id, parentid, body):
        create_child_capability_url = (
            self.base_url
            + "programs/"
            + str(program_id)
            + "/capabilities/"
            + str(parentid)
        )

        payload = json.dumps(body)

        response = requests.request(
            "POST",
            create_child_capability_url,
            headers=self.headers,
            data=payload,
            verify=self.verify,
        )

        return response.json()

    def get_all_program_capabilities(self, program_id):
        params = {"current_page": 1, "page_size": 10000}

        get_all_program_capabilities_url = (
            self.base_url
            + "programs/"
            + str(program_id)
            + "/capabilities/search?"
            + urllib.parse.urlencode(params)
        )

        response = requests.request(
            "GET",
            get_all_program_capabilities_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def add_capability_requirement_association(
        self, program_id, capability_id, requirement_id
    ):
        capability_requirement_association_url = (
            self.base_url
            + "programs/"
            + str(program_id)
            + "/capabilities/"
            + str(capability_id)
            + "/requirements/"
            + str(requirement_id)
        )

        response = requests.request(
            "POST",
            capability_requirement_association_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.status_code

    def delete_program_capability(self, program_id, capability_id):
        delete_program_capability_url = (
            self.base_url
            + "/programs/"
            + str(program_id)
            + "/capabilities/"
            + str(capability_id)
        )

        response = requests.request(
            "DELETE",
            delete_program_capability_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.status_code

    def delete_program_milestone(self, program_id, milestone_id):
        delete_program_milestone_url = (
            self.base_url
            + "/programs/"
            + str(program_id)
            + "/milestones/"
            + str(milestone_id)
        )

        response = requests.request(
            "DELETE",
            delete_program_milestone_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.status_code

    def get_program_capability_types(self):
        get_program_capability_types_url = self.base_url + "capabilities/types"

        response = requests.request(
            "GET",
            get_program_capability_types_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_program_capability_statuses(self):
        get_program_capability_statuses_url = self.base_url + "capabilities/statuses"

        response = requests.request(
            "GET",
            get_program_capability_statuses_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_program_capability_priorities(self):
        get_program_capability_priorities_url = (
            self.base_url + "capabilities/priorities"
        )

        response = requests.request(
            "GET",
            get_program_capability_priorities_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_program_milestone_types(self):
        get_program_milestone_types_url = self.base_url + "program-milestones/types"

        response = requests.request(
            "GET",
            get_program_milestone_types_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()

    def get_program_milestone_statuses(self):
        get_program_milestone_statuses_url = (
            self.base_url + "program-milestones/statuses"
        )

        response = requests.request(
            "GET",
            get_program_milestone_statuses_url,
            headers=self.headers,
            verify=self.verify,
        )

        return response.json()
