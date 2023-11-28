import json
import re
from spira import Spira
from utility import pretty_print


def insert_releases_to_spira(
    spira: Spira, spira_metadata, input_file_handle, spira_release_dict
) -> int:
    print("Spira releases input supplied through: " + input_file_handle.name)
    releases_to_spira = json.load(input_file_handle)
    print("Spira input loaded")

    print("Starting upload to spira...")

    releases = releases_to_spira["releases"]

    # Sort parent and child releases in separate lists
    parent_releases = list(filter((lambda x: x["is_parent"] is True), releases))  # type: ignore
    child_releases = list(filter((lambda x: x["is_parent"] is False), releases))  # type: ignore

    releases_processed = len(releases)

    # Adds parent releases first
    for release in parent_releases:
        try:
            response = spira.create_release(
                int(spira_metadata["project"]["ProjectId"]), release["payload"]  # type: ignore
            )

            project_release = {
                "Name": response["Name"],
                "VersionNumber": re.findall(r"\d+", response["Name"]),
                "ReleaseId": response["ReleaseId"],
            }

            spira_release_dict["releases"].append(project_release)

        except Exception as e:
            releases_processed -= 1
            print(e)
            print(
                "An error occured when trying to insert the requirement artifact with data:"
            )
            pretty_print(release)

    for release in child_releases:
        # Look for parent release
        parent_release_id = find_parent_release(release, spira_release_dict)

        if parent_release_id is not None:
            try:
                spira.create_child_release(
                    int(spira_metadata["project"]["ProjectId"]),
                    parent_release_id,
                    release["payload"],  # type: ignore
                )
            except Exception as e:
                releases_processed -= 1
                print(e)
                print(
                    "An error occured when trying to insert the requirement artifact with data:"
                )
                pretty_print(release)
        else:
            try:
                spira.create_release(
                    int(spira_metadata["project"]["ProjectId"]), release["payload"]  # type: ignore
                )
            except Exception as e:
                releases_processed -= 1
                print(e)
                print(
                    "An error occured when trying to insert the requirement artifact with data:"
                )
                pretty_print(release)

    print("Releases found and to be inserted: " + str(releases_processed))
    print("If the number of artifacts are high, this might take a while")

    return releases_processed


def insert_components_to_spira(spira: Spira, spira_metadata, input_file_handle) -> int:
    print("Spira components input supplied through" + input_file_handle.name)
    components_to_spira = json.load(input_file_handle)
    print("Spira input loaded")

    print("Starting to upload to spira...")

    components = components_to_spira["components"]

    components_processed = len(components)

    print("Components found and to be inserted: " + str(components_processed))
    print("If the number of artifacts are high, this might take a while")

    for component in components:
        try:
            spira.create_component(
                int(spira_metadata["project"]["ProjectId"]), component["payload"]
            )
        except Exception as e:
            components_processed -= 1
            print(e)
            print(
                "An error occured when trying to insert the requirement artifact with data:"
            )
            pretty_print(component)

    return components_processed


def insert_lists_to_spira(
    spira: Spira, input_file_handle, system_level, spira_template_ids
):
    print("Spira customlists input supplied through" + input_file_handle.name)
    customlists_to_spira = json.load(input_file_handle)
    print("Spira input loaded")

    print("Starting to upload to spira...")

    customlists = customlists_to_spira["customlists"]

    customlists_processed = len(customlists)

    print(
        "Customlists found and to be inserted at template- or at system level: "
        + str(len(customlists))
    )

    if system_level:
        for customlist in customlists:
            try:
                spira.create_system_customlist(
                    customlist["payload"],
                )
            except Exception as e:
                customlists_processed -= 1
                print(e)
                print(
                    "An error occured when trying to insert the customlist at system level:"
                )
                pretty_print(str(customlist))
    else:
        for id in spira_template_ids:
            for customlist in customlists:
                try:
                    spira.create_project_template_customlist(
                        id,
                        customlist["payload"],
                    )
                except Exception as e:
                    customlists_processed -= 1
                    print(e)
                    print(
                        "An error occured when trying to insert the customlist at project level:"
                    )
                    pretty_print(str(customlist))

    return customlists_processed


def find_parent_release(release, spira_release_dict):
    # Sort out all numbers in the version name
    child_release_version = re.findall(r"\d+", release["payload"]["Name"])

    # Looks for a release that match first and second position and assume that this is the parent
    if len(child_release_version) > 1:
        for parent_release in spira_release_dict["releases"]:
            if (
                len(parent_release["VersionNumber"]) > 1
                and child_release_version[0] == parent_release["VersionNumber"][0]
                and child_release_version[1] == parent_release["VersionNumber"][1]
            ):
                return parent_release["ReleaseId"]

    return None
