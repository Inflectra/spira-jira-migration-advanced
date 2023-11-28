from convert_jira_to_spira_issue_elements import get_artifact_id_data_from_jira_id
import json


def convert_spira_data_for_spira_updates(
    all_documents_in_spira, all_artifacts_in_spira, action, spira_metadata
):
    print("Starting conversion")

    to_validate = open("temp/to_spira.json", "w")

    validation_dict = {"update_action": "", "artifacts": []}
    if action == "add_document_association":
        for document in all_documents_in_spira:
            property = next(
                filter(
                    (lambda x: x["Definition"]["Name"] == "Jira Id"),
                    document["CustomProperties"],
                ),
                None,
            )

            if property:
                artifact_id_data = get_artifact_id_data_from_jira_id(
                    property["StringValue"], all_artifacts_in_spira
                )
                document["artifact_id_data"] = artifact_id_data
                validation_dict["update_action"] = "add_document_association"
                validation_dict["artifacts"].append(document)

    json.dump(validation_dict, to_validate, indent=4)
    to_validate.close()
