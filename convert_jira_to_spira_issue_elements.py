from spira import Spira
from utility import convert_jira_markup_to_html
from convert_jira_to_spira_issues import (
    jira_string_field_to_spira_custom_prop,
    jira_datetime_field_to_spira_custom_prop,
)
import json


def convert_jira_to_spira_issue_elements(
    jira_connection_dict,
    skip_ssl,
    jira_output_dict,
    mapping_dict,
    all_artifacts_in_spira,
    action,
    spira: Spira,
    spira_metadata={},
    jira_metadata={},
):
    print("Starting conversion")

    to_validate = open("temp/to_spira.json", "w")

    validation_dict = {"update_action": "", "artifacts": []}

    issues = jira_output_dict["issues"]
    issues_with_outward_links = []
    all_outward_links = []

    if action == "associations":
        # For all issues found
        for issue in issues:
            # Check if issue has any links
            if issue["fields"]["issuelinks"]:
                # If there are links check which of those are outward links
                for link in issue["fields"]["issuelinks"]:
                    artifact = {"project_id": mapping_dict["spira_product_id"]}
                    if "outwardIssue" in link.keys():
                        source_id_data = get_artifact_id_data_from_jira_id(
                            issue["key"], all_artifacts_in_spira
                        )
                        dest_id_data = get_artifact_id_data_from_jira_id(
                            link["outwardIssue"]["key"], all_artifacts_in_spira
                        )
                        issues_with_outward_links.append(issue["key"])
                        all_outward_links.append(link["outwardIssue"]["key"])

                        if source_id_data and dest_id_data:
                            payload = {
                                # "ArtifactLinkId":None,
                                "SourceArtifactId": source_id_data["artifact_id"],
                                "SourceArtifactTypeId": source_id_data[
                                    "artifact_type_id"
                                ],
                                "DestArtifactId": dest_id_data["artifact_id"],
                                "DestArtifactTypeId": dest_id_data["artifact_type_id"],
                                "ArtifactLinkTypeId": 1,  # At the moment they will all be set to "relates to"
                                # "CreatorId":None,
                                "Comment": link["type"]["outward"],
                                # "CreationDate":None,
                                # "DestArtifactName":None,
                                # "DestArtifactTypeName":None,
                                # "CreatorName":None,
                                # "ArtifactLinkTypeName":None,
                                # "Guid":None,
                                # "ConcurrencyGuid":None,
                                # "LastUpdateDate":None
                            }

                            validation_dict["update_action"] = "association"
                            artifact["payload"] = payload
                            validation_dict["artifacts"].append(artifact)

        print(
            "Found "
            + str(len(list(set(issues_with_outward_links))))
            + " issues with at total of "
            + str(len(all_outward_links))
            + "links"
        )

    elif action == "comments":
        # For all issues found
        for issue in issues:
            # Check if issue has any links
            if issue["fields"]["comment"]["comments"]:
                # If there are links check which of those are outward links
                for comment in issue["fields"]["comment"]["comments"]:
                    artifact = {"project_id": mapping_dict["spira_product_id"]}
                    source_id_data = get_artifact_id_data_from_jira_id(
                        issue["key"], all_artifacts_in_spira
                    )
                    userinfo = get_user_info_from_email(
                        comment["author"]["emailAddress"], spira_metadata["users"]
                    )
                    if source_id_data:
                        payload = {
                            # "CommentId":None, ReadOnly
                            "ArtifactId": source_id_data["artifact_id"],
                            # "Guid":None,
                            "UserId": userinfo["spira_id"],
                            # "UserGuid":None,
                            "UserName": userinfo["name"],
                            "Text": convert_jira_markup_to_html(
                                jira_connection_dict, skip_ssl, comment["body"]
                            ),
                            # "CreationDate":None,
                            # "IsDeleted":False,
                            # "IsPermanent":False
                        }

                        validation_dict["update_action"] = "comment"
                        artifact["artifacttype"] = source_id_data["artifact_type_id"]
                        artifact["payload"] = payload
                        validation_dict["artifacts"].append(artifact)

    elif action == "documents":
        print("Check for attachment folder")
        all_folders = spira_metadata["document_folders"]
        folder = get_folder(all_folders, "Attachments")
        if folder is None:
            print("Creates attachment folder")
            folder = create_folder(
                spira,
                mapping_dict["spira_product_id"],
                all_folders,
                "Attachments",
            )
            spira_metadata["document_folders"].append(folder)

        # For all issues found
        for issue in issues:
            # Check if issue has any documents
            if issue["fields"]["attachment"]:
                for document in issue["fields"]["attachment"]:
                    artifact = {"project_id": mapping_dict["spira_product_id"]}
                    source_id_data = get_artifact_id_data_from_jira_id(
                        issue["key"], all_artifacts_in_spira
                    )
                    userinfo = get_user_info_from_email(
                        document["author"]["emailAddress"], spira_metadata["users"]
                    )
                    payload = {
                        "BinaryData": None,
                        "AttachmentId": None,
                        "AttachmentTypeId": 1,  # 1 is for file 2 is for url
                        # DocumentTypeId": None,
                        "DocumentStatusId": None,
                        "ProjectAttachmentFolderId": folder[
                            "ProjectAttachmentFolderId"
                        ],
                        "AttachedArtifacts": get_attached_artifact(source_id_data),
                        "AuthorId": userinfo["spira_id"],
                        # "EditorId":None,
                        # "AuthorGuid":None,
                        # "EditorGuid":None,
                        "FilenameOrUrl": document["filename"],  # MANDATORY
                        # Description": "",
                        # "UploadDate":"0001-01-01T00:00:00",
                        # "EditedDate":"0001-01-01T00:00:00",
                        # "CurrentVersion":None,
                        # "Versions":None,
                        # "DocumentTypeName":None,
                        # "DocumentStatusName":None,
                        # "AttachmentTypeName":None,
                        # "AuthorName": userinfo,
                        # "EditorName":None,
                        # "ProjectId":0,
                        # "ProjectGuid":None,
                        # "ArtifactTypeId":0,
                        # "ConcurrencyDate":"0001-01-01T00:00:00",
                        # "CustomProperties":None, #LÄGG TILL JIRA ID, CREATED
                        # "IsAttachments":False,
                        # "Tags":None,
                        # "Guid":None
                    }

                    # Add all the custom properties
                    payload["CustomProperties"] = add_document_custom_properties(
                        spira_metadata,
                        "document",
                        issue,
                        document["created"],
                    )

                    validation_dict["update_action"] = "document"

                    if source_id_data:
                        artifact["artifacttype"] = source_id_data["artifact_type_id"]

                    artifact["jira_attachment_url"] = document["content"]
                    artifact["document_id"] = document["id"]
                    artifact["payload"] = payload
                    validation_dict["artifacts"].append(artifact)

    json.dump(validation_dict, to_validate, indent=4)
    to_validate.close()


def get_artifact_id_data_from_jira_id(jira_id, all_artifacts_in_spira):
    for artifact in all_artifacts_in_spira:
        property = next(
            filter(
                (
                    lambda x: x["Definition"]["Name"] == "Jira Id"
                    and x["StringValue"] == jira_id
                ),
                artifact["CustomProperties"],
            ),
            None,
        )
        if property is not None:
            artifact_type_id = artifact["ArtifactTypeId"]
            artifact_id = next(iter(artifact.values()))

            return {"artifact_type_id": artifact_type_id, "artifact_id": artifact_id}

    return None


def get_user_info_from_email(email, all_users_in_spira):
    for user in all_users_in_spira:
        if email == user["EmailAddress"]:
            return {
                "spira_id": user["UserId"],
                "name": user["FirstName"] + " " + user["LastName"],
            }

    return {"spira_id": "", "name": ""}


def add_document_custom_properties(spira_metadata, artifact_type, issue, time):
    custom_properties = [
        # Special case for Jira id as it's not in the fields part of the issue
        jira_string_field_to_spira_custom_prop(
            spira_metadata, artifact_type, "Jira Id", issue["key"]
        )
    ]

    custom_prop_to_add = jira_datetime_field_to_spira_custom_prop(
        spira_metadata, artifact_type, "Created", time
    )

    custom_properties.append(custom_prop_to_add)

    return custom_properties


def get_folder(folders, folder_name):
    folder = next(
        filter(
            (lambda x: x["Name"] == folder_name),
            folders,
        ),
        None,
    )
    return folder


def create_folder(spira: Spira, project_id, folders, folder_name):
    folders = spira.get_all_document_folders(project_id)
    parent_folder = next(
        filter(
            (lambda x: x["Name"] == "Root Folder"),
            folders,
        )
    )
    payload = {
        "ParentProjectAttachmentFolderId": parent_folder["ProjectAttachmentFolderId"],
        "Name": folder_name,
    }

    return spira.add_document_folder(project_id, payload)


def get_attached_artifact(source_id_data):
    artifacts = []
    if source_id_data:
        artifacts.append(
            {
                "ArtifactId": source_id_data["artifact_id"],
                "ArtifactTypeId": source_id_data["artifact_type_id"],
            }
        )
    return artifacts
