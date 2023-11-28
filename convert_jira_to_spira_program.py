import json
from utility import convert_jira_markup_to_html
from convert_jira_to_spira_issues import (
    find_spira_user_id_by_email,
    get_jira_data_from_custom_field,
    add_custom_properties,
    get_mapped_spira_type_name,
    jira_status_to_spira_status_id,
    get_mapped_spira_type_name,
)


# Convert a single type of issues to the correctly mapped one on the program level in spira.
def convert_jira_issues_to_spira_program_capabilities(
    jira_connection_dict,
    skip_ssl,
    jira_output_dict,
    mapping_dict,
    spira_metadata,
    jira_metadata,
    current_issue_type,
):
    print(
        "Starting conversion of jira issue type to capabilities: "
        + (str(current_issue_type))
    )

    conversion_output = open("temp/capabilities_to_spira.json", "w")

    output_dict = {"program": []}

    issues = jira_output_dict["issues"]

    program_id = spira_metadata["program"]["program_id"]

    for issue in issues:
        if (
            get_mapped_spira_type_name(
                mapping_dict["types"]["capabilities"],
                issue["fields"]["issuetype"]["name"],
            )
            is not None
            and issue["fields"]["issuetype"]["name"] == current_issue_type
        ):
            capability = {
                "issue_type": issue["fields"]["issuetype"]["name"],
                "program_id": program_id,
            }

            payload = {
                # CapabilityId - READ ONLY - set when spira creates the capability
                # ProjectGroupId - essentially READ ONLY - set when inserted into a program, as ProjectGroupId is the same as program_id
                "MilestoneId": get_milestone_id_from_jira_issue(
                    issue, spira_metadata["milestones"]
                ),
                # MilestoneName
                "StatusId": jira_status_to_spira_status_id(
                    mapping_dict["statuses"]["capabilities"],
                    spira_metadata["statuses"]["capability"],
                    issue["fields"]["status"]["name"],
                ),
                # StatusName
                # StatusIsOpen
                "TypeId": jira_issue_type_to_spira_capability_type_id(
                    spira_metadata["types"]["capability"],
                    issue["fields"]["issuetype"]["name"],
                    mapping_dict,
                ),
                # TypeName
                "PriorityId": jira_priority_to_capability_priority_id(
                    spira_metadata["priorities"]["capability"],
                    issue["fields"]["priority"]["name"],
                    mapping_dict["priorities"]["capabilities"],
                ),
                # PriorityName
                "Name": issue["fields"]["summary"],
                "Description": convert_jira_markup_to_html(
                    jira_connection_dict, skip_ssl, issue["fields"]["description"]
                ),
                # PercentComplete - probably read only
                # RequirementCount - probably read only
                # IndentLevel
                # Guid - READ ONLY - assigned when created
                "CreatorId": find_spira_user_id_by_email(
                    spira_metadata["users"], "reporter", issue
                ),
                # CreatorName - Above method is enough
                "OwnerId": find_spira_user_id_by_email(
                    spira_metadata["users"], "assignee", issue
                ),
                # OwnerName - Above method is enough
                # CreationDate - READ ONLY - probably need to be put in a custom field or something
                # LastUpdateDate - READ ONLY - see above
                # IsSummary - READ ONLY
                # ConcurrencyGuid - READ ONLY
                # CustomProperties - Added later, see below
            }

            payload["CustomProperties"] = add_custom_properties(
                issue,
                spira_metadata,
                jira_metadata,
                mapping_dict["custom_props"]["capabilities"],
                "capability",
                jira_connection_dict,
                skip_ssl,
            )

            capability["payload"] = payload
            capability["parent_link"] = get_jira_data_from_custom_field(
                issue, jira_metadata["customfields"], "Parent Link"
            )
            capability["epic_link"] = get_jira_data_from_custom_field(
                issue, jira_metadata["customfields"], "Epic Link"
            )

            output_dict["program"].append(capability)

    json.dump(output_dict, conversion_output, indent=4)

    conversion_output.close()


def convert_jira_versions_to_spira_program_milestones(
    capabilities, jira_output_versions_dict, mapping_dict, spira_program_metadata
):
    milestones_to_spira = open("temp/milestones_to_spira.json", "w")
    input_versions = jira_output_versions_dict["versions"]

    to_spira_dict = {"milestones": []}

    versions = []

    for capability in capabilities:
        affectedVersions = capability["fields"]["versions"]
        fixVersions = capability["fields"]["fixVersions"]

        if len(affectedVersions) > 0:
            print("For JIRA key: " + capability["key"])
            print(
                "This script does not handle affectedVersions, but they are still present:"
            )
            print(str(affectedVersions))

        if len(fixVersions) > 1:
            print("For JIRA key: " + capability["key"])
            print(
                "Spira can't handle more than one fixVersion, the first one will be set. These are the other versions not handled:"
            )
            print(str(fixVersions[1:]))

        if len(fixVersions) > 0:
            found_version = next(
                filter(
                    lambda x: x["name"] == fixVersions[0]["name"],
                    input_versions,
                ),
                None,
            )

            # This might not work as identical objects might not be detected as such.
            if found_version not in versions and found_version is not None:
                versions.append(found_version)

    for version in versions:
        milestone = {}

        payload = {
            # MilestoneId - READ ONLY - assigned on creation
            # Guid - READ ONLY
            # CreatorId - Jira does not record creator of versions
            # CreatorName
            # OwnerId - Jira does not record owner of versions
            # OwnerName
            "StatusId": calculate_milestone_status_id(
                version,
                mapping_dict["milestone_statuses"],
                spira_program_metadata["statuses"]["milestone"],
            ),
            # StatusIsOpen - READ ONLY
            # StatusName
            # TypeId - TODO
            # TypeName
            "Name": version["name"] if "name" in version else "",
            "Description": version["description"] if "description" in version else " ",
            # ProjectGroupId
            # ProjectGroupName
            "StartDate": (version["startDate"] + "T00:00:00.000")
            if "startDate" in version
            else "1970-01-01T00:00:00",
            # ChildrenStartDate - probably read only
            "EndDate": (version["releaseDate"] + "T00:00:00.000")
            if "releaseDate" in version
            else "1970-01-01T00:00:00",
            # ChildrenEndDate - probably read only
            # CreationDate - probably read only - need to use custom properties
            # LastUpdateDate - probably read only - need to sue custom properties
            # PercentComplete - READ ONLY
            # ReleaseCount - READ ONLY
            # RequirementCount - READ ONLY
            # ConcurrencyGuid - READ ONLY
            # CustomProperties - TODO
        }

        milestone["payload"] = payload

        to_spira_dict["milestones"].append(milestone)

    json.dump(to_spira_dict, milestones_to_spira, indent=4)

    milestones_to_spira.close()


def get_milestone_id_from_jira_issue(issue, milestones):
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
        milestone = next(
            filter(lambda x: x["Name"] == fixVersions[0]["name"], milestones), None
        )
        if milestone is not None and "MilestoneId" in milestone:
            return milestone["MilestoneId"]
        else:
            return None
    else:
        return None


def calculate_milestone_status_id(
    version, milestone_statuses, spira_milestone_statuses
) -> int:
    archived = version["archived"]
    released = version["released"]

    if not archived and not released:
        spira_status_name = milestone_statuses["not_archived_and_not_released"]
        found_milestone = next(
            filter(lambda x: x["Name"] == spira_status_name, spira_milestone_statuses)
        )
        return found_milestone["StatusId"] if found_milestone is not None else 0
    elif not archived and released:
        spira_status_name = milestone_statuses["not_archived_and_released"]
        found_milestone = next(
            filter(lambda x: x["Name"] == spira_status_name, spira_milestone_statuses)
        )
        return found_milestone["StatusId"] if found_milestone is not None else 0
    elif archived and not released:
        spira_status_name = milestone_statuses["archived_and_not_released"]
        found_milestone = next(
            filter(lambda x: x["Name"] == spira_status_name, spira_milestone_statuses)
        )
        return found_milestone["StatusId"] if found_milestone is not None else 0
    elif archived and released:
        spira_status_name = milestone_statuses["archived_and_released"]
        found_milestone = next(
            filter(lambda x: x["Name"] == spira_status_name, spira_milestone_statuses)
        )
        return found_milestone["StatusId"] if found_milestone is not None else 0
    else:
        return 0


def jira_priority_to_capability_priority_id(
    spira_priorities, jira_priority_name, priority_mapping
) -> int:
    if jira_priority_name is None:
        print(
            "Priority is null, artifact priority will have to be added in spira manually"
        )
        return 0

    mapped_name = priority_mapping[jira_priority_name]

    priority_object = next(
        filter(lambda x: x["Name"] == mapped_name, spira_priorities), None
    )

    if priority_object:
        return int(priority_object["CapabilityPriorityId"])
    else:
        return 0


def jira_issue_type_to_spira_capability_type_id(capability_types, issue_type, mapping):
    if issue_type is None:
        return 0

    spira_mapped_type_name = get_mapped_spira_type_name(
        mapping["types"]["capabilities"], issue_type
    )

    if not spira_mapped_type_name:
        # If the spira type is not mapped to a jira type
        return 0

    capability_type_object = next(
        filter(lambda x: x["Name"] == spira_mapped_type_name, capability_types)
    )

    if capability_type_object:
        return int(capability_type_object["CapabilityTypeId"])
    else:
        return 0
