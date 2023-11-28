import json
import base64
from spira import Spira
from jira import JIRA
from utility import pretty_print


def update_artifacts(spira: Spira, spira_project_number, input_file_handle, jira: JIRA):
    print("Spira input supplied through:" + input_file_handle.name)
    to_spira = json.load(input_file_handle)
    print("Spira input loaded")

    print("Starting upload to spira...")

    artifacts = to_spira["artifacts"]
    update_action = to_spira["update_action"]

    if (update_action) == "association":
        print("Associations found and to be inserted: " + str(len(artifacts)))
        print(
            "Associations not migrated belongs to issues not migrated to spira yet or association already exist in spira"
        )
        for item in artifacts:
            spira.add_association(int(spira_project_number), item["payload"])

    elif (update_action) == "comment":
        comments_found = len(artifacts)
        print("Comments found and to be inserted: " + str(len(artifacts)))
        for item in artifacts:
            if item["artifacttype"] == 1:
                try:
                    spira.create_requirement_comment(
                        int(spira_project_number),
                        item["payload"]["ArtifactId"],
                        item["payload"],
                    )
                except Exception as e:
                    comments_found -= 1
                    print(e)
                    print(
                        "An error occured when trying to insert the task artifact with data:"
                    )
                    pretty_print(item["payload"])

            elif item["artifacttype"] == 3:
                try:
                    spira.create_incident_comment(
                        int(spira_project_number),
                        item["payload"]["ArtifactId"],
                        item["payload"],
                    )
                except Exception as e:
                    comments_found -= 1
                    print(e)
                    print(
                        "An error occured when trying to insert the task artifact with data:"
                    )
                    pretty_print(item["payload"])
            elif item["artifacttype"] == 6:
                try:
                    spira.create_task_comment(
                        int(spira_project_number),
                        item["payload"]["ArtifactId"],
                        item["payload"],
                    )
                except Exception as e:
                    comments_found -= 1
                    print(e)
                    print(
                        "An error occured when trying to insert the task artifact with data:"
                    )
                    pretty_print(item["payload"])
        return comments_found
    elif (update_action) == "document":
        documents_found = len(artifacts)
        print("Documents found and to be inserted: " + str(documents_found))
        for item in artifacts:
            try:
                id = item["document_id"]
                attachment = jira.attachment(id)
                jira_document = attachment.get()

                # Encode the byte string from jira and then decode it to a string
                item["payload"]["BinaryData"] = base64.b64encode(jira_document).decode()

                try:
                    spira.add_document(int(spira_project_number), item["payload"])

                except Exception as x:
                    documents_found -= 1
                    print(x)
                    print(
                        "An error occured when trying to insert the document to spira:"
                    )
                    pretty_print(item["payload"])

            except Exception as e:
                documents_found -= 1
                print(e)
                print("An error occured when trying to fetch the document from jira:")
                pretty_print(item["payload"])

        return documents_found

    elif (update_action) == "add_document_association":
        documents_found = len(artifacts)
        print("Documents found and to be inserted: " + str(documents_found))

        for item in artifacts:
            try:
                id = item["AttachmentId"]
                artifact_type_id = item["artifact_id_data"]["artifact_type_id"]
                artifact_id = item["artifact_id_data"]["artifact_id"]

                spira.add_artifact_document_association(
                    int(spira_project_number), artifact_type_id, artifact_id, id
                )

            except Exception as e:
                documents_found -= 1
                print(e)
                print(
                    "An error occured when trying to attach the artifact to the document, artifact could be a capability :"
                )
                pretty_print(item)

        return documents_found
