from jira import JIRA
from spira import Spira
from datetime import datetime
from utility import convert_jira_markup_to_html, try_json_dump_string
import json


# Convert a single type of issues to the correctly mapped one in Spira.
def convert_jira_to_spira_issues(
    jira_connection_dict,
    skip_ssl,
    jira_output_dict,
    mapping_dict,
    spira_metadata,
    jira_metadata,
    all_requirements_in_spira,
    current_artifact_type,
    current_issue_type,
):
    print("Starting conversion of Spira artifact type: " + str(current_artifact_type))
    print("With Jira issue type: " + str(current_issue_type))

    to_validate = open("temp/to_spira.json", "w")

    validation_dict = {
        "product": [],
    }

    issues = jira_output_dict["issues"]

    # What kind of spira artifact type we are converting to from the jira issue and issue type.
    if current_artifact_type == "requirements":
        # Find the top level issues, aka initiatives
        for issue in issues:
            # Check if issue is not already in capabilities, and filter out the currently processed jira issue type.
            #
            # issue should not be in capabilities AND
            # spira mapped name should exist AND
            # the issue type of the issue should match what we're currently processing.
            if (
                not_in_capabilities((issue["key"]), spira_metadata["capabilites"])
                and get_mapped_spira_type_name(
                    mapping_dict["types"][current_artifact_type],
                    issue["fields"]["issuetype"]["name"],
                )
                is not None
                and issue["fields"]["issuetype"]["name"] == current_issue_type
            ):
                requirement = {"project_id": spira_metadata["project"]["ProjectId"]}

                payload = {
                    # Requirement_id - READ ONLY - set when spira creates the artifact inside its system
                    # Indentlevel - Initiative level does not need to be set, as its the highest level which gets assigned automatically.
                    "StatusId": jira_status_to_spira_status_id(
                        mapping_dict["statuses"]["requirements"],
                        spira_metadata["statuses"]["requirement"],
                        issue["fields"]["status"]["name"],
                    ),
                    "RequirementTypeId": jira_issue_type_to_spira_requirement_type_id(
                        spira_metadata["types"]["requirement"],
                        issue["fields"]["issuetype"]["name"],
                        mapping_dict,
                    ),
                    "AuthorId": find_spira_user_id_by_email(
                        spira_metadata["users"], "reporter", issue
                    ),
                    "OwnerId": find_spira_user_id_by_email(
                        spira_metadata["users"], "assignee", issue
                    ),
                    "ImportanceId": jira_priority_to_requirement_importance_id(
                        spira_metadata["importances"],
                        issue["fields"]["priority"],
                        mapping_dict,
                    ),  # REQUIRED - differs between jira and spira, mapped in the mapping file
                    "ReleaseId": jira_version_to_spira_release_id(
                        spira_metadata["releases"], issue
                    ),  # REQUIRED - the id of the release to connect to, we need to have prepared the releases in Spira
                    "ComponentId": jira_component_to_spira_component_id(
                        spira_metadata["components"], issue, isComponentArray=False
                    ),
                    "Name": issue["fields"]["summary"],
                    "Description": convert_jira_markup_to_html(
                        jira_connection_dict,
                        skip_ssl,
                        issue["fields"]["description"],
                    ),
                    # CreationDate # READ ONLY - is read only, special solution needed with custom properties below.
                    # LastUpdateDate" # READ ONLY - is read only, special solution needed with custom properties below.
                    # Summary - READ ONLY
                    "EstimatePoints": calculate_estimate_points(
                        issue["fields"]["aggregatetimeoriginalestimate"]
                    ),
                    # EstimatedEffort - ?
                    # TaskEstimatedEffort - ?
                    # TaskActualEffort - ?
                    # TaskCount - READ ONLY
                    # ReleaseVerionNumber - READ ONLY
                    # Steps - READ ONLY
                    "StartDate": get_jira_data_from_custom_field(
                        issue, jira_metadata["customfields"], "Target start"
                    ),
                    "EndDate": get_jira_data_from_custom_field(
                        issue, jira_metadata["customfields"], "Target end"
                    ),
                    "PercentComplete": None,
                    "GoalId": None,
                    "IsSuspect": False,  # False is the default value
                    # ProjectId - Suspected that it is derived from the projectid in the input, as it's populated when a GET of the artifact is made
                    # ConcurrencyDate - READ ONLY
                    # Tags - ?
                }

                # releaseid and componentid
                requirement["artifact_type"] = "requirement"

                # Add all the custom properties
                payload["CustomProperties"] = add_custom_properties(
                    issue,
                    spira_metadata,
                    jira_metadata,
                    mapping_dict["custom_props"]["requirements"],
                    "requirement",
                    jira_connection_dict,
                    skip_ssl,
                )

                requirement["payload"] = payload
                requirement["parentlink"] = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], "Parent Link"
                )
                requirement["epiclink"] = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], "Epic Link"
                )
                validation_dict["product"].append(requirement)

    # Else if it's currently processing jira issue of type Sub-task to spira artifact type Task
    elif current_artifact_type == "tasks":
        # Find all the sub-tasks
        for issue in issues:
            # Check if issue is not already in capabilities, and filter out the currently processed jira issue type.
            #
            # issue should not be in capabilities AND
            # spira mapped name should exist AND
            # the issue type of the issue should match what is currently processing.
            if (
                not_in_capabilities((issue["key"]), spira_metadata["capabilites"])
                and get_mapped_spira_type_name(
                    mapping_dict["types"][current_artifact_type],
                    issue["fields"]["issuetype"]["name"],
                )
                is not None
                and issue["fields"]["issuetype"]["name"] == current_issue_type
            ):
                task = {"project_id": spira_metadata["project"]["ProjectId"]}

                payload = {
                    # Task_id - READ ONLY - set when spira creates the artifact inside its system
                    "TaskStatusId": jira_status_to_spira_status_id(
                        mapping_dict["statuses"]["tasks"],
                        spira_metadata["statuses"]["task"],
                        issue["fields"]["status"]["name"],
                    ),
                    "TaskTypeId": jira_issue_type_to_spira_task_type_id(
                        spira_metadata["types"]["task"],
                        issue["fields"]["issuetype"]["name"],
                        mapping_dict,
                    ),
                    # TaskFolderId: None,  # Not in plan to be developed right now
                    "RequirementId": get_spira_id_from_jira_id(
                        all_requirements_in_spira, issue["fields"]["parent"]["key"]
                    )
                    if "parent" in issue["fields"]
                    else 0,
                    "ReleaseId": jira_version_to_spira_release_id(
                        spira_metadata["releases"], issue
                    ),  # REQUIRED - the id of the release to connect to, releases in Spira must be prepared beforehand
                    # ComponentId - READ ONLY - cant be set, only retrieved as it inherits the component from the parent.
                    "CreatorId": find_spira_user_id_by_email(
                        spira_metadata["users"], "reporter", issue
                    ),
                    "OwnerId": find_spira_user_id_by_email(
                        spira_metadata["users"], "assignee", issue
                    ),
                    "TaskPriorityId": jira_priority_to_task_priority_id(
                        spira_metadata["task_priorities"],
                        issue["fields"]["priority"],
                        mapping_dict,
                    ),  # REQUIRED - differs between jira and spira, mapped in the mapping file
                    "Name": issue["fields"]["summary"],
                    "Description": convert_jira_markup_to_html(
                        jira_connection_dict, skip_ssl, issue["fields"]["description"]
                    ),
                    # CreationDate # READ ONLY - is read only, special solution needed with custom properties below.
                    # LastUpdateDate" # READ ONLY - is read only, special solution needed with custom properties below.
                    "StartDate": get_jira_data_from_custom_field(
                        issue, jira_metadata["customfields"], "Target start"
                    ),
                    "EndDate": get_jira_data_from_custom_field(
                        issue, jira_metadata["customfields"], "Target end"
                    ),
                    "CompletionPercent": 0,
                    "EstimatedEffort": None,
                    "ActualEffort": None,
                    "RemainingEffort": None,
                    "ProjectedEffort": None,
                    "TaskStatusName": None,
                    "TaskTypeName": None,
                    "OwnerName": None,
                    "TaskPriorityName": None,
                    "ProjectName": None,
                    "ReleaseVersionNumber": None,
                    "RequirementName": None,
                    "RiskId": None,
                    # "ProjectId":0,
                    # "ProjectGuid":None,
                    # "ArtifactTypeId":0,
                    # "ConcurrencyDate":READ ONLY "0001-01-01T00:00:00",
                    # "IsAttachments":False,
                    # "Tags":? None,
                    # "Guid":None
                    # Tags - ?
                }

                task["artifact_type"] = "task"

                # Add all the custom properties
                payload["CustomProperties"] = add_custom_properties(
                    issue,
                    spira_metadata,
                    jira_metadata,
                    mapping_dict["custom_props"]["tasks"],
                    "task",
                    jira_connection_dict,
                    skip_ssl,
                )

                task["payload"] = payload
                validation_dict["product"].append(task)

    # Else if it's processing artifacts of type incidents
    elif current_artifact_type == "incidents":
        # Find all incidents
        for issue in issues:
            # Check if issue is not already in capabilities, and filter out the currently processed jira issue type.
            #
            # issue should not be in capabilities AND
            # spira mapped name should exist AND
            # the issue type of the issue should match what we're currently processing.
            if (
                not_in_capabilities((issue["key"]), spira_metadata["capabilites"])
                and get_mapped_spira_type_name(
                    mapping_dict["types"][current_artifact_type],
                    issue["fields"]["issuetype"]["name"],
                )
                is not None
                and issue["fields"]["issuetype"]["name"] == current_issue_type
            ):
                incident = {"project_id": spira_metadata["project"]["ProjectId"]}
                incident_releases = jira_version_to_spira_release_id_incident_type(
                    spira_metadata["releases"], issue
                )

                payload = {
                    # IncidentId - READ ONLY - set when spira creates the artifact inside its system
                    "IncidentStatusId": jira_status_to_spira_status_id(
                        mapping_dict["statuses"]["incidents"],
                        spira_metadata["statuses"]["incident"],
                        issue["fields"]["status"]["name"],
                    ),
                    "IncidentTypeId": jira_issue_type_to_spira_incident_type_id(
                        spira_metadata["types"]["incident"],
                        issue["fields"]["issuetype"]["name"],
                        mapping_dict,
                    ),
                    # ArtifactTypeId - READ ONLY
                    "PriorityId": jira_priority_to_incident_priority_id(
                        spira_metadata["incident_priorities"],
                        issue["fields"]["priority"],
                        mapping_dict,
                    ),  # REQUIRED - differs between jira and spira, mapped in the mapping file
                    # TODO "SeverityId"
                    "OpenerId": find_spira_user_id_by_email(
                        spira_metadata["users"], "reporter", issue
                    ),
                    "OwnerId": find_spira_user_id_by_email(
                        spira_metadata["users"], "assignee", issue
                    ),
                    "DetectedReleaseId": incident_releases["detected_release"],
                    "ResolvedReleaseId": incident_releases["planned_release"],
                    "VerifiedReleaseId": incident_releases["verified_release"],
                    "Name": issue["fields"]["summary"],
                    "Description": convert_jira_markup_to_html(
                        jira_connection_dict, skip_ssl, issue["fields"]["description"]
                    ),
                    # CreationDate - READ ONLY
                    "StartDate": get_jira_data_from_custom_field(
                        issue, jira_metadata["customfields"], "Target start"
                    ),
                    "EndDate": get_jira_data_from_custom_field(
                        issue, jira_metadata["customfields"], "Target end"
                    ),
                    # TODO "ClosedDate"
                    # TODO - Something with the time and effort?
                    # FixedBuildId - ?
                    # DetectedBuildId - ?
                    # ProjectId - Suspected that it is derived from the projectid in the input, as it's populated later when a GET of the artifact is made
                    # LastUpdateDate # READ ONLY - is read only, special solution needed with custom properties below.
                    # CreationDate # READ ONLY - is read only, special solution needed with custom properties below.
                    # ConcurrencyDate - READ ONLY
                    # Tags - ?
                    "ComponentIds": jira_component_to_spira_component_id(
                        spira_metadata["components"], issue, isComponentArray=True
                    ),  # - Array of component Ids
                }

                # releaseid and componentid
                incident["artifact_type"] = "incident"

                # Add all the custom properties
                payload["CustomProperties"] = add_custom_properties(
                    issue,
                    spira_metadata,
                    jira_metadata,
                    mapping_dict["custom_props"]["incidents"],
                    "incident",
                    jira_connection_dict,
                    skip_ssl,
                )

                incident["payload"] = payload
                incident["parentlink"] = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], "Parent Link"
                )
                incident["epiclink"] = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], "Epic Link"
                )
                validation_dict["product"].append(incident)

    json.dump(validation_dict, to_validate, indent=4)

    to_validate.close()


def find_spira_user_id_by_email(users, person_field, issue):
    if not issue["fields"][person_field]:
        return None
    else:
        user = next(
            filter(
                lambda x: x["EmailAddress"]
                == issue["fields"][person_field]["emailAddress"],
                users,
            ),
            None,
        )

    if user:
        return user["UserId"]
    else:
        return None


def calculate_estimate_points(aggregatetimeoriginalestimate: int | None):
    if aggregatetimeoriginalestimate is None:
        return None
    else:
        return round((aggregatetimeoriginalestimate / 3600) / 8, 2)


def get_jira_data_from_custom_field(issue, jira_custom_fields, jira_field_name):
    customfield = next(
        filter(lambda x: x["name"] == jira_field_name, jira_custom_fields), None
    )

    if customfield and customfield["id"] in issue["fields"]:
        custom_value = issue["fields"][customfield["id"]]

        try:
            if is_datetime(str(custom_value)):
                custom_value = convert_datetime(custom_value)
        except Exception as e:
            print(e)

        return custom_value
    else:
        return None


def jira_priority_to_requirement_importance_id(
    importances, jira_priority_name, mapping
) -> int:
    if jira_priority_name is None:
        print(
            "Priority is null, artifact priority will have to be added in spira manually"
        )
        return 0

    mapped_name = mapping["priorities"]["requirements"][jira_priority_name["name"]]

    importance_object = next(
        filter(lambda x: x["Name"] == mapped_name, importances), None
    )

    if importance_object:
        return int(importance_object["ImportanceId"])
    else:
        return 0


def jira_priority_to_task_priority_id(priorities, jira_priority_name, mapping) -> int:
    if jira_priority_name is None:
        print(
            "Priority is null, artifact priority will have to be added in spira manually"
        )
        return 0

    mapped_name = mapping["priorities"]["tasks"][jira_priority_name["name"]]

    priority_object = next(filter(lambda x: x["Name"] == mapped_name, priorities), None)

    if priority_object:
        return int(priority_object["PriorityId"])
    else:
        return 0


def jira_priority_to_incident_priority_id(
    priorities, jira_priority_name, mapping
) -> int:
    if jira_priority_name is None:
        print(
            "Priority is null, artifact priority will have to be added in spira manually"
        )
        return 0

    mapped_name = mapping["priorities"]["incidents"][jira_priority_name["name"]]

    priority_obejct = next(filter(lambda x: x["Name"] == mapped_name, priorities), None)

    if priority_obejct:
        return int(priority_obejct["PriorityId"])
    else:
        return 0


def jira_issue_type_to_spira_requirement_type_id(
    requirement_types, issue_type, mapping
) -> int:
    if issue_type is None:
        return 0

    spira_mapped_type_name = get_mapped_spira_type_name(
        mapping["types"]["requirements"], issue_type
    )

    if not spira_mapped_type_name:
        # If the spira type is not mapped to a jira type
        return 0

    requirement_type_object = next(
        filter(lambda x: x["Name"] == spira_mapped_type_name, requirement_types), None
    )

    if requirement_type_object:
        return int(requirement_type_object["RequirementTypeId"])
    else:
        return 0


def jira_issue_type_to_spira_incident_type_id(
    incident_types, issue_type, mapping
) -> int:
    if issue_type is None:
        return 0

    spira_mapped_type_name = get_mapped_spira_type_name(
        mapping["types"]["incidents"], issue_type
    )

    if not spira_mapped_type_name:
        # If the spira type is not mapped to a jira type
        return 0

    requirement_type_object = next(
        filter(lambda x: x["Name"] == spira_mapped_type_name, incident_types), None
    )

    if requirement_type_object:
        return int(requirement_type_object["IncidentTypeId"])
    else:
        return 0


def jira_issue_type_to_spira_task_type_id(task_types, issue_type, mapping) -> int:
    if issue_type is None:
        return 0

    spira_mapped_type_name = get_mapped_spira_type_name(
        mapping["types"]["tasks"], issue_type
    )

    if not spira_mapped_type_name:
        # If the spira type is not mapped to a jira type
        return 0

    task_type_object = next(
        filter(lambda x: x["Name"] == spira_mapped_type_name, task_types), None
    )

    if task_type_object:
        return int(task_type_object["TaskTypeId"])
    else:
        return 0


def get_mapped_spira_type_name(type_mapping, jira_issue_type) -> str | None:
    spira_mapped_type_name = None
    for spira_type in type_mapping:
        jira_types = type_mapping[spira_type]
        if isinstance(jira_types, list) and jira_issue_type in type_mapping[spira_type]:
            spira_mapped_type_name = spira_type
            break
        elif (
            isinstance(jira_types, str) and jira_issue_type == type_mapping[spira_type]
        ):
            spira_mapped_type_name = spira_type
            break
    return spira_mapped_type_name


def get_spira_id_from_jira_id(all_requirements_in_spira, jira_id):
    for requirement in all_requirements_in_spira:
        property = next(
            filter(
                (
                    lambda x: x["Definition"]["Name"] == "Jira Id"
                    and x["StringValue"] == jira_id
                ),
                requirement["CustomProperties"],
            ),
            None,
        )
        if property is not None:
            return requirement["RequirementId"]

    return None


def not_in_capabilities(jira_id, all_capabilites):
    for capability in all_capabilites:
        property = next(
            filter(
                (
                    lambda x: x["Definition"]["Name"] == "Jira Id"
                    and x["StringValue"] == jira_id
                ),
                capability["CustomProperties"],
            ),
            None,
        )
        if property is not None:
            return False

    return True


def is_datetime(date_string):
    date_formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f%z"]

    if date_string is None:
        return False

    for date_format in date_formats:
        try:
            datetime.strptime(date_string, date_format)
            return True
        except ValueError:
            continue
    return False


def convert_datetime(date_string):
    date_formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f%z"]

    for date_format in date_formats:
        try:
            modified_date_string = datetime.strptime(date_string, date_format)
            return modified_date_string.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

        except ValueError:
            continue


def add_custom_properties(
    issue,
    spira_metadata,
    jira_metadata,
    custom_props_mapping,
    artifact_type,
    jira_connection_dict,  # Needed for the rich_text_conversion
    skip_ssl,  # Needed for the rich_text_conversion
) -> list:
    custom_properties = [
        # Special case for Jira id as it's not in the fields part of the issue
        jira_string_field_to_spira_custom_prop(
            spira_metadata, artifact_type, "Jira Id", issue["key"]
        )
    ]

    custom_prop_to_add = None

    # Go through all the mappings of the custom props
    for prop in custom_props_mapping:
        # Check if it's a datetime type of the custom prop
        if prop["type"] == "date_time" or prop["type"] == "date":
            # Check if its a custom field, starting with if it's not
            if prop["jira_key"] is not None:
                time = issue["fields"][prop["jira_key"]]
                custom_prop_to_add = jira_datetime_field_to_spira_custom_prop(
                    spira_metadata, artifact_type, prop["spira_name"], time
                )
            # Handle it if the value is in a custom field
            else:
                time = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], prop["jira_custom_field_name"]
                )
                custom_prop_to_add = jira_datetime_field_to_spira_custom_prop(
                    spira_metadata, artifact_type, prop["spira_name"], time
                )

        # Check if it's a text type custom prop
        elif prop["type"] == "text":
            if prop["jira_key"] is not None:
                # Try to dump a string to json. If it fails set a standard string with a warning message.
                if not try_json_dump_string(issue["fields"][prop["jira_key"]]):
                    issue["fields"][
                        prop["jira_key"]
                    ] = "--MIGRATION OF TEXT FAILED because of error during JSON validation--"
                custom_prop_to_add = jira_string_field_to_spira_custom_prop(
                    spira_metadata,
                    artifact_type,
                    prop["spira_name"],
                    issue["fields"][prop["jira_key"]],
                )
            else:
                text = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], prop["jira_custom_field_name"]
                )
                custom_prop_to_add = jira_string_field_to_spira_custom_prop(
                    spira_metadata, artifact_type, prop["spira_name"], text
                )

        # Check if it's a decimal custom prop
        elif prop["type"] == "decimal":
            if prop["jira_key"] is not None:
                custom_prop_to_add = jira_decimal_field_to_spira_custom_prop(
                    spira_metadata,
                    artifact_type,
                    prop["spira_name"],
                    issue["fields"][prop["jira_key"]],
                )
            else:
                number = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], prop["jira_custom_field_name"]
                )

                custom_prop_to_add = jira_decimal_field_to_spira_custom_prop(
                    spira_metadata, artifact_type, prop["spira_name"], number
                )

        # Check if it's a rich text custom prop
        elif prop["type"] == "rich_text":
            if jira_connection_dict is None:
                print("No jira connection dict present, can't convert rich text")
                continue
            # Check if it's a jira key,
            if prop["jira_key"] is not None:
                custom_prop_to_add = jira_textarea_field_to_spira_custom_prop(
                    spira_metadata,
                    artifact_type,
                    prop["spira_name"],
                    issue["fields"][prop["jira_key"]],
                    jira_connection_dict,
                    skip_ssl,
                )
            # Else it is a custom field
            else:
                text = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], prop["jira_custom_field_name"]
                )
                custom_prop_to_add = jira_textarea_field_to_spira_custom_prop(
                    spira_metadata,
                    artifact_type,
                    prop["spira_name"],
                    text,  # type: ignore
                    jira_connection_dict,
                    skip_ssl,
                )

        # Check if it's a list custom prop
        elif prop["type"] == "list":
            if prop["jira_key"] is not None:
                custom_prop_to_add = jira_list_field_to_spira_custom_prop(
                    spira_metadata,
                    artifact_type,
                    prop["spira_name"],
                    issue["fields"][prop["jira_key"]]["value"],
                )

            else:
                list_value = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], prop["jira_custom_field_name"]
                )

                custom_prop_to_add = jira_list_field_to_spira_custom_prop(
                    spira_metadata, artifact_type, prop["spira_name"], list_value
                )

        # Check if it's a multiselect list custom prop
        elif prop["type"] == "multiselect_list":
            # Check if it's a jira key,
            # This is not tested since there are no standards fields as multiselect list at the moment.
            if prop["jira_key"] is not None:
                custom_prop_to_add = jira_multiselect_list_field_to_spira_custom_prop(
                    spira_metadata,
                    artifact_type,
                    prop["spira_name"],
                    issue["fields"][prop["jira_key"]],
                )

            else:
                list_of_values = get_jira_data_from_custom_field(
                    issue, jira_metadata["customfields"], prop["jira_custom_field_name"]
                )

                custom_prop_to_add = jira_multiselect_list_field_to_spira_custom_prop(
                    spira_metadata, artifact_type, prop["spira_name"], list_of_values
                )

        custom_properties.append(custom_prop_to_add)

    return custom_properties


def jira_list_field_to_spira_custom_prop(
    spira_metadata, artifact_type, spira_custom_prop_name, issue_field_value
) -> dict | None:
    spira_custom_props = spira_metadata["custom_properties"][artifact_type]

    custom_prop_data = next(
        filter((lambda x: x["Name"] == spira_custom_prop_name), spira_custom_props),
        None,
    )

    if custom_prop_data:
        custom_prop = {
            "PropertyNumber": custom_prop_data["PropertyNumber"],
            "StringValue": None,
            "IntegerValue": jira_list_value_to_spira_id(
                custom_prop_data["CustomList"]["Values"], issue_field_value
            )
            if issue_field_value
            else None,
            "BooleanValue": None,
            "DateTimeValue": None,
            "DecimalValue": None,
            "IntegerListValue": None,
            "Definition": {
                "CustomPropertyId": custom_prop_data["CustomPropertyId"],
                "ProjectTemplateId": None
                if artifact_type == "capability"
                else spira_metadata["project"]["ProjectTemplateId"],
                "ArtifactTypeId": custom_prop_data["ArtifactTypeId"],
                "Name": custom_prop_data["CustomList"]["Name"],
                "CustomList": {
                    "CustomPropertyListId": custom_prop_data["CustomList"][
                        "CustomPropertyListId"
                    ],
                    "ProjectTemplateId": None
                    if artifact_type == "capability"
                    else spira_metadata["project"]["ProjectTemplateId"],
                    "Name": None,
                    "Active": False,
                    "SortedOnValue": False,
                    "Values": None,
                    "Guid": None,
                    "ConcurrencyGuid": None,
                    "LastUpdateDate": None,
                },
                "CustomPropertyFieldName": custom_prop_data["CustomPropertyFieldName"],
                "CustomPropertyTypeId": custom_prop_data["CustomPropertyTypeId"],
                "CustomPropertyTypeName": "List",
                "IsDeleted": False,
                "PropertyNumber": custom_prop_data["PropertyNumber"],
                "SystemDataType": "System.Int32",
                "Options": None,
                "Position": None,
                "Description": "",
                "Guid": None,
                "ConcurrencyGuid": None,
                "LastUpdateDate": None,
            },
        }
        return custom_prop
    else:
        return None


def jira_multiselect_list_field_to_spira_custom_prop(
    spira_metadata, artifact_type, spira_custom_prop_name, issue_field_value
) -> dict | None:
    spira_custom_props = spira_metadata["custom_properties"][artifact_type]

    custom_prop_data = next(
        filter((lambda x: x["Name"] == spira_custom_prop_name), spira_custom_props),
        None,
    )

    if custom_prop_data:
        custom_prop = {
            "PropertyNumber": custom_prop_data["PropertyNumber"],
            "StringValue": None,
            "IntegerValue": None,
            "BooleanValue": None,
            "DateTimeValue": None,
            "DecimalValue": None,
            "IntegerListValue": jira_multi_list_values_to_spira_ids(
                custom_prop_data["CustomList"]["Values"],
                issue_field_value,
                custom_prop_data["CustomList"]["Name"],
            )
            if issue_field_value
            else None,
            "Definition": {
                "CustomPropertyId": custom_prop_data["CustomPropertyId"],
                "ProjectTemplateId": None
                if artifact_type == "capability"
                else spira_metadata["project"]["ProjectTemplateId"],
                "ArtifactTypeId": custom_prop_data["ArtifactTypeId"],
                "Name": custom_prop_data["CustomList"]["Name"],
                "CustomList": {
                    "CustomPropertyListId": custom_prop_data["CustomList"][
                        "CustomPropertyListId"
                    ],
                    "ProjectTemplateId": None
                    if artifact_type == "capability"
                    else spira_metadata["project"]["ProjectTemplateId"],
                    "Name": None,
                    "Active": False,
                    "SortedOnValue": False,
                    "Values": None,
                    "Guid": None,
                    "ConcurrencyGuid": None,
                    "LastUpdateDate": None,
                },
                "CustomPropertyFieldName": custom_prop_data["CustomPropertyFieldName"],
                "CustomPropertyTypeId": custom_prop_data["CustomPropertyTypeId"],
                "CustomPropertyTypeName": "Multiselect List",
                "IsDeleted": False,
                "PropertyNumber": custom_prop_data["PropertyNumber"],
                "SystemDataType": "System.Collections.Generic.List`1[System.Int32]",
                "Options": None,
                "Position": None,
                "Description": "",
                "Guid": None,
                "ConcurrencyGuid": None,
                "LastUpdateDate": None,
            },
        }
        return custom_prop
    else:
        return None


def jira_datetime_field_to_spira_custom_prop(
    spira_metadata, artifact_type, spira_custom_prop_name, issue_field_value
) -> dict | None:
    spira_custom_props = spira_metadata["custom_properties"][artifact_type]

    custom_prop_data = next(
        filter((lambda x: x["Name"] == spira_custom_prop_name), spira_custom_props),
        None,
    )

    if issue_field_value:
        issue_field_value = convert_datetime(issue_field_value)

    if custom_prop_data:
        custom_prop = {
            "PropertyNumber": custom_prop_data["PropertyNumber"],
            "StringValue": None,
            "IntegerValue": None,
            "BooleanValue": None,
            "DateTimeValue": issue_field_value,
            "DecimalValue": None,
            "IntegerListValue": None,
            "Definition": {
                "CustomPropertyId": custom_prop_data["CustomPropertyId"],
                "ProjectTemplateId": None
                if artifact_type == "capability"
                else spira_metadata["project"]["ProjectTemplateId"],
                "ArtifactTypeId": custom_prop_data["ArtifactTypeId"],
                "Name": custom_prop_data["CustomPropertyFieldName"],
                "CustomList": None,
                "CustomPropertyFieldName": custom_prop_data["CustomPropertyFieldName"],
                "CustomPropertyTypeId": custom_prop_data["CustomPropertyTypeId"],
                "CustomPropertyTypeName": "Date & Time",
                "IsDeleted": False,
                "PropertyNumber": custom_prop_data["PropertyNumber"],
                "SystemDataType": "System.DateTime",
                "Options": None,
                "Position": None,
                "Description": None,
                "Guid": None,
                "ConcurrencyGuid": None,
                "LastUpdateDate": None,
            },
        }
        return custom_prop
    else:
        return None


def jira_string_field_to_spira_custom_prop(
    spira_metadata, artifact_type, spira_custom_prop_name, issue_field_value
) -> dict | None:
    spira_custom_props = spira_metadata["custom_properties"][artifact_type]

    custom_prop_data = next(
        filter((lambda x: x["Name"] == spira_custom_prop_name), spira_custom_props),
        None,
    )

    if custom_prop_data:
        custom_prop = {
            "PropertyNumber": custom_prop_data["PropertyNumber"],
            "StringValue": issue_field_value,
            "IntegerValue": None,
            "BooleanValue": None,
            "DateTimeValue": None,
            "DecimalValue": None,
            "IntegerListValue": None,
            "Definition": {
                "CustomPropertyId": custom_prop_data["CustomPropertyId"],
                "ProjectTemplateId": None
                if artifact_type == "capability"
                else spira_metadata["project"]["ProjectTemplateId"],
                "ArtifactTypeId": custom_prop_data["ArtifactTypeId"],
                "Name": custom_prop_data["CustomPropertyFieldName"],
                "CustomList": None,
                "CustomPropertyFieldName": custom_prop_data["CustomPropertyFieldName"],
                "CustomPropertyTypeId": custom_prop_data["CustomPropertyTypeId"],
                "CustomPropertyTypeName": "Text",
                "IsDeleted": False,
                "PropertyNumber": custom_prop_data["PropertyNumber"],
                "SystemDataType": "System.String",
                "Options": None,
                "Position": None,
                "Description": None,
                "Guid": None,
                "ConcurrencyGuid": None,
                "LastUpdateDate": None,
            },
        }
        return custom_prop
    else:
        return None


def jira_decimal_field_to_spira_custom_prop(
    spira_metadata, artifact_type, spira_custom_prop_name, issue_field_value
) -> dict | None:
    spira_custom_props = spira_metadata["custom_properties"][artifact_type]

    custom_prop_data = next(
        filter((lambda x: x["Name"] == spira_custom_prop_name), spira_custom_props),
        None,
    )

    if custom_prop_data:
        custom_prop = {
            "PropertyNumber": custom_prop_data["PropertyNumber"],
            "StringValue": None,
            "IntegerValue": None,
            "BooleanValue": None,
            "DateTimeValue": None,
            "DecimalValue": issue_field_value,
            "IntegerListValue": None,
            "Definition": {
                "CustomPropertyId": custom_prop_data["CustomPropertyId"],
                "ProjectTemplateId": None
                if artifact_type == "capability"
                else spira_metadata["project"]["ProjectTemplateId"],
                "ArtifactTypeId": custom_prop_data["ArtifactTypeId"],
                "Name": custom_prop_data["CustomPropertyFieldName"],
                "CustomList": None,
                "CustomPropertyFieldName": custom_prop_data["CustomPropertyFieldName"],
                "CustomPropertyTypeId": custom_prop_data["CustomPropertyTypeId"],
                "CustomPropertyTypeName": "Decimal",
                "IsDeleted": False,
                "PropertyNumber": custom_prop_data["PropertyNumber"],
                "SystemDataType": "System.Decimal",
                "Options": None,
                "Position": None,
                "Description": None,
                "Guid": None,
                "ConcurrencyGuid": None,
                "LastUpdateDate": None,
            },
        }
        return custom_prop
    else:
        return None


def jira_textarea_field_to_spira_custom_prop(
    spira_metadata,
    artifact_type,
    spira_custom_prop_name,
    issue_field_value: str,
    jira_connection_dict,
    skip_ssl,
) -> dict | None:
    spira_custom_props = spira_metadata["custom_properties"][artifact_type]

    custom_prop_data = next(
        filter((lambda x: x["Name"] == spira_custom_prop_name), spira_custom_props),
        None,
    )

    if custom_prop_data:
        custom_prop = {
            "PropertyNumber": custom_prop_data["PropertyNumber"],
            "StringValue": convert_jira_markup_to_html(
                jira_connection_dict, skip_ssl, issue_field_value
            ),
            "IntegerValue": None,
            "BooleanValue": None,
            "DateTimeValue": None,
            "DecimalValue": None,
            "IntegerListValue": None,
            "Definition": {
                "CustomPropertyId": custom_prop_data["CustomPropertyId"],
                "ProjectTemplateId": None
                if artifact_type == "capability"
                else spira_metadata["project"]["ProjectTemplateId"],
                "ArtifactTypeId": custom_prop_data["ArtifactTypeId"],
                "Name": custom_prop_data["CustomPropertyFieldName"],
                "CustomList": None,
                "CustomPropertyFieldName": custom_prop_data["CustomPropertyFieldName"],
                "CustomPropertyTypeId": custom_prop_data["CustomPropertyTypeId"],
                "CustomPropertyTypeName": "Text",
                "IsDeleted": False,
                "PropertyNumber": custom_prop_data["PropertyNumber"],
                "SystemDataType": "System.String",
                "Options": None,
                "Position": None,
                "Description": None,
                "Guid": None,
                "ConcurrencyGuid": None,
                "LastUpdateDate": None,
            },
        }
        return custom_prop
    else:
        return None


def jira_status_to_spira_status_id(mapping, status_types, issue_status_name) -> int:
    mapped_name = mapping[issue_status_name]

    status_object = next(filter(lambda x: x["Name"] == mapped_name, status_types), None)

    if status_object and "StatusId" in status_object:
        return int(status_object["StatusId"])
    elif status_object and "RequirementStatusId" in status_object:
        return int(status_object["RequirementStatusId"])
    elif status_object and "IncidentStatusId" in status_object:
        return int(status_object["IncidentStatusId"])
    elif status_object and "TaskStatusId" in status_object:
        return int(status_object["TaskStatusId"])
    elif status_object and "CapabilityStatusId" in status_object:
        return int(status_object["CapabilityStatusId"])
    else:
        return 0


def jira_list_value_to_spira_id(custom_list_values, issue_field_value):
    spira_list_value_id = next(
        filter((lambda x: x["Name"] == issue_field_value["value"]), custom_list_values),
        None,
    )

    if spira_list_value_id:
        return spira_list_value_id["CustomPropertyValueId"]
    else:
        return None


def jira_multi_list_values_to_spira_ids(
    custom_list_values, issue_field_value, custom_list_name
):
    list_of_ids = []

    for item in issue_field_value:
        spira_list_value_id = next(
            filter((lambda x: x["Name"] == item["value"]), custom_list_values),
            None,
        )

        if spira_list_value_id:
            list_of_ids.append(spira_list_value_id["CustomPropertyValueId"])
        else:
            print(
                "Error: Spira can't match this value when migrating a multiselect list: "
                + item["value"]
            )
            print("Jira name of list effected: " + custom_list_name)

    return list_of_ids


def jira_version_to_spira_release_id(releases, issue):
    affectedVersions = issue["fields"]["versions"]
    fixVersions = issue["fields"]["fixVersions"]

    if len(affectedVersions) > 0:
        print("For JIRA key: " + issue["key"])
        print(
            "This script does not handle affectedVersions, but they are still present:"
        )
        print(str(affectedVersions))

    if len(fixVersions) > 1:
        print("For JIRA key: " + issue["key"])
        print(
            "Spira can't handle more than one fixVersion, the first one will be set. These are the other versions not handled:"
        )
        print(str(fixVersions[1:]))

    if len(fixVersions) > 0:
        release = next(
            filter(lambda x: x["Name"] == fixVersions[0]["name"], releases), None
        )

        return release["ReleaseId"] if release is not None else None
    else:
        return None


def jira_version_to_spira_release_id_incident_type(releases, issue):
    affectedVersions = issue["fields"]["versions"]
    fixVersions = issue["fields"]["fixVersions"]

    incident_releases = {
        "detected_release": None,
        "planned_release": None,
        "verified_release": None,
    }

    if len(affectedVersions) > 1:
        print(
            "This script does not handle more than one affectedversion. These are the other versions not handled:"
        )
        print(str(affectedVersions[1:]))

    if len(fixVersions) > 1:
        print(
            "Spira can't handle more than one fixVersion, the first one will be set. These are the other versions not handled:"
        )
        print(str(fixVersions[1:]))

    if len(affectedVersions) > 0:
        detected_release_obj = next(
            filter(lambda x: x["Name"] == affectedVersions[0]["name"], releases), None
        )

        incident_releases["detected_release"] = (
            detected_release_obj["ReleaseId"]
            if detected_release_obj is not None
            else None
        )

    if len(fixVersions) > 0:
        fix_release_obj = next(
            filter(lambda x: x["Name"] == fixVersions[0]["name"], releases), None
        )
        if issue["fields"]["resolution"] is not None:
            incident_releases["verified_release"] = (
                fix_release_obj["ReleaseId"] if fix_release_obj is not None else None
            )
        else:
            incident_releases["planned_release"] = (
                fix_release_obj["ReleaseId"] if fix_release_obj is not None else None
            )

    return incident_releases


def jira_component_to_spira_component_id(components, issue, isComponentArray=False):
    jira_components = issue["fields"]["components"]

    if not isComponentArray and len(jira_components) > 1:
        print("For key: " + issue["key"])
        print("The script does not handle multiple components when it's not an array.")
        print("These components are not handled: ")
        print(str(jira_components[1:]))

    if len(jira_components) <= 0 and not isComponentArray:
        return None
    elif len(jira_components) <= 0 and isComponentArray:
        return []

    if isComponentArray:
        component_ids = []
        for component in jira_components:
            spira_component_obj = next(
                filter(lambda x: x["Name"] == component["name"], components), None
            )
            if spira_component_obj is not None and "ComponentId" in spira_component_obj:
                component_ids.append(spira_component_obj["ComponentId"])
        return component_ids
    else:
        spira_component_obj = next(
            filter(lambda x: x["Name"] == jira_components[0]["name"], components), None
        )
        if spira_component_obj is not None and "ComponentId" in spira_component_obj:
            return spira_component_obj["ComponentId"]
        else:
            return None
