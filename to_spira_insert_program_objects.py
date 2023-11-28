import json
from spira import Spira
from utility import pretty_print



def insert_milestones_to_spira(spira: Spira, spira_metadata, input_file_handle) -> int:
    print("Spira milestones input supplied through: " + input_file_handle.name)
    milestones_to_spira = json.load(input_file_handle)
    print("Spira input loaded")

    print("Starting upload to spira...")

    milestones = milestones_to_spira["milestones"]

    milestones_processed = len(milestones)

    print("Milestones found and to be inserted: " + str(milestones_processed))
    print("If the number of milestones are high, this might take a while")

    for milestone in milestones:
        try:
            spira.create_program_milestone(
                int(spira_metadata["program"]["program_id"]), milestone["payload"]
            )
        except Exception as e:
            milestones_processed -= 1
            print(e)
            print(
                "An error occured when trying to insert the program milestone with data:"
            )
            pretty_print(milestone)
    return milestones_processed


def insert_capabilities_to_spira(
    spira: Spira, spira_metadata, input_file_handle, all_capabilies_in_spira
):
    print("Spira input suppled through: " + input_file_handle.name)
    capabilities_to_spira = json.load(input_file_handle)
    print("Spira input loaded")

    print("Starting upload to spira...")

    program = capabilities_to_spira["program"]

    capabilities_processed = len(program)

    print("Capabilities found and to be inserted: " + str(capabilities_processed))
    print("If the number of milestones are high, this might take a while")

    for capability in program:
        try:
            parent_id = get_spira_id_from_jira_id(
                all_capabilies_in_spira, capability["epic_link"]
            )
            if parent_id is None:
                parent_id = get_spira_id_from_jira_id(
                    all_capabilies_in_spira, capability["parent_link"]
                )

            if parent_id is None:
                spira.create_capability(
                    spira_metadata["program"]["program_id"], capability["payload"]
                )
            else:
                spira.create_child_capability(
                    spira_metadata["program"]["program_id"],
                    parent_id,
                    capability["payload"],
                )
        except Exception as e:
            capabilities_processed -= 1
            print(e)
            print("An error occured when trying to insert the capability with data:")
            pretty_print(capability)
    return capabilities_processed


def get_spira_id_from_jira_id(all_capabilies_in_spira, link_jira_id):
    for requirement in all_capabilies_in_spira:
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
            return requirement["CapabilityId"]

    return None
