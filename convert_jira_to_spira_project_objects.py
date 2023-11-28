import re
from jira import JIRA
from spira import Spira
import json


def convert_jira_to_spira_releases(jira_output_versions_dict, mapping_dict):
    releases_to_spira = open("temp/releases_to_spira.json", "w")

    to_spira_dict = {"releases": []}

    versions = jira_output_versions_dict["versions"]

    for version in versions:
        release = {}

        payload = {
            # ReleaseId - READ ONLY - set when spira creates the artifact
            # CreatorId - Jira does not record creator of versions
            # OwnerId - Jira does not record owner of versions
            # IndentLevel - We let spira set it for major/minor/patch version relationships
            "Name": version["name"] if "name" in version else "",
            "Description": version["description"] if "description" in version else " ",
            "VersionNumber": version["name"] if "name" in version else "",
            # CreationDate - READ ONLY - we do not need to set it
            # LastUpdateDate - we do not need to set it
            # Summary - Not used
            "ReleaseStatusId": calculate_release_status_id(
                version, mapping_dict["release_statuses"]
            ),
            "ReleaseTypeId": 1,  # We treat all jira versions as a major release
            "StartDate": (version["startDate"] + "T00:00:00.000")
            if "startDate" in version
            else "1970-01-01T00:00:00",
            "EndDate": (version["releaseDate"] + "T00:00:00.000")
            if "releaseDate" in version
            else "1970-01-01T00:00:00",
            # ResourceCount - Not used
            # DaysNonWorking - Not used
            # PlannedEffort - Not used
            # AvailableEffort - Not used
            # TaskEstimatedEffort - Not used
            # TaskActualEffort - Not used
            # TaskCount - Not used
            # PercentComplete - READ ONLY - Not used
            # ProjectId - set by spira in query parameter
            # ProjectGuid - Not used
            # ConcurrencyDate - Not used
            # CustomProperties - currently no unique custom properties
            # Tags - not used
            # Guid - not used
        }

        is_parent = check_if_parent(version["name"])

        release["is_parent"] = is_parent
        release["payload"] = payload

        to_spira_dict["releases"].append(release)

    json.dump(to_spira_dict, releases_to_spira, indent=4)

    releases_to_spira.close()


def convert_jira_to_spira_components(
    jira_output_components_dict,
):
    components_to_spira = open("temp/components_to_spira.json", "w")

    to_spira_dict = {"components": []}

    components = jira_output_components_dict["components"]

    for component in components:
        spira_component = {}

        payload = {
            # ComponentId - READ ONLY - populated by spira
            # ProjectId - set with post request
            "Name": component["name"] if "name" in component else "",
            "IsActive": (not component["archived"])
            if "archived" in component
            else True,
            "IsDeleted": component["deleted"] if "deleted" in component else False
            # Guid - READ ONLY
            # ConcurrencyGuid - READ ONLY
            # LastUpdateDate - READ ONLY
        }

        spira_component["payload"] = payload

        to_spira_dict["components"].append(spira_component)

    json.dump(to_spira_dict, components_to_spira, indent=4)

    components_to_spira.close()


def convert_jira_to_spira_customlists(
    jira_output_customlists_dict,
):
    customlist_to_spira = open("temp/customlists_to_spira.json", "w")

    to_spira_dict = {"customlists": []}

    customlists = jira_output_customlists_dict["customlists"]

    for customlist in customlists:
        spira_customlist = {}

        payload = {
            # "CustomPropertyListId": - READ ONLY - populated by spira,
            # "ProjectTemplateId": - set with post request,
            "Name": customlist["Name"],
            "Active": True,
            # "SortedOnValue":  - Not set at the moment, can be set later,
            "Values": set_list_values(customlist["Values"]),
        }

        spira_customlist["payload"] = payload

        to_spira_dict["customlists"].append(spira_customlist)

    json.dump(to_spira_dict, customlist_to_spira, indent=4)

    customlist_to_spira.close()


# Calculate the status from mapping
def calculate_release_status_id(version, release_statuses) -> int:
    archived = version["archived"]
    released = version["released"]

    valid_statuses = {
        "Planned": 1,
        "InProgress": 2,
        "Completed": 3,
        "Closed": 4,
        "Deferred": 5,
        "Cancelled": 6,
    }

    if not archived and not released:
        return valid_statuses[release_statuses["not_archived_and_not_released"]]
    elif not archived and released:
        return valid_statuses[release_statuses["not_archived_and_released"]]
    elif archived and not released:
        return valid_statuses[release_statuses["archived_and_not_released"]]
    elif archived and released:
        return valid_statuses[release_statuses["archived_and_released"]]
    else:
        return 0


# Check if the version is top level
def check_if_parent(name) -> bool:
    # Assumes that if the last character in the version name is not number this is a child release
    m = re.findall(r"\d+$", name[-1])
    if not m:
        return False

    # Find all the numbers in a string
    numbers_in_name = re.findall(r"\d+", name)

    # Convert a list of string numbers to int
    numbers_in_name = [int(numeric_string) for numeric_string in numbers_in_name]

    # Assumes that if it's more than two numbers in the name it is a child release
    return len(numbers_in_name) < 3


def set_list_values(jira_values):
    values = []

    for item in jira_values:
        name_of_value = {
            "Name": item["value"],
            "Active": True
            # "ParentCustomPropertyValueId": Not set at the moment, can be set later,
            # "Guid": READ ONLY,
            # "ConcurrencyGuid": READ ONLY,
            # "LastUpdateDate": READ ONLY,
        }

        values.append(name_of_value)

    return values
