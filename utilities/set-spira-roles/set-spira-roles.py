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

    parser.add_argument("project_id", type=int)

    parser.add_argument("role_id", type=int)

    parser.add_argument("ldap_filter", type=str)

    parser.add_argument(
        "-csv",
        "--csv-files",
        help="CSV files to set roles from",
        nargs="+",
        type=argparse.FileType("r", encoding="UTF-8"),
    )

    args = parser.parse_args()

    # Start spira connection
    spira_connection_dict = get_spira_conn_dict()
    spira = get_spira_instance(spira_connection_dict, True)

    # Start LDAP connection
    # See if required env variables are present
    if args.csv_files is None and (
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
    project_users = spira.get_all_project_users(args.project_id)
    project_roles = spira.get_all_project_roles()

    users = set()

    users_does_not_exist = []
    users_created = []
    users_already_member = []
    users_role_set = []
    users_role_removed = []  # TODO

    # LDAP case
    if args.csv_files is None:
        mapping_file = open("mapping.yaml", "r")
        mapping = yaml.safe_load(mapping_file)

        role = get_project_role(args.role_id, project_roles)

        user_result = ldap_conn.search_s(
            os.getenv("LDAP_BASE_DN"), ldap.SCOPE_SUBTREE, args.ldap_filter
        )
        for user in track(user_result, "Processing LDAP users...", transient=True):
            # The only required ldap field in Spiraplan is the "Login", or the userid/username.
            if mapping["Login"] not in user[1]:
                print(
                    "ERROR User:"
                    + str(user)
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
                    response = spira.create_user(
                        user_payload, args.project_id, args.role_id
                    )
                    if response.status_code > 399:
                        raise Exception
                    users_created.append(
                        "[*] User: "
                        + str(username)
                        + ", was added to this Spiraplan instance and project with role: "
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
                "ProjectId": args.project_id,
                "ProjectRoleId": args.role_id,
                "UserId": user_id,
                "UserName": username,
            }

            result = spira.add_user_with_role_to_project(args.project_id, payload)
            found_project_user = get_project_user(user_id, project_users)

            if result.status_code > 399:
                if (
                    result.text
                    == '<string xmlns="http://schemas.microsoft.com/2003/10/Serialization/">The user is already a member of the product</string>'
                    or result.text
                    == '<string xmlns="http://schemas.microsoft.com/2003/10/Serialization/">ProjectDuplicateMembershipRecordException: That project membership row already exists!</string>'
                ):
                    users_already_member.append(
                        "[0] User: "
                        + str(username)
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
                    print(
                        "[ERR] Error when setting role for user with username: "
                        + str(user)
                    )
                    print("Error ------------------------------------")
                    print(result.text)
                    print("----------------------------------------")
            else:
                role = get_project_role(args.role_id, project_roles)
                users_role_set.append(
                    "[+] User: " + user + ", has been set to role: " + role["Name"]
                    if role is not None
                    else "RoleNameNotFound" + ", with role id: " + str(args.role_id)
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

        print("---** Users created from LDAP **---")
        print("---------------------------------------------------")
        for user in track(users_created, "Printing...", transient=True):
            print(user)
        print("---------------------------------------------------")

        print("Finished role setting using LDAP connection, see above for details")

    # CSV case
    else:
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
                "ProjectId": args.project_id,
                "ProjectRoleId": args.role_id,
                "UserId": user_id,
                "UserName": user,
            }

            result = spira.add_user_with_role_to_project(args.project_id, payload)
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
                role = get_project_role(args.role_id, project_roles)
                users_role_set.append(
                    "[+] User: " + user + ", has been set to role: " + role["Name"]
                    if role is not None
                    else "RoleNameNotFound" + ", with role id: " + str(args.role_id)
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


if __name__ == "__main__":
    main()
