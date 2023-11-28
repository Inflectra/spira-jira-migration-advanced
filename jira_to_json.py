import sys
import json
import os
from jira import JIRA


def jira_to_json(jira, output_file_handle, jql):
    if not (jira and output_file_handle):
        print("Jira connection instance or output file handle found, exiting")
        sys.exit(1)

    outdict = {"jql": jql, "issues": []}

    print("Using jql query: '" + jql + "' to search for issues...")

    issues = jira.search_issues(
        jql, maxResults=False, fields="*all"
    )  # The script expect it to retrieve all issues, but it is unknown if it's actually the case as the docs dont specify it.

    print("Number of issues found: " + str(len(issues)))
    print(
        "Saving to file in directory: " + str(os.path.realpath(output_file_handle.name))
    )

    for issue in issues:
        outdict["issues"].append(issue.raw)

    json.dump(outdict, output_file_handle, indent=4)

    print("Extraction of issues complete")

    return len(issues)


def jira_versions_to_json(jira, output_file_handle, projects):
    if not (jira and output_file_handle):
        print("Jira connection instance or output file handle found, exiting")
        sys.exit(1)

    outdict = {"versions": []}

    for project in projects:
        versions = jira.project_versions(project)

        for version in versions:
            outdict["versions"].append(version.raw)

    json.dump(outdict, output_file_handle, indent=4)

    print("Extraction of versions complete")

    return len(outdict["versions"])


def jira_components_to_json(jira, output_file_handle, projects):
    if not (jira and output_file_handle):
        print("Jira connection instance or our output file handle not found, exiting")
        sys.exit(1)

    outdict = {"components": []}

    for project in projects:
        components = jira.project_components(project)

        for component in components:
            outdict["components"].append(component.raw)

    json.dump(outdict, output_file_handle, indent=4)

    print("Extraction of components complete")

    return len(outdict["components"])


def jira_customlists_to_json(jira, output_file_handle, projects):
    if not (jira and output_file_handle):
        print("Jira connection instance or our output file handle not found, exiting")
        sys.exit(1)

    outdict = {"customlists": []}

    # A set for issue type id to avoid duplicates
    all_issue_type_ids = set()

    # Gets all issuetypes id for every project
    for project in projects:
        if jira._version >= (8, 4, 0):
            project_issue_types = jira.createmeta_issuetypes(project)["values"]
        else:
            if len(jira.createmeta(projectKeys=project)["projects"]) > 0:
                project_issue_types = jira.createmeta(projectKeys=project)["projects"][
                    0
                ]["issuetypes"]
            else:
                project_issue_types = []

        for issue_type in project_issue_types:
            all_issue_type_ids.add(issue_type["id"])

    fieldtypes = []

    # Gets all field types for all issuetypes for every project
    for project in projects:
        for id in all_issue_type_ids:
            fieldtype_list = []
            if jira._version >= (8, 4, 0):
                fieldtype_list = jira.createmeta_fieldtypes(project, id)["values"]
            else:
                if (
                    len(
                        jira.createmeta(
                            projectKeys=project,
                            issuetypeIds=id,
                            expand="projects.issuetypes.fields",
                        )["projects"]
                    )
                    > 0
                ) and (
                    len(
                        jira.createmeta(
                            projectKeys=project,
                            issuetypeIds=id,
                            expand="projects.issuetypes.fields",
                        )["projects"][0]["issuetypes"]
                    )
                    > 0
                ):
                    # Converting all the jira 7 fieldtypes to jira 8 style
                    jira_7_fieldtypes: dict = jira.createmeta(
                        projectKeys=project,
                        issuetypeIds=id,
                        expand="projects.issuetypes.fields",
                    )["projects"][0]["issuetypes"][0]["fields"]

                    for (
                        jira_7_fieldtype_key,
                        jira_7_fieldtype_value,
                    ) in jira_7_fieldtypes.items():
                        temp_fieldtype = {
                            "fieldId": jira_7_fieldtype_key,
                            "name": jira_7_fieldtype_value["name"],
                            "schema": jira_7_fieldtype_value["schema"]
                            if jira_7_fieldtype_value["schema"] is not None
                            else None,
                        }

                        if "allowedValues" in jira_7_fieldtype_value:
                            temp_fieldtype["allowedValues"] = jira_7_fieldtype_value[
                                "allowedValues"
                            ]
                        else:
                            temp_fieldtype["allowedValues"] = []
                        fieldtype_list.append(temp_fieldtype)

            fieldtypes.append(fieldtype_list)

    # Extracts the value from all the select and multiselect lists and filter for duplicate lists
    for fieldtype in fieldtypes:
        for item in fieldtype:
            if "custom" in item["schema"].keys():
                if (
                    item["schema"]["custom"]
                    == "com.atlassian.jira.plugin.system.customfieldtypes:select"
                    or item["schema"]["custom"]
                    == "com.atlassian.jira.plugin.system.customfieldtypes:multiselect"
                ):
                    list_exists = next(
                        filter(
                            (lambda x: x["FieldId"] == item["fieldId"]),
                            outdict["customlists"],
                        ),
                        None,
                    )
                    if not list_exists:
                        to_add = {}
                        to_add["Name"] = item["name"]
                        to_add["FieldId"] = item["fieldId"]
                        to_add["Values"] = item["allowedValues"]
                        outdict["customlists"].append(to_add)

    json.dump(outdict, output_file_handle, indent=4)

    print("Extraction of lists complete")

    return len(outdict["customlists"])
