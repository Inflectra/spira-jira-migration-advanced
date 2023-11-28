import argparse, json, sys, os
import yaml
import re
import itertools
from jira import JIRA
from convert_jira_to_spira_program import (
    convert_jira_issues_to_spira_program_capabilities,
    convert_jira_versions_to_spira_program_milestones,
)
from jira_to_json import (
    jira_components_to_json,
    jira_customlists_to_json,
    jira_to_json,
    jira_versions_to_json,
)

from spira import Spira
from convert_jira_to_spira_issues import convert_jira_to_spira_issues
from convert_jira_to_spira_issue_elements import convert_jira_to_spira_issue_elements
from convert_spira_data_for_spira_updates import convert_spira_data_for_spira_updates
from convert_jira_to_spira_project_objects import (
    convert_jira_to_spira_releases,
    convert_jira_to_spira_components,
    convert_jira_to_spira_customlists,
)
from to_spira_insert_issue import insert_issue_to_spira
from to_spira_insert_program_objects import (
    insert_milestones_to_spira,
    insert_capabilities_to_spira,
)
from to_spira_update_artifact import update_artifacts
from to_spira_insert_project_objects import (
    insert_releases_to_spira,
    insert_components_to_spira,
    insert_lists_to_spira,
)
from clean_spira import (
    clean_spira_product,
    clean_spira_program,
    clean_spira_product_documents,
)
from typing import Any, Dict

from utility import combine_jira_types

# Load env variables from .env file
from dotenv import load_dotenv

load_dotenv()

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def main():
    parser = argparse.ArgumentParser(
        description="Migrate issues, versions, and components from Jira to Spira with optional advanced settings and mappings"
    )
    subparsers = parser.add_subparsers(dest="command")

    # ------------------------------------------------------
    # Full issue migration flow to a product with defaults
    # ------------------------------------------------------
    parser_migrate_issues = subparsers.add_parser(
        "migrate_issues",
        help="Run the full issue migration flow to a product with defaults",
    )

    parser_migrate_issues.add_argument(
        "spira_product_identifier",
        help="The full, exact, and case sensitive name of the spira product, or the product id as an integer.",
    )

    parser_migrate_issues.add_argument(
        "jql",
        help="The jira jql that the argument will use to query issues from the specified jira instance",
    )

    ## Jira to spira mapping file
    parser_migrate_issues.add_argument(
        "-m",
        "--mapping",
        help="The jira-to-spira mapping file based on the template in the mapping_template.yaml file, which is also the default parameter.",
        type=argparse.FileType("r", encoding="UTF-8"),
        default="mapping_template.yaml",
    )

    ## Output file for outputting json file from jira
    parser_migrate_issues.add_argument(
        "-jo",
        "--jira-to-json-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_output.json",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_migrate_issues.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Full issue migration flow to a program with defaults
    # ------------------------------------------------------
    parser_migrate_capabilities = subparsers.add_parser(
        "migrate_capabilities",
        help="Run the full issue migration flow to a program with defaults",
    )

    parser_migrate_capabilities.add_argument(
        "spira_program_identifier",
        help="The full, exact, and case sensitive name of the spira program, or the program id as an integer.",
    )

    parser_migrate_capabilities.add_argument(
        "jql",
        help="The jira jql that the argument will use to query issues from the specified jira instance",
    )

    ## Jira to spira mapping file
    parser_migrate_capabilities.add_argument(
        "-m",
        "--mapping",
        help="The jira-to-spira mapping file based on the template in the mapping_template.yaml file, which is also the default parameter.",
        type=argparse.FileType("r", encoding="UTF-8"),
        default="mapping_template.yaml",
    )

    ## Output file for outputting json file from jira
    parser_migrate_capabilities.add_argument(
        "-jo",
        "--jira-to-json-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_output.json",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_migrate_capabilities.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Document migration flow with defaults
    # ------------------------------------------------------
    parser_migrate_documents = subparsers.add_parser(
        "migrate_documents", help="Run the documents migration flow with defaults"
    )

    parser_migrate_documents.add_argument(
        "spira_product_identifier",
        help="The full, exact, and case sensitive name of the spira product, or the product id as an integer.",
    )

    parser_migrate_documents.add_argument(
        "jql",
        help="The jira jql that the argument will use to query issues from the specified jira instance",
    )

    ## Jira to spira mapping file
    parser_migrate_documents.add_argument(
        "-m",
        "--mapping",
        help="The jira-to-spira mapping file based on the template in the mapping_template.yaml file, which is also the default parameter.",
        type=argparse.FileType("r", encoding="UTF-8"),
        default="mapping_template.yaml",
    )

    ## Output file for outputting json file from jira
    parser_migrate_documents.add_argument(
        "-jo",
        "--jira-to-json-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_output.json",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_migrate_documents.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Update document migration flow with defaults
    # ------------------------------------------------------
    parser_add_document_associations = subparsers.add_parser(
        "add_document_associations",
        help="Run the add document association flow with defaults",
    )

    parser_add_document_associations.add_argument(
        "spira_product_identifier",
        help="The full, exact, and case sensitive name of the spira product, or the product id as an integer.",
    )

    ## Jira to spira mapping file
    parser_add_document_associations.add_argument(
        "-m",
        "--mapping",
        help="The jira-to-spira mapping file based on the template in the mapping_template.yaml file, which is also the default parameter.",
        type=argparse.FileType("r", encoding="UTF-8"),
        default="mapping_template.yaml",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_add_document_associations.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Comment migration flow with defaults
    # ------------------------------------------------------
    parser_migrate_comments = subparsers.add_parser(
        "migrate_comments", help="Run the comments migration flow with defaults"
    )

    parser_migrate_comments.add_argument(
        "spira_product_identifier",
        help="The full, exact, and case sensitive name of the spira product, or the product id as an integer.",
    )

    parser_migrate_comments.add_argument(
        "jql",
        help="The jira jql that the argument will use to query issues from the specified jira instance",
    )

    ## Jira to spira mapping file
    parser_migrate_comments.add_argument(
        "-m",
        "--mapping",
        help="The jira-to-spira mapping file based on the template in the mapping_template.yaml file, which is also the default parameter.",
        type=argparse.FileType("r", encoding="UTF-8"),
        default="mapping_template.yaml",
    )

    ## Output file for outputting json file from jira
    parser_migrate_comments.add_argument(
        "-jo",
        "--jira-to-json-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_output.json",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_migrate_comments.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Association migration flow with defaults
    # ------------------------------------------------------
    parser_migrate_associations = subparsers.add_parser(
        "migrate_associations", help="Run the association migration flow with defaults"
    )

    parser_migrate_associations.add_argument(
        "spira_product_identifier",
        help="The full, exact, and case sensitive name of the spira product, or the product id as an integer.",
    )

    parser_migrate_associations.add_argument(
        "jql",
        help="The jira jql that the argument will use to query issues from the specified jira instance",
    )

    ## Jira to spira mapping file
    parser_migrate_associations.add_argument(
        "-m",
        "--mapping",
        help="The jira-to-spira mapping file based on the template in the mapping_template.yaml file, which is also the default parameter.",
        type=argparse.FileType("r", encoding="UTF-8"),
        default="mapping_template.yaml",
    )

    ## Output file for outputting json file from jira
    parser_migrate_associations.add_argument(
        "-jo",
        "--jira-to-json-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_output.json",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_migrate_associations.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Releases migration flow with defaults
    # ------------------------------------------------------
    parser_migrate_releases = subparsers.add_parser(
        "migrate_releases", help="Run the releases migration flow with defaults"
    )

    parser_migrate_releases.add_argument(
        "spira_product_identifier",
        help="The full, exact, and case sensitive name of the spira product, or the product id as an integer.",
    )

    parser_migrate_releases.add_argument(
        "jira_projects",
        help="The jira projects that the argument will use to query jira versions from the specified jira instance",
        nargs="+",
    )

    ## Jira to spira mapping file
    parser_migrate_releases.add_argument(
        "-m",
        "--mapping",
        help="The jira-to-spira mapping file based on the template in the mapping_template.yaml file, which is also the default parameter.",
        type=argparse.FileType("r", encoding="UTF-8"),
        default="mapping_template.yaml",
    )

    ## Output file for outputting json file from jira
    parser_migrate_releases.add_argument(
        "-jo",
        "--jira-to-json-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_versions_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_versions_output.json",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_migrate_releases.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Milestones migration flow with defaults
    # ------------------------------------------------------
    parser_migrate_milestones = subparsers.add_parser(
        "migrate_milestones", help="Run the milestones migration flow with defaults"
    )

    parser_migrate_milestones.add_argument(
        "spira_program_identifier",
        help="The full, exact, and case sensitive name of the spira program, or the program id as an integer.",
    )

    parser_migrate_milestones.add_argument(
        "jql",
        help="The jira jql that the argument will use to query issues from the specified jira instance",
    )

    parser_migrate_milestones.add_argument(
        "jira_projects",
        help="The jira projects that the argument will use to query jira versions from the specified jira instance",
        nargs="+",
    )

    ## Jira to spira mapping file
    parser_migrate_milestones.add_argument(
        "-m",
        "--mapping",
        help="The jira-to-spira mapping file based on the template in the mapping_template.yaml file, which is also the default parameter.",
        type=argparse.FileType("r", encoding="UTF-8"),
        default="mapping_template.yaml",
    )

    ## Output file for outputting issue json file from jira
    parser_migrate_milestones.add_argument(
        "-jo",
        "--jira-to-json-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_output.json",
    )

    ## Output file for outputting versions json file from jira
    parser_migrate_milestones.add_argument(
        "-jov",
        "--jira-to-json-version-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_versions_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_versions_output.json",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_migrate_milestones.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Components migration flow with defaults
    # ------------------------------------------------------
    parser_migrate_components = subparsers.add_parser(
        "migrate_components", help="Run the components migration flow with defaults"
    )

    parser_migrate_components.add_argument(
        "spira_product_identifier",
        help="The full, exact, and case sensitive name of the spira product, or the product id as an integer.",
    )

    parser_migrate_components.add_argument(
        "jira_projects",
        help="The jira projects that the argument will use to query jira versions from the specified jira instance",
        nargs="+",
    )

    ## Jira to spira mapping file
    parser_migrate_components.add_argument(
        "-m",
        "--mapping",
        help="The jira-to-spira mapping file based on the template in the mapping_template.yaml file, which is also the default parameter.",
        type=argparse.FileType("r", encoding="UTF-8"),
        default="mapping_template.yaml",
    )

    ## Output file for outputting json file from jira
    parser_migrate_components.add_argument(
        "-jo",
        "--jira-to-json-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_components_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_components_output.json",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_migrate_components.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Custom list migration with defaults
    # ------------------------------------------------------
    parser_migrate_customlists = subparsers.add_parser(
        "migrate_customlists", help="Run the components migration flow with defaults"
    )

    parser_migrate_customlists.add_argument(
        "jira_projects",
        help="The jira projects that the argument will use to query jira versions from the specified jira instance",
        nargs="+",
    )

    ## Output file for outputting json file from jira
    parser_migrate_customlists.add_argument(
        "-jo",
        "--jira-to-json-output",
        help="Output file and location for jira extraction to a json file. Default is 'jira_output.json' in the temp directory. As of right now changing this path will break the full migration flow",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="temp/jira_output.json",
    )

    # Arguments that will be set to a list of templates where the list will be inserted
    # TODO: SHOULD BE PRE FLIGHT CHECKED
    parser_migrate_customlists.add_argument(
        "-template",
        "--spira-templates",
        help="The spira templates names or numbers that the argument will use to insert the list",
        nargs="*",
    )

    ## Bool if it should migrate the lists to system level
    parser_migrate_customlists.add_argument(
        "-system",
        "--system-level",
        help="Migrate list globally at system level",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_migrate_customlists.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Clean a product from the spira instance automatically.
    # ------------------------------------------------------
    parser_clean_product = subparsers.add_parser(
        "clean_product",
        help="Clean the spira instance, removing all inserted values for components, releases, requirements, incidents, tasks, comments, associations, and document associations.",
    )

    parser_clean_product.add_argument(
        "spira_product_identifier",
        help="The full, exact, and case sensitive name of the spira product, or the product id as an integer.",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_clean_product.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ------------------------------------------------------
    # Clean a program from the spira instance automatically.
    # ------------------------------------------------------
    parser_clean_program = subparsers.add_parser(
        "clean_program",
        help="Clean a program from the spira instance, removing all inserted values for milestones and capabilities.",
    )

    parser_clean_program.add_argument(
        "spira_program_identifier",
        help="The full, exact, and case sensitive name of the spira program, or the program id as an integer.",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_clean_program.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # ---------------------------------------------------------------------
    # Clean the spira instance automatically of documents on product level
    # ---------------------------------------------------------------------
    parser_clean_product_documents = subparsers.add_parser(
        "clean_product_documents",
        help="Clean documents from a product in the spira instance, removing all documents and the folders.",
    )

    parser_clean_product_documents.add_argument(
        "spira_product_identifier",
        help="The full, exact, and case sensitive name of the spira product, or the product id as an integer.",
    )

    ## Bool if it should skip the ssl check when using the REST api routes
    parser_clean_product_documents.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on both the jira and spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    args = parser.parse_args()

    jira_connection_dict = {}
    spira_connection_dict = {}
    mapping_dict = {}

    jira: JIRA = Any
    spira: Spira = Any

    if args.command == "migrate_issues":
        print("Setting up migration flow...")

        # Set up some variables
        jira_connection_dict: Dict = get_jira_conn_dict()
        spira_connection_dict = get_spira_conn_dict()
        mapping_dict = get_mapping_dict(args.mapping)
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Initialize the instances
        jira = get_jira_instance(jira_connection_dict, skip_ssl)
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira product_id
        spira_product_id = get_spira_product_id_from_identifier(
            args.spira_product_identifier, spira
        )

        if spira_product_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        # Adding the spira_product_id to mapping dict
        mapping_dict["spira_product_id"] = spira_product_id

        # Extract the jira issues to a file
        print("Extracting the issues from jira...")
        total_number_of_issues = jira_to_json(jira, args.jira_to_json_output, args.jql)

        args.jira_to_json_output.close()

        # Get all the required data for migration
        print("Extracting metadata from jira...")
        jira_metadata = construct_jira_metadata(
            jira
        )  # only gets customfields metadata atm
        print("Jira metadata extraction complete.")

        print("Extracting metadata from spira...")
        spira_metadata = construct_spira_metadata(
            spira, mapping_dict["spira_product_id"]
        )
        print("Spira metadata extraction complete.")

        with open(args.jira_to_json_output.name, "r") as file:
            json_output_dict = json.load(file)

        # Counter for number of processed issues
        number_of_processed_issues = 0

        # Convert and insert types in order
        for jira_type in mapping_dict["artifact_type_order"]:
            print("------------------------------------------------------------")
            print("Processing issues of jira type: " + jira_type)
            print("------------------------------------------------------------")
            print(
                "Getting all newly added, if available, artifacts from spira to be able to infer data and connections..."
            )
            all_requirements_in_spira_project = spira.get_all_requirements(
                mapping_dict["spira_product_id"]
            )
            all_tasks_in_spira_project = spira.get_all_tasks(
                mapping_dict["spira_product_id"]
            )
            # TODO Add incidents and tasks aswell if needed

            # Check which artifact type and send the correct jira counterpart
            if jira_type in combine_jira_types(mapping_dict["types"]["requirements"]):
                convert_jira_to_spira_issues(
                    jira_connection_dict,
                    skip_ssl,
                    json_output_dict,
                    mapping_dict,
                    spira_metadata,
                    jira_metadata,
                    all_requirements_in_spira_project,
                    "requirements",
                    jira_type,
                )
            elif jira_type in combine_jira_types(mapping_dict["types"]["incidents"]):
                convert_jira_to_spira_issues(
                    jira_connection_dict,
                    skip_ssl,
                    json_output_dict,
                    mapping_dict,
                    spira_metadata,
                    jira_metadata,
                    all_requirements_in_spira_project,
                    "incidents",
                    jira_type,
                )
            elif jira_type in combine_jira_types(mapping_dict["types"]["tasks"]):
                convert_jira_to_spira_issues(
                    jira_connection_dict,
                    skip_ssl,
                    json_output_dict,
                    mapping_dict,
                    spira_metadata,
                    jira_metadata,
                    all_requirements_in_spira_project,
                    "tasks",
                    jira_type,
                )

            spira_input = open("temp/to_spira.json", "r")

            number_of_processed_issues += insert_issue_to_spira(spira, spira_metadata, spira_input, all_requirements_in_spira_project)  # type: ignore
            print("Migration of type " + jira_type + " finished.")

        print("--------------------------------------")
        print("Migration of issues complete")
        print(
            "Migration processed "
            + str(number_of_processed_issues)
            + " issues of a total "
            + str(total_number_of_issues)
            + " found from supplied jql query."
        )
        print(
            "If the values are mismatched, either this script does not have support for some of the issue types found in jira or the mapping is incorrectly set."
        )
        print("--------------------------------------")

    elif args.command == "migrate_capabilities":
        print("Setting up migration flow...")

        # Set up some variables
        jira_connection_dict: Dict = get_jira_conn_dict()
        spira_connection_dict = get_spira_conn_dict()
        mapping_dict = get_mapping_dict(args.mapping)
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Initialize the instances
        jira = get_jira_instance(jira_connection_dict, skip_ssl)
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira program_id
        spira_program_id = get_spira_program_id_from_identifier(
            args.spira_program_identifier, spira
        )

        if spira_program_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        # Adding the spira_program_id to mapping dict
        mapping_dict["spira_program_id"] = spira_program_id

        # Extract the jira issues to a file
        print("Extracting the issues from jira...")
        total_number_of_issues = jira_to_json(jira, args.jira_to_json_output, args.jql)

        args.jira_to_json_output.close()

        # Get all the required data for migration
        print("Extracting metadata from jira...")
        jira_metadata = construct_jira_metadata(
            jira
        )  # only gets customfields metadata atm
        print("Jira metadata extraction complete.")

        print("Extracting metadata from spira...")
        spira_metadata = construct_program_spira_metadata(
            spira, mapping_dict["spira_program_id"]
        )
        print("Spira metadata extraction complete.")

        with open(args.jira_to_json_output.name, "r") as file:
            json_output_dict = json.load(file)

        # Counter for number of processed issues
        number_of_processed_issues = 0

        # Convert and insert types in order
        for jira_type in mapping_dict["capability_type_order"]:
            print("------------------------------------------------------------")
            print("Processing issues of jira type: " + jira_type)
            print("------------------------------------------------------------")
            print(
                "Getting all newly added, if available, artifacts from spira to be able to infer data and connections..."
            )

            all_capabilites_in_spira_project = spira.get_all_program_capabilities(
                mapping_dict["spira_program_id"]
            )

            # Check which artifact type and send the correct jira counterpart
            if jira_type in combine_jira_types(mapping_dict["types"]["capabilities"]):
                convert_jira_issues_to_spira_program_capabilities(
                    jira_connection_dict,
                    skip_ssl,
                    json_output_dict,
                    mapping_dict,
                    spira_metadata,
                    jira_metadata,
                    jira_type,
                )

            spira_input = open("temp/capabilities_to_spira.json", "r")

            number_of_processed_issues += insert_capabilities_to_spira(spira, spira_metadata, spira_input, all_capabilites_in_spira_project)  # type: ignore
            print("Migration of type " + jira_type + " to program finished.")

        print("--------------------------------------")
        print("Migration of issues to program complete")
        print(
            "Migration processed "
            + str(number_of_processed_issues)
            + " issues of a total "
            + str(total_number_of_issues)
            + " found from supplied jql query."
        )
        print(
            "If the values are mismatched, either this script does not have support for some of the issue types found in jira or the mapping is incorrectly set."
        )
        print("--------------------------------------")

    elif args.command == "migrate_associations":
        # Set up some variables
        jira_connection_dict: Dict = get_jira_conn_dict()
        spira_connection_dict = get_spira_conn_dict()
        mapping_dict = get_mapping_dict(args.mapping)
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Initialize the instances
        jira = get_jira_instance(jira_connection_dict, skip_ssl)
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira product_id
        spira_product_id = get_spira_product_id_from_identifier(
            args.spira_product_identifier, spira
        )

        if spira_product_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        # Adding the spira_product_id to mapping dict
        mapping_dict["spira_product_id"] = spira_product_id

        # Extract the jira issues to a file
        print("Extracting the issues from jira...")
        jira_to_json(jira, args.jira_to_json_output, args.jql)

        args.jira_to_json_output.close()

        print("Getting all current artifacts from spira")
        all_requirements_in_spira_project = spira.get_all_requirements(
            mapping_dict["spira_product_id"]
        )
        all_tasks_in_spira_project = spira.get_all_tasks(
            mapping_dict["spira_product_id"]
        )
        all_incidents_in_spira_projects = spira.get_all_incidents(
            mapping_dict["spira_product_id"]
        )

        all_artifacts_in_spira = list(
            itertools.chain(
                all_requirements_in_spira_project,
                all_tasks_in_spira_project,
                all_incidents_in_spira_projects,
            )
        )

        with open(args.jira_to_json_output.name, "r") as file:
            json_output_dict = json.load(file)

        convert_jira_to_spira_issue_elements(
            jira_connection_dict,
            skip_ssl,
            json_output_dict,
            mapping_dict,
            all_artifacts_in_spira,
            "associations",
            spira,
        )

        spira_input = open("temp/to_spira.json", "r")

        update_artifacts(spira, mapping_dict["spira_product_id"], spira_input, jira)

        print("--------------------------------------")
        print("Migration of associations between artifacts complete")
        print("--------------------------------------")

    elif args.command == "migrate_documents":
        # Set up some variables
        jira_connection_dict: Dict = get_jira_conn_dict()
        spira_connection_dict = get_spira_conn_dict()
        mapping_dict = get_mapping_dict(args.mapping)
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Initialize the instances
        jira = get_jira_instance(jira_connection_dict, skip_ssl)
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira product_id
        spira_product_id = get_spira_product_id_from_identifier(
            args.spira_product_identifier, spira
        )

        if spira_product_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        # Adding the spira_product_id to mapping dict
        mapping_dict["spira_product_id"] = spira_product_id

        # Extract the jira issues to a file
        print("Extracting the issues from jira...")
        jira_to_json(jira, args.jira_to_json_output, args.jql)

        args.jira_to_json_output.close()

        # Get all the required data for migration
        print("Extracting metadata from spira...")
        spira_metadata = construct_spira_metadata(
            spira, mapping_dict["spira_product_id"]
        )
        print("Spira metadata extraction complete.")

        print("Getting all current artifacts from spira")
        all_requirements_in_spira_project = spira.get_all_requirements(
            mapping_dict["spira_product_id"]
        )
        all_tasks_in_spira_project = spira.get_all_tasks(
            mapping_dict["spira_product_id"]
        )
        all_incidents_in_spira_projects = spira.get_all_incidents(
            mapping_dict["spira_product_id"]
        )

        all_artifacts_in_spira = list(
            itertools.chain(
                all_requirements_in_spira_project,
                all_tasks_in_spira_project,
                all_incidents_in_spira_projects,
            )
        )

        with open(args.jira_to_json_output.name, "r") as file:
            json_output_dict = json.load(file)

        convert_jira_to_spira_issue_elements(
            jira_connection_dict,
            skip_ssl,
            json_output_dict,
            mapping_dict,
            all_artifacts_in_spira,
            "documents",
            spira,
            spira_metadata,
        )

        spira_input = open("temp/to_spira.json", "r")

        no_of_documents = update_artifacts(
            spira, mapping_dict["spira_product_id"], spira_input, jira
        )

        print("--------------------------------------")
        print("Migration of " + str(no_of_documents) + " documents complete")
        print("--------------------------------------")

    elif args.command == "add_document_associations":
        # Set up some variables
        spira_connection_dict = get_spira_conn_dict()
        mapping_dict = get_mapping_dict(args.mapping)
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Initialize the instances
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira product_id
        spira_product_id = get_spira_product_id_from_identifier(
            args.spira_product_identifier, spira
        )

        if spira_product_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        # Adding the spira_product_id to mapping dict
        mapping_dict["spira_product_id"] = spira_product_id

        # Get all the required data for migration
        print("Extracting metadata from spira...")
        spira_metadata = construct_spira_metadata(
            spira, mapping_dict["spira_product_id"]
        )
        print("Spira metadata extraction complete.")

        print("Getting all current artifacts from spira")
        all_requirements_in_spira_project = spira.get_all_requirements(
            mapping_dict["spira_product_id"]
        )
        all_tasks_in_spira_project = spira.get_all_tasks(
            mapping_dict["spira_product_id"]
        )
        all_incidents_in_spira_projects = spira.get_all_incidents(
            mapping_dict["spira_product_id"]
        )

        all_artifacts_in_spira = list(
            itertools.chain(
                all_requirements_in_spira_project,
                all_tasks_in_spira_project,
                all_incidents_in_spira_projects,
            )
        )

        all_documents_in_spira = spira.get_all_documents(
            mapping_dict["spira_product_id"]
        )

        convert_spira_data_for_spira_updates(
            all_documents_in_spira,
            all_artifacts_in_spira,
            "add_document_association",
            spira_metadata,
        )

        spira_input = open("temp/to_spira.json", "r")

        no_of_documents = update_artifacts(
            spira, mapping_dict["spira_product_id"], spira_input, jira
        )

        print("--------------------------------------")
        print("Updating of " + str(no_of_documents) + " documents complete")
        print("--------------------------------------")

    elif args.command == "migrate_comments":
        # Set up some variables
        jira_connection_dict: Dict = get_jira_conn_dict()
        spira_connection_dict = get_spira_conn_dict()
        mapping_dict = get_mapping_dict(args.mapping)
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Initialize the instances
        jira = get_jira_instance(jira_connection_dict, skip_ssl)
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira product_id
        spira_product_id = get_spira_product_id_from_identifier(
            args.spira_product_identifier, spira
        )

        if spira_product_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        # Adding the spira_product_id to mapping dict
        mapping_dict["spira_product_id"] = spira_product_id

        # Extract the jira issues to a file
        print("Extracting the issues from jira...")
        jira_to_json(jira, args.jira_to_json_output, args.jql)

        args.jira_to_json_output.close()

        print("Extracting metadata from spira...")
        spira_metadata = construct_spira_metadata(
            spira, mapping_dict["spira_product_id"]
        )
        print("Spira metadata extraction complete.")

        print("Getting all artifacts from spira")
        all_requirements_in_spira_project = spira.get_all_requirements(
            mapping_dict["spira_product_id"]
        )
        all_tasks_in_spira_project = spira.get_all_tasks(
            mapping_dict["spira_product_id"]
        )
        all_incidents_in_spira_projects = spira.get_all_incidents(
            mapping_dict["spira_product_id"]
        )

        all_artifacts_in_spira = list(
            itertools.chain(
                all_requirements_in_spira_project,
                all_tasks_in_spira_project,
                all_incidents_in_spira_projects,
            )
        )

        with open(args.jira_to_json_output.name, "r") as file:
            json_output_dict = json.load(file)

        convert_jira_to_spira_issue_elements(
            jira_connection_dict,
            skip_ssl,
            json_output_dict,
            mapping_dict,
            all_artifacts_in_spira,
            "comments",
            spira,
            spira_metadata,  # type: ignore
        )

        spira_input = open("temp/to_spira.json", "r")

        no_of_comments = update_artifacts(
            spira, mapping_dict["spira_product_id"], spira_input, jira
        )

        print("--------------------------------------")
        print("Migration of " + str(no_of_comments) + " comments to artifacts complete")
        print("--------------------------------------")

    elif args.command == "migrate_releases":
        # Set up some variables
        jira_connection_dict: Dict = get_jira_conn_dict()
        spira_connection_dict = get_spira_conn_dict()
        mapping_dict = get_mapping_dict(args.mapping)
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Adding jira projects to the mapping dict
        mapping_dict["jira_projects"] = args.jira_projects

        # Initialize the instances
        jira = get_jira_instance(jira_connection_dict, skip_ssl)
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira product_id
        spira_product_id = get_spira_product_id_from_identifier(
            args.spira_product_identifier, spira
        )

        if spira_product_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        # Adding the spira_product_id to mapping dict
        mapping_dict["spira_product_id"] = spira_product_id

        # Extract the jira issues to a file
        print("Extracting the versions from jira...")
        jira_versions_to_json(
            jira, args.jira_to_json_output, mapping_dict["jira_projects"]
        )

        args.jira_to_json_output.close()

        print("Extracting metadata from spira...")
        spira_metadata = construct_spira_metadata(
            spira, mapping_dict["spira_product_id"]
        )

        # Get all the current releases in spira
        all_releases_in_spira_project = spira.get_all_releases(
            mapping_dict["spira_product_id"]
        )

        print("Spira metadata extraction complete.")

        with open(args.jira_to_json_output.name, "r") as file:
            json_version_output_dict = json.load(file)

        # Counter for number of processed versions
        number_of_processed_releases = 0

        # Sort out name, versionnumber and releaseid
        spira_release_dict = {"releases": []}
        for release in all_releases_in_spira_project:
            project_release = {
                "Name": release["Name"],
                "VersionNumber": re.findall(r"\d+", release["Name"]),
                "ReleaseId": release["ReleaseId"],
            }

            spira_release_dict["releases"].append(project_release)

        convert_jira_to_spira_releases(json_version_output_dict, mapping_dict)

        spira_input = open("temp/releases_to_spira.json", "r")

        number_of_processed_releases += insert_releases_to_spira(
            spira, spira_metadata, spira_input, spira_release_dict
        )

        print("--------------------------------------")
        print(
            "Migration of "
            + str(number_of_processed_releases)
            + " versions to release artifacts complete"
        )
        print("--------------------------------------")
    elif args.command == "migrate_milestones":
        # Set up some variables
        jira_connection_dict: Dict = get_jira_conn_dict()
        spira_connection_dict = get_spira_conn_dict()
        mapping_dict = get_mapping_dict(args.mapping)
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Adding jira projects to the mapping dict
        mapping_dict["jira_projects"] = args.jira_projects

        # Initialize the instances
        jira = get_jira_instance(jira_connection_dict, skip_ssl)
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira program_id
        spira_program_id = get_spira_program_id_from_identifier(
            args.spira_program_identifier, spira
        )

        if spira_program_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        # Adding the spira_program_id to mapping dict
        mapping_dict["spira_program_id"] = spira_program_id

        # Extract issues that is to become capabilites from jira to a file
        print("Extracting the issues from jira...")
        jira_to_json(jira, args.jira_to_json_output, args.jql)

        args.jira_to_json_output.close()

        # Extract the jira issues to a file
        print("Extracting the versions from jira...")
        jira_versions_to_json(
            jira, args.jira_to_json_version_output, mapping_dict["jira_projects"]
        )
        args.jira_to_json_version_output.close()

        print("Extracting metadata from spira...")
        spira_metadata = construct_program_spira_metadata(
            spira, mapping_dict["spira_program_id"]
        )
        print("Spira metadata extraction complete.")

        with open(args.jira_to_json_output.name, "r") as file:
            json_output_dict = json.load(file)

        with open(args.jira_to_json_version_output.name, "r") as file:
            json_output_version_dict = json.load(file)

        # Counter for number of processed milestones
        number_of_processed_milestones = 0
        convert_jira_versions_to_spira_program_milestones(
            json_output_dict["issues"],
            json_output_version_dict,
            mapping_dict,
            spira_metadata,
        )

        spira_input = open("temp/milestones_to_spira.json", "r")

        number_of_processed_milestones += insert_milestones_to_spira(
            spira, spira_metadata, spira_input
        )

        print("--------------------------------------")
        print(
            "Migration of "
            + str(number_of_processed_milestones)
            + " versions to program milestones complete"
        )
        print("--------------------------------------")

    elif args.command == "migrate_components":
        # Set up some variables
        jira_connection_dict: Dict = get_jira_conn_dict()
        spira_connection_dict = get_spira_conn_dict()
        mapping_dict = get_mapping_dict(args.mapping)
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Adding jira projects to the mapping dict
        mapping_dict["jira_projects"] = args.jira_projects

        # Initialize the instances
        jira = get_jira_instance(jira_connection_dict, skip_ssl)
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira product_id
        spira_product_id = get_spira_product_id_from_identifier(
            args.spira_product_identifier, spira
        )

        if spira_product_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        # Adding the spira_product_id to mapping dict
        mapping_dict["spira_product_id"] = spira_product_id

        # Extract the jira components to a file
        print("Extracting the components from jira...")
        jira_components_to_json(
            jira, args.jira_to_json_output, mapping_dict["jira_projects"]
        )

        args.jira_to_json_output.close()

        print("Extracting metadata from spira...")
        spira_metadata = construct_spira_metadata(
            spira, mapping_dict["spira_product_id"]
        )
        print("Spira metadata extraction complete.")

        with open(args.jira_to_json_output.name, "r") as file:
            json_component_output_dict = json.load(file)

        # Counter for number of processed versions
        number_of_processed_components = 0

        convert_jira_to_spira_components(json_component_output_dict)

        spira_input = open("temp/components_to_spira.json", "r")

        number_of_processed_components += insert_components_to_spira(
            spira, spira_metadata, spira_input
        )

        print("--------------------------------------")
        print(
            "Migration of "
            + str(number_of_processed_components)
            + " components to component artifacts complete"
        )
        print("--------------------------------------")

    elif args.command == "migrate_customlists":
        # Set up some variables
        jira_connection_dict: Dict = get_jira_conn_dict()
        spira_connection_dict = get_spira_conn_dict()
        template_list = args.spira_templates
        system_level = args.system_level
        skip_ssl = args.skip_ssl_check

        if skip_ssl:
            print("HTTPS/SSL certificate verification is turned off, beware!")

        # Adding jira projects to dict
        mapping_dict = {}
        mapping_dict["jira_projects"] = args.jira_projects

        # Initialize the instances
        jira = get_jira_instance(jira_connection_dict, skip_ssl)
        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        mapping_dict["spira_template_ids"] = []

        # Check if lists should be migrated globally or at template level
        if system_level:
            print("Customlists will be migrated globally at system level")
        else:
            if not template_list:
                print(
                    "Could not parse template list and system flag not set to true, exiting."
                )
                sys.exit(EXIT_FAILURE)

            # Identify and extract correct spira template ids
            template_id_list = []
            for item in template_list:
                spira_template_id = get_spira_template_ids_from_identifier(item, spira)
                template_id_list.append(spira_template_id)

            # Adding the spira_product_id to mapping dict
            mapping_dict["spira_template_ids"] = template_id_list

        # Extract all projects to a file
        print("Extracting the customlists from jira...")
        jira_customlists_to_json(
            jira, args.jira_to_json_output, mapping_dict["jira_projects"]
        )

        args.jira_to_json_output.close()

        with open(args.jira_to_json_output.name, "r") as file:
            json_component_output_dict = json.load(file)

        # Counter for number of processed versions
        number_of_processed_lists = 0

        convert_jira_to_spira_customlists(json_component_output_dict)

        spira_input = open("temp/customlists_to_spira.json", "r")

        number_of_processed_lists += insert_lists_to_spira(
            spira, spira_input, system_level, mapping_dict["spira_template_ids"]
        )

        print("--------------------------------------")
        print(
            "Migration of " + str(number_of_processed_lists) + " customlists processed"
        )
        print("--------------------------------------")

    elif args.command == "clean_product":
        spira_connection_dict = get_spira_conn_dict()
        skip_ssl = args.skip_ssl_check

        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira product_id
        spira_product_id = get_spira_product_id_from_identifier(
            args.spira_product_identifier, spira
        )

        if spira_product_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        clean_spira_product(spira, spira_product_id)

        print("Clean complete")

    elif args.command == "clean_program":
        spira_connection_dict = get_spira_conn_dict()

        skip_ssl = args.skip_ssl_check

        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira program_id
        spira_program_id = get_spira_program_id_from_identifier(
            args.spira_program_identifier, spira
        )

        if spira_program_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        clean_spira_program(spira, spira_program_id)

        print("Clean complete")

    elif args.command == "clean_product_documents":
        spira_connection_dict = get_spira_conn_dict()
        skip_ssl = args.skip_ssl_check

        spira = get_spira_instance(spira_connection_dict, skip_ssl)

        # Identify and extract correct spira product_id
        spira_product_id = get_spira_product_id_from_identifier(
            args.spira_product_identifier, spira
        )

        if spira_product_id == 0:
            print("Could not parse spira product identifier, exiting.")
            sys.exit(EXIT_FAILURE)

        clean_spira_product_documents(spira, spira_product_id)

        print("Cleaning of documents complete")

    else:
        print(
            "Command not recognized, please try again with a registered command, see -h for more info"
        )


def get_jira_conn_dict() -> Dict:
    if (
        os.getenv("JIRA_BASE_URL") is None
        or os.getenv("JIRA_USERNAME") is None
        or os.getenv("JIRA_API_KEY") is None
    ):
        print("No values supplied for jira connection in the .env file, exiting...")
        sys.exit(EXIT_FAILURE)
    else:
        return {
            "jira_base_url": os.getenv("JIRA_BASE_URL"),
            "jira_username": os.getenv("JIRA_USERNAME"),
            "jira_api_key": os.getenv("JIRA_API_KEY"),
        }


def get_spira_conn_dict() -> Dict:
    if (
        os.getenv("SPIRA_BASE_URL") is None
        or os.getenv("SPIRA_USERNAME") is None
        or os.getenv("SPIRA_API_KEY") is None
    ):
        print("No values supplied for spira connection in the .env file, exiting...")
        sys.exit(EXIT_FAILURE)
    else:
        return {
            "spira_base_url": os.getenv("SPIRA_BASE_URL"),
            "spira_username": os.getenv("SPIRA_USERNAME"),
            "spira_api_key": os.getenv("SPIRA_API_KEY"),
        }


def get_mapping_dict(mapping_file) -> Dict:
    if mapping_file:
        try:
            return yaml.safe_load(mapping_file)
        except Exception as e:
            print(e)
            print("An error occured when trying to read the mapping file")
            sys.exit(EXIT_FAILURE)
    else:
        print("No mapping file supplied or found")
        return {}


def get_jira_instance(jira_conn_dict, skip_ssl) -> JIRA:
    try:
        return JIRA(
            jira_conn_dict["jira_base_url"],
            basic_auth=(
                jira_conn_dict["jira_username"],
                jira_conn_dict["jira_api_key"],
            ),
            options={"verify": (not skip_ssl)},
        )
    except Exception as e:
        print(e)
        print(
            "An error occured when trying to connect to the jira instance, please check that you have the correct variables set."
        )
        sys.exit(EXIT_FAILURE)


def get_spira_instance(spira_conn_dict, skip_ssl) -> Spira:
    try:
        return Spira(
            spira_conn_dict["spira_base_url"],
            basic_auth=(
                spira_conn_dict["spira_username"],
                spira_conn_dict["spira_api_key"],
            ),
            verify=(not skip_ssl),
        )
    except Exception as e:
        print(e)
        print(
            "An error occured when trying to connect to the spira instance, please check that you have the correct variables set."
        )
        sys.exit(EXIT_FAILURE)


def construct_jira_metadata(jira) -> Dict:
    jira_metadata = {"customfields": []}

    fields = jira.fields()

    # Get the customfields
    customfields = list(filter((lambda x: x["custom"] is True), fields))  # type: ignore

    for customfield in customfields:
        jira_metadata["customfields"].append(customfield)

    return jira_metadata


def construct_spira_metadata(spira: Spira, project_id: int) -> Dict:
    spira_metadata = {}

    # Get all projects
    projects = spira.get_projects()

    if not project_id:
        print("Missing project id to target, can't proceed")
        sys.exit(EXIT_FAILURE)

    # Get the project the script is working on
    project = next(
        filter((lambda x: x["ProjectId"] == int(project_id)), projects), None
    )

    if not project:
        print("No valid project found for supplied id: " + str(project_id))
        sys.exit(0)

    spira_metadata["project"] = project

    # Get the project the script is working on's template.
    project_template = spira.get_project_template(
        spira_metadata["project"]["ProjectTemplateId"]
    )

    if not project_template:
        print(
            "No valid project template found for supplied id: "
            + str(spira_metadata["project"]["ProjectTemplateId"])
        )
        sys.exit(0)

    project_template_id = project["ProjectTemplateId"]

    spira_metadata["project_template"] = project_template

    # Get the users on the instance

    spira_metadata["users"] = spira.get_all_users()

    # Get all types

    spira_metadata["types"] = {}

    # Requirement types

    spira_metadata["types"]["requirement"] = spira.get_requirement_types(
        project_template_id
    )
    spira_metadata["types"]["incident"] = spira.get_incident_types(project_template_id)
    spira_metadata["types"]["task"] = spira.get_task_types(project_template_id)

    # Get all custom properties

    spira_metadata["custom_properties"] = {}

    spira_metadata["custom_properties"][
        "capability"
    ] = spira.get_project_template_custom_properties(project_template_id, "capability")
    spira_metadata["custom_properties"][
        "requirement"
    ] = spira.get_project_template_custom_properties(project_template_id, "requirement")
    spira_metadata["custom_properties"][
        "incident"
    ] = spira.get_project_template_custom_properties(project_template_id, "incident")
    spira_metadata["custom_properties"][
        "task"
    ] = spira.get_project_template_custom_properties(project_template_id, "task")
    spira_metadata["custom_properties"][
        "document"
    ] = spira.get_project_template_custom_properties(project_template_id, "document")

    # Get all statuses

    spira_metadata["statuses"] = {}

    spira_metadata["statuses"]["requirement"] = spira.get_requirement_statuses(
        project_template_id
    )
    spira_metadata["statuses"]["incident"] = spira.get_incident_statuses(
        project_template_id
    )
    spira_metadata["statuses"]["task"] = spira.get_task_statuses(project_template_id)

    # Get all project custom lists with values

    all_project_lists = spira.get_project_template_custom_lists(project_template_id)

    all_lists_w_values = []

    for customlist in all_project_lists:
        customlist["CustomPropertyListId"]
        item = spira.get_project_template_custom_list_values(
            project_template_id, customlist["CustomPropertyListId"]
        )
        all_lists_w_values.append(item)

    spira_metadata["custom_lists"] = all_lists_w_values

    # Get all releases

    spira_metadata["releases"] = spira.get_all_releases(project_id)

    # Get all components

    spira_metadata["components"] = spira.get_all_components(project_id)

    # Get all capabilites in program that project belongs to
    spira_metadata["capabilites"] = spira.get_all_program_capabilities(
        spira_metadata["project"]["ProjectGroupId"]
    )

    # Get requirement importances
    spira_metadata["importances"] = spira.get_requirement_importances(
        project_template_id
    )

    # Get incident priorities
    spira_metadata["incident_priorities"] = spira.get_incident_priorities(
        project_template_id
    )

    # Get task priorities
    spira_metadata["task_priorities"] = spira.get_task_priorities(project_template_id)

    # Get document folders
    spira_metadata["document_folders"] = spira.get_all_document_folders(project_id)

    return spira_metadata


def construct_program_spira_metadata(spira: Spira, program_id: int) -> Dict:
    spira_metadata = {}

    if not program_id:
        print("Missing program id to target, can't proceed")
        sys.exit(EXIT_FAILURE)

    program = {
        "program_id": program_id,
    }

    spira_metadata["program"] = program

    # Get custom properties for capabilies
    capability_custom_properties = spira.get_system_custom_properties("capability")

    spira_metadata["custom_properties"] = {"capability": capability_custom_properties}

    # Get the users on the instance
    spira_metadata["users"] = spira.get_all_users()

    # Get all program types
    spira_metadata["types"] = {}
    spira_metadata["types"]["capability"] = spira.get_program_capability_types()
    spira_metadata["types"]["milestone"] = spira.get_program_milestone_types()

    # Get all program statuses
    spira_metadata["statuses"] = {}
    spira_metadata["statuses"]["capability"] = spira.get_program_capability_statuses()
    spira_metadata["statuses"]["milestone"] = spira.get_program_milestone_statuses()

    # Get all program priorities
    spira_metadata["priorities"] = {}
    spira_metadata["priorities"][
        "capability"
    ] = spira.get_program_capability_priorities()

    # Get all program custom lists
    all_program_lists = spira.get_system_level_custom_lists()

    all_lists_w_values = []

    for customlist in all_program_lists:
        customlist["CustomPropertyListId"]
        item = spira.get_system_level_custom_list_values(
            customlist["CustomPropertyListId"]
        )
        all_lists_w_values.append(item)

    spira_metadata["custom_lists"] = all_lists_w_values

    # Get all program milestones
    spira_metadata["milestones"] = spira.get_all_program_milestones(program_id)

    return spira_metadata


def get_spira_product_id_from_identifier(spira_product_identifier: str, spira) -> int:
    # If string is actually an int and therefore the spira product_id
    try:
        product_id = int(spira_product_identifier)
        return product_id
    except Exception as e:
        pass

    # String is not an int, so script have to fetch the possible products and infer a product id from spira.
    products = spira.get_projects()

    found_product = next(
        filter(lambda x: x["Name"] == spira_product_identifier, products)
    )

    if found_product is not None and found_product["ProjectId"] is not None:
        return found_product["ProjectId"]
    else:
        return 0


def get_spira_template_ids_from_identifier(
    spira_template_identifier: str, spira
) -> int:
    try:
        template_id = int(spira_template_identifier)
        return template_id
    except Exception as e:
        pass

    # String is not an int, so script have to fetch the possible templates and infer a template id from spira.
    templates_in_spira = spira.get_all_project_templates()

    found_template = next(
        filter(lambda x: x["Name"] == spira_template_identifier, templates_in_spira)
    )

    if found_template is not None and found_template["ProjectTemplateId"] is not None:
        return found_template["ProjectTemplateId"]
    else:
        return 0


def get_spira_program_id_from_identifier(spira_program_identifier: str, spira) -> int:
    # If string is actually an int and therefore the spira program_id
    try:
        program_id = int(spira_program_identifier)
        return program_id
    except Exception as e:
        pass

    # String is not an int, so script have to fetch the possible programs and infer a program id from spira
    programs = spira.get_all_programs()

    found_program = next(
        filter(lambda x: x["Name"] == spira_program_identifier, programs)
    )

    if found_program is not None and found_program["ProgramId"] is not None:
        return found_program["ProgramId"]
    else:
        return 0


if __name__ == "__main__":
    main()
