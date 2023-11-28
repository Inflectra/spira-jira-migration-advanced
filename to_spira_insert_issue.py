import json
from spira import Spira
from utility import pretty_print


def insert_issue_to_spira(
    spira: Spira,
    spira_metadata,
    input_file_handle,
    all_requirements_in_spira,
):  # All artifacts not only requirements
    print("Spira input supplied through: " + input_file_handle.name)
    to_spira = json.load(input_file_handle)
    print("Spira input loaded")

    print("Starting upload to spira...")

    product = to_spira["product"]

    all_capabilites_program = spira_metadata["capabilites"]

    artifacts_processed = len(product)

    print("Artifacts found and to be inserted: " + str(len(product)))
    print("If the number of artifacts are high, this might take a while")

    # This will probably take some time, so e.g. "Rich" library should be added to have a progress bar
    # Logging to a file should also be here, so the user can lookup what actually happened
    for artifact in product:
        if artifact["artifact_type"] == "requirement":
            inserted_requirement = {}
            try:
                parent_id = get_spira_id_from_jira_id(
                    all_requirements_in_spira, artifact["epiclink"]
                )
                if parent_id is None:
                    parent_id = get_spira_id_from_jira_id(
                        all_requirements_in_spira, artifact["parentlink"]
                    )

                if parent_id is None:
                    inserted_requirement = spira.create_requirement(
                        int(spira_metadata["project"]["ProjectId"]), artifact["payload"]
                    )
                else:
                    inserted_requirement = spira.create_child_requirement(
                        int(spira_metadata["project"]["ProjectId"]),
                        parent_id,
                        artifact["payload"],
                    )

            except Exception as e:
                artifacts_processed -= 1
                print(e)
                print(
                    "An error occured when trying to insert the requirement artifact with data:"
                )
                pretty_print(artifact)

            if bool(inserted_requirement):
                try:
                    capability_id = get_capability_spira_id_from_jira_id(
                        all_capabilites_program,
                        artifact["epiclink"],
                        artifact["parentlink"],
                    )

                    if capability_id is not None:
                        spira.add_capability_requirement_association(
                            spira_metadata["project"]["ProjectGroupId"],
                            capability_id,
                            inserted_requirement["RequirementId"],
                        )

                except Exception as e:
                    print(e)
                    print(
                        "An error occured when trying to associate a requirement with a capability:"
                    )
                    print(
                        "RequirementId: " + str(inserted_requirement["RequirementId"])
                    )

        elif artifact["artifact_type"] == "task":
            try:
                spira.create_task(
                    int(spira_metadata["project"]["ProjectId"]), artifact["payload"]
                )
            except Exception as e:
                artifacts_processed -= 1
                print(e)
                print(
                    "An error occured when trying to insert the task artifact with data:"
                )
                pretty_print(artifact)
        elif artifact["artifact_type"] == "incident":
            try:
                spira.create_incident(
                    int(spira_metadata["project"]["ProjectId"]), artifact["payload"]
                )
            except Exception as e:
                artifacts_processed -= 1
                print(e)
                print(
                    "An error occured when trying to insert the incident artifact with data:"
                )
                pretty_print(artifact)
        else:
            print("Artifact unrecognized, with data:")
            pretty_print(artifact)

    return artifacts_processed


def get_spira_id_from_jira_id(all_requirements_in_spira, link_jira_id):
    for requirement in all_requirements_in_spira:
        property = next(
            filter(
                (
                    lambda x: x["Definition"]["Name"] == "Jira Id"
                    and x["StringValue"] == link_jira_id
                ),
                requirement["CustomProperties"],
            ),
            None,
        )
        if property is not None:
            return requirement["RequirementId"]

    return None


def get_capability_spira_id_from_jira_id(all_capabilites, epicid, parentid):
    for capability in all_capabilites:
        property = next(
            filter(
                (
                    lambda x: x["Definition"]["Name"] == "Jira Id"
                    and x["StringValue"] == parentid
                ),
                capability["CustomProperties"],
            ),
            None,
        )

        if property is not None:
            return capability["CapabilityId"]

        property = next(
            filter(
                (
                    lambda x: x["Definition"]["Name"] == "Jira Id"
                    and x["StringValue"] == epicid
                ),
                capability["CustomProperties"],
            ),
            None,
        )
        if property is not None:
            return capability["CapabilityId"]

    return None
