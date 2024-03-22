import csv, argparse, os, sys
from spira import Spira
import ldap
import yaml
from rich.progress import track

# Load env variables from .env file
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Set spira roles from groups from an LDAP connection or from CSV files"
    )

    subparsers = parser.add_subparsers(dest="command")

    # LDAP ADD command
    parser_ldap_add_roles = subparsers.add_parser(
        "add",
        help="Adds the users and roles to the product, creates users if not exists, does not remove any rights or users.",
    )

    parser_ldap_add_roles.add_argument("project_id", type=str)

    parser_ldap_add_roles.add_argument("role_id", type=str)

    parser_ldap_add_roles.add_argument("ldap_filter", type=str)

    parser_ldap_add_roles.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on the spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # LDAP SET command

    parser_ldap_set_roles = subparsers.add_parser(
        "set",
        help="Sets the users and roles to the product, creates users if not exists, removes user roles and rights if not in ldap.",
    )

    parser_ldap_set_roles.add_argument("project_id", type=str)

    parser_ldap_set_roles.add_argument("role_id", type=str)

    parser_ldap_set_roles.add_argument("ldap_filter", type=str)

    parser_ldap_set_roles.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on the spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    # CSV command

    parser_csv_set_roles = subparsers.add_parser(
        "csv",
        help="Sets the users roles on the product from a csv file, see example.csv for how to format it. Does not create users or remove roles.",
    )

    parser_csv_set_roles.add_argument("project_id", type=str)

    parser_csv_set_roles.add_argument("role_id", type=str)

    parser_csv_set_roles.add_argument(
        "csv_files",
        help="CSV files to set roles from, see example.csv for example csv file structure.",
        nargs="+",
        type=argparse.FileType("r", encoding="UTF-8"),
    )

    parser_csv_set_roles.add_argument(
        "-nossl",
        "--skip-ssl-check",
        help="Skip the ssl check on the spira instance",
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=False,
    )

    args = parser.parse_args()

    # Start spira connection
    spira_connection_dict = get_spira_conn_dict()
    spira: Spira = get_spira_instance(spira_connection_dict, args.skip_ssl_check)

    project_id = get_spira_product_id_from_identifier(args.project_id, spira)
    role_id = get_spira_role_id_from_identifier(args.role_id, spira)

    # Start LDAP connection
    # See if required env variables are present
    if (args.command == "add" or args.command == "set") and (
        os.getenv("LDAP_ADDRESS") is None or os.getenv("LDAP_BASE_DN") is None
    ):
        print("No values supplied for ldap connection in the .env file, exiting...")
        sys.exit(1)

    ldap_conn = ldap.initialize(os.getenv("LDAP_ADDRESS"))
    ldap_conn.protocol_version = 3
    ldap_conn.set_option(ldap.OPT_REFERRALS, 0)

    try:
        ldap_conn.simple_bind_s(os.getenv("LDAP_USERNAME"), os.getenv("LDAP_PASSWORD"))
    except ldap.INVALID_CREDENTIALS:
        print("Invalid Credentials")
        sys.exit(1)
    except ldap.SERVER_DOWN:
        print("Server down")
        sys.exit(1)
    except ldap.LDAPError as e:
        print("Other ldap error: " + str(e))
        sys.exit(1)

    # Fetch spira users, needed for both LDAP and CSV usage.
    fetched_users = spira.get_all_users()
    project_users = spira.get_all_project_users(project_id)
    project_roles = spira.get_all_project_roles()

    users = set()

    users_does_not_exist = []
    users_created = []
    users_already_member = []
    users_role_changed = []
    users_role_set = []
    users_role_removed = []

    # LDAP add case
    if args.command == "add":
        mapping_file = open("mapping.yaml", "r")
        mapping = yaml.safe_load(mapping_file)

        role = get_project_role(role_id, project_roles)

        user_result = ldap_conn.search_s(
            os.getenv("LDAP_BASE_DN"), ldap.SCOPE_SUBTREE, args.ldap_filter
        )
        for user in track(user_result, "Processing LDAP users...", transient=True):
            # The only required ldap field in Spiraplan is the "Login", or the userid/username.
            if mapping["Login"] not in user[1]:
                print(
                    "ERROR User:"
                    + str(user)
                    + ", "
                    + user[1][mapping]["Email_Address"][0].decode("utf-8")
                    if mapping["Email_Address"] in user[1]
                    else "NoEmailAddress"
                    + "\n, could not be added as the required login id is missing"
                )
                continue
            username = user[1][mapping["Login"]][0].decode("utf-8")
            found_user = get_user_id_from_username(username, fetched_users)
            user_id = found_user["UserId"]

            # Check if user exist in SpiraPlan, else we add it.
            if not found_user["UserId"]:
                user_payload = {
                    "UserName": user[1][mapping["Login"]][0].decode("utf-8"),
                    "FirstName": (
                        user[1][mapping["First_Name"]][0].decode("utf-8")
                        if mapping["First_Name"] in user[1]
                        else None
                    ),
                    "MiddleInitial": (
                        user[1][mapping["Middle_Initial"]][0].decode("utf-8")
                        if mapping["Middle_Initial"] in user[1]
                        else None
                    ),
                    "LastName": (
                        user[1][mapping["Last_Name"]][0].decode("utf-8")
                        if mapping["Last_Name"] in user[1]
                        else None
                    ),
                    "EmailAddress": (
                        user[1][mapping["Email_Address"]][0].decode("utf-8")
                        if mapping["Email_Address"] in user[1]
                        else ""
                    ),
                    "LdapDn": user[0],
                    "Approved": True,  # This pre-approves the users
                }
                try:
                    response = spira.create_user(user_payload, project_id, role_id)
                    if response.status_code > 399:
                        raise Exception
                    users_created.append(
                        "[*] User: "
                        + str(username)
                        + ", "
                        + user_payload["EmailAddress"]
                        if user_payload["EmailAddress"] is not None
                        else "NoEmailAddress"
                        + ", "
                        + "was added to this Spiraplan instance and project with role: "
                        + (role["Name"] if role is not None else "RoleNotFound")
                    )
                except Exception as e:
                    print(
                        "ERROR User with payload: "
                        + str(user_payload)
                        + "\n, could not be created"
                    )
                finally:
                    continue

            payload = {
                "ProjectId": project_id,
                "ProjectRoleId": role_id,
                "UserId": user_id,
                "UserName": username,
            }

            result = spira.add_user_with_role_to_project(project_id, payload)
            found_project_user = get_project_user(user_id, project_users)

            if result.status_code > 399:
                if (
                    result.text
                    == '<string xmlns="http://schemas.microsoft.com/2003/10/Serialization/">The user is already a member of the product</string>'
                    or result.text
                    == '<string xmlns="http://schemas.microsoft.com/2003/10/Serialization/">ProjectDuplicateMembershipRecordException: That project membership row already exists!</string>'
                ):
                    if (
                        found_project_user is not None
                        and "ProjectRoleId" in found_project_user
                    ):
                        found_project_user_role_id = found_project_user["ProjectRoleId"]
                    else:
                        found_project_user_role_id = 0

                    # Check if the user already has the role so we can skip removing and readding it.
                    if (
                        found_project_user_role_id != 0
                        and role_id == found_project_user_role_id
                    ):
                        users_already_member.append(
                            "[0] User: "
                            + str(username)
                            + ", "
                            + user[1][mapping["Email_Address"]][0].decode("utf-8")
                            if mapping["Email_Address"] in user[1]
                            else "NoEmailAddress"
                            + ", with role: "
                            + str(
                                found_project_user["ProjectRoleName"]
                                if found_project_user is not None
                                else "ProjectRoleNameNotFound"
                            )
                            + ", and role id: "
                            + str(
                                found_project_user["ProjectRoleId"]
                                if found_project_user is not None
                                else "ProjectRoleIdNotFound"
                            )
                            + " already exists in product."
                        )
                    else:
                        update_result = spira.update_user_with_role_to_project(
                            project_id, payload
                        )
                        if update_result.status_code > 399:
                            print(
                                "[ERR] Unknown error when trying to update user with role_id:"
                                + str(user)
                            )
                            print("Error ------------------------------------")
                            print(update_result.text)
                            print("----------------------------------------")
                        else:
                            users_role_changed.append(
                                "[o] User: "
                                + str(username)
                                + ", "
                                + user[1][mapping["Email_Address"]][0].decode("utf-8")
                                if mapping["Email_Address"] in user[1]
                                else "NoEmailAddress"
                                + ", with role: "
                                + str(
                                    found_project_user["ProjectRoleName"]
                                    if found_project_user is not None
                                    else "ProjectRoleNameNotFound"
                                )
                                + ", and role id: "
                                + str(
                                    found_project_user["ProjectRoleId"]
                                    if found_project_user is not None
                                    else "ProjectRoleIdNotFound"
                                )
                                + "was changed on this Spiraplan instance and project and updated to role: "
                                + (role["Name"] if role is not None else "RoleNotFound")
                            )

                else:
                    print(
                        "[ERR] Error when setting role for user with username: "
                        + str(user)
                    )
                    print("Error ------------------------------------")
                    print(result.text)
                    print("----------------------------------------")
            else:
                role = get_project_role(role_id, project_roles)

                role_set_log_string = "[+] User: " + user + ", "

                if mapping["Email_Address"] in user[1]:
                    role_set_log_string + user[1][mapping]["Email_Address"][0].decode(
                        "utf-8"
                    )
                else:
                    role_set_log_string + "NoEmailAddress"

                role_set_log_string + ", has been set to role: "

                if role is not None:
                    role_set_log_string + role["Name"]
                else:
                    role_set_log_string + "RoleNameNotFound"

                role_set_log_string + ", with role id: " + str(role_id)

                users_role_set.append(role_set_log_string)

        print("---** Users with roles set **---")
        print("---------------------------------------------------")
        for user in track(users_role_set, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("---** Users with roles changed **---")
        print("---------------------------------------------------")
        for user in track(users_role_changed, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("---** Users already members with role set. **---")
        print("---------------------------------------------------")
        for user in track(users_already_member, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("---** Users created from LDAP **---")
        print("---------------------------------------------------")
        for user in track(users_created, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("Finished role setting using LDAP connection, see above for details")

    # LDAP set case
    elif args.command == "set":
        mapping_file = open("mapping.yaml", "r")
        mapping = yaml.safe_load(mapping_file)

        role = get_project_role(role_id, project_roles)

        users_to_remove = project_users.copy()

        user_result = ldap_conn.search_s(
            os.getenv("LDAP_BASE_DN"), ldap.SCOPE_SUBTREE, args.ldap_filter
        )
        for user in track(user_result, "Processing LDAP users...", transient=True):
            # The only required ldap field in Spiraplan is the "Login", or the userid/username.
            if mapping["Login"] not in user[1]:
                print(
                    "ERROR User:"
                    + str(user)
                    + ", "
                    + user[1][mapping]["Email_Address"][0].decode("utf-8")
                    if mapping["Email_Address"] in user[1]
                    else "NoEmailAddress"
                    + "\n, could not be added as the required login id is missing"
                )
                continue
            username = user[1][mapping["Login"]][0].decode("utf-8")
            found_user = get_user_id_from_username(username, fetched_users)
            user_id = found_user["UserId"]

            # Check if user exist in SpiraPlan, else we add it.
            if not found_user["UserId"]:
                user_payload = {
                    "UserName": user[1][mapping["Login"]][0].decode("utf-8"),
                    "FirstName": (
                        user[1][mapping["First_Name"]][0].decode("utf-8")
                        if mapping["First_Name"] in user[1]
                        else None
                    ),
                    "MiddleInitial": (
                        user[1][mapping["Middle_Initial"]][0].decode("utf-8")
                        if mapping["Middle_Initial"] in user[1]
                        else None
                    ),
                    "LastName": (
                        user[1][mapping["Last_Name"]][0].decode("utf-8")
                        if mapping["Last_Name"] in user[1]
                        else None
                    ),
                    "EmailAddress": (
                        user[1][mapping["Email_Address"]][0].decode("utf-8")
                        if mapping["Email_Address"] in user[1]
                        else ""
                    ),
                    "LdapDn": user[0],
                    "Approved": True,  # This pre-approves the users
                }
                try:
                    response = spira.create_user(user_payload, project_id, role_id)
                    if response.status_code > 399:
                        raise Exception
                    users_created.append(
                        "[*] User: "
                        + str(username)
                        + ", "
                        + user_payload["EmailAddress"]
                        if user_payload["EmailAddress"] is not None
                        else "NoEmailAddress"
                        + ", "
                        + "was added to this Spiraplan instance and project with role: "
                        + (role["Name"] if role is not None else "RoleNotFound")
                    )
                except Exception as e:
                    print(
                        "ERROR User with payload: "
                        + str(user_payload)
                        + "\n, could not be created"
                    )
                finally:
                    continue

            # TODO Check if user already exists before in user_result, if with other role, remove it and add new role.

            payload = {
                "ProjectId": int(project_id),
                "ProjectRoleId": int(role_id),
                "UserId": int(user_id),
                "UserName": username,
            }

            print(payload)

            result = spira.add_user_with_role_to_project(project_id, payload)
            found_project_user = get_project_user(user_id, project_users)

            if result.status_code > 399:
                if (
                    result.text
                    == '<string xmlns="http://schemas.microsoft.com/2003/10/Serialization/">The user is already a member of the product</string>'
                    or result.text
                    == '<string xmlns="http://schemas.microsoft.com/2003/10/Serialization/">ProjectDuplicateMembershipRecordException: That project membership row already exists!</string>'
                ):
                    if (
                        found_project_user is not None
                        and "ProjectRoleId" in found_project_user
                    ):
                        found_project_user_role_id = found_project_user["ProjectRoleId"]
                    else:
                        found_project_user_role_id = 0

                    # Check if the user already has the role so we can skip removing and readding it.
                    if (
                        found_project_user_role_id != 0
                        and role_id == found_project_user_role_id
                    ):
                        users_already_member.append(
                            "[0] User: "
                            + str(username)
                            + ", "
                            + user[1][mapping["Email_Address"]][0].decode("utf-8")
                            if mapping["Email_Address"] in user[1]
                            else "NoEmailAddress"
                            + ", with role: "
                            + str(
                                found_project_user["ProjectRoleName"]
                                if found_project_user is not None
                                else "ProjectRoleNameNotFound"
                            )
                            + ", and role id: "
                            + str(
                                found_project_user["ProjectRoleId"]
                                if found_project_user is not None
                                else "ProjectRoleIdNotFound"
                            )
                            + " already exists in product."
                        )

                    else:
                        update_result = spira.update_user_with_role_to_project(
                            project_id, payload
                        )
                        if update_result.status_code > 399:
                            print(
                                "[ERR] Unknown error when trying to update user with role_id:"
                                + str(user)
                            )
                            print("Error ------------------------------------")
                            print(update_result.text)
                            print("----------------------------------------")
                        else:
                            users_role_changed.append(
                                "[o] User: "
                                + str(username)
                                + ", "
                                + user[1][mapping["Email_Address"]][0].decode("utf-8")
                                if mapping["Email_Address"] in user[1]
                                else "NoEmailAddress"
                                + ", with role: "
                                + str(
                                    found_project_user["ProjectRoleName"]
                                    if found_project_user is not None
                                    else "ProjectRoleNameNotFound"
                                )
                                + ", and role id: "
                                + str(
                                    found_project_user["ProjectRoleId"]
                                    if found_project_user is not None
                                    else "ProjectRoleIdNotFound"
                                )
                                + "was changed on this Spiraplan instance and project and updated to role: "
                                + (role["Name"] if role is not None else "RoleNotFound")
                            )

                else:
                    print(
                        "[ERR] Error when setting role for user with username: "
                        + str(username)
                    )
                    print("Error ------------------------------------")
                    print(result.text)
                    print("----------------------------------------")
            else:
                role = get_project_role(role_id, project_roles)

                role_set_log_string = "[+] User: " + user + ", "

                if mapping["Email_Address"] in user[1]:
                    role_set_log_string + user[1][mapping]["Email_Address"][0].decode(
                        "utf-8"
                    )
                else:
                    role_set_log_string + "NoEmailAddress"

                role_set_log_string + ", has been set to role: "

                if role is not None:
                    role_set_log_string + role["Name"]
                else:
                    role_set_log_string + "RoleNameNotFound"

                role_set_log_string + ", with role id: " + str(role_id)

                users_role_set.append(role_set_log_string)

            # Remove the user if we found it in the ldap search
            remove_user_from_list(users_to_remove, user_id)

        # Remove users roles from this project if they were not in the ldap group search.
        for user in track(
            users_to_remove, "Processing removing users from project...", transient=True
        ):
            # If the user exists and has a UserId and is not the system administrator account that is on every project
            if user and "UserName" in user and user["UserName"] == "administrator":
                print("Administrator username present, it is not removed from project")

            if user and "UserId" in user:
                result = spira.remove_user_with_role_from_project(
                    project_id, int(user["UserId"])
                )
                if result.status_code > 399:
                    print(
                        "[ERR] Error when removing role for this project for user with username: "
                        + str(user["UserName"])
                    )
                    print("Error ------------------------------------")
                    print(result.text)
                    print("----------------------------------------")
                else:
                    users_role_removed.append(
                        "[X] User: "
                        + str(user["UserName"])
                        + ", "
                        + str(user["EmailAddress"])
                        + ", with role: "
                        + str(user["ProjectRoleName"])
                        + ", and role id: "
                        + str(user["ProjectRoleId"])
                        + "was removed from this project on this Spiraplan instance and project."
                    )

        print("---** Users with roles set **---")
        print("---------------------------------------------------")
        for user in track(users_role_set, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("---** Users with roles changed **---")
        print("---------------------------------------------------")
        for user in track(users_role_changed, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("---** Users with roles removed from this project **---")
        print("---------------------------------------------------")
        for user in track(users_role_removed, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("---** Users already members with role set. **---")
        print("---------------------------------------------------")
        for user in track(users_already_member, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("---** Users created from LDAP **---")
        print("---------------------------------------------------")
        for user in track(users_created, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("Finished role setting using LDAP connection, see above for details")

    # CSV case
    elif args.command == "csv":
        for csv_file in vars(args)["csv_files"]:
            reader = csv.reader(csv_file, delimiter=",", quotechar='"')
            next(reader)
            for row in reader:
                user = row[0].strip()
                users.add(user)

        for user in track(users, "Processing users...", transient=True):
            found_user = get_user_id_from_username(user, fetched_users)
            user_id = found_user["UserId"]
            # Check if user exist in SpiraPlan, if not we skip
            if not user_id:
                users_does_not_exist.append(
                    "[-] User: "
                    + str(user)
                    + ", does not exist in this SpiraPlan instance"
                )
                continue

            payload = {
                "ProjectId": project_id,
                "ProjectRoleId": role_id,
                "UserId": user_id,
                "UserName": user,
            }

            result = spira.add_user_with_role_to_project(project_id, payload)
            found_project_user = get_project_user(user_id, project_users)
            if result.status_code > 399:
                if (
                    result.text
                    == '<string xmlns="http://schemas.microsoft.com/2003/10/Serialization/">The user is already a member of the product</string>'
                ):
                    users_already_member.append(
                        "[0] User: "
                        + user
                        + ", with role: "
                        + found_project_user["ProjectRoleName"]
                        + ", and role id: "
                        + str(found_project_user["ProjectRoleId"])
                        + " already exists in product."
                    )
                else:
                    print("[ERR] Error when inserting user with username: " + user)
                    print("Error ------------------------------------")
                    print(result.text)
                    print("----------------------------------------")
            else:
                role = get_project_role(role_id, project_roles)
                users_role_set.append(
                    "[+] User: " + user + ", has been set to role: " + role["Name"]
                    if role is not None
                    else "RoleNameNotFound" + ", with role id: " + str(role_id)
                )

        print("---** Users with roles set **---")
        print("---------------------------------------------------")
        for user in track(users_role_set, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("---** Users already members with role set. **---")
        print("---------------------------------------------------")
        for user in track(users_already_member, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("---** Users does not exist, skipped **---")
        print("---------------------------------------------------")
        for user in track(users_does_not_exist, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")
        print("Finished role setting using CSV files, see above for details")
    else:
        print("No command supplied, exiting.")


def get_user_id_from_username(username, fetched_users):
    for user in fetched_users:
        if username == user["UserName"]:
            return {
                "UserId": user["UserId"],
                "UserName": user["UserName"],
                "Name": user["FirstName"] + " " + user["LastName"],
            }

    return {"UserId": "", "UserName": "", "Name": ""}


def get_project_user(user_id, project_users):
    for user in project_users:
        if user["UserId"] == user_id:
            return user


def get_project_role(role_id, project_roles):
    for role in project_roles:
        if role["ProjectRoleId"] == role_id:
            return role


# Removes first occurence of a user from a supplied list of project users from spira if the user exists by their UserId.
def remove_user_from_list(project_users, user_id):
    for user in project_users:
        if user and "UserId" in user and user_id == user["UserId"]:
            project_users.remove(user)
            break


def get_spira_conn_dict():
    if (
        os.getenv("SPIRA_BASE_URL") is None
        or os.getenv("SPIRA_USERNAME") is None
        or os.getenv("SPIRA_API_KEY") is None
    ):
        print("No values supplied for spira connection in the .env file, exiting...")
        sys.exit(1)
    else:
        return {
            "spira_base_url": os.getenv("SPIRA_BASE_URL"),
            "spira_username": os.getenv("SPIRA_USERNAME"),
            "spira_api_key": os.getenv("SPIRA_API_KEY"),
        }


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
        sys.exit(1)


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


def get_spira_role_id_from_identifier(spira_role_identifier: str, spira) -> int:
    # If the string is actually an int and therefore the spira role_id
    try:
        role_id = int(spira_role_identifier)
        return role_id
    except Exception as e:
        pass

    # String is not an int, so script have to fetch the possible roles and infer a role id from spira
    project_roles = spira.get_all_project_roles()

    found_role = next(
        filter(lambda x: x["Name"] == spira_role_identifier, project_roles)
    )

    if found_role is not None and found_role["ProjectRoleId"] is not None:
        return found_role["ProjectRoleId"]
    else:
        return 0


if __name__ == "__main__":
    main()
