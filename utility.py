# Utility functions
# Some utility functions that might be needed in several places in the codebase.
import requests
from requests.auth import HTTPBasicAuth
import json
import re

# Pre-compiled regex for removing \xhh chars.
regex_x_invalid_escape_chars = re.compile(r"\\x([0-9a-fA-F]{2})")


# Functions for fixing the string and replacing the \xhh chars
def fix_xinvalid(m):
    return chr(int(m.group(1), 16))


def fix(s):
    return regex_x_invalid_escape_chars.sub(fix_xinvalid, s)


# Indent levels
# Functions for handling indent levels


# Add indent level to the current string.
def add_indent_level(indent_string: str) -> str:
    indent_string = indent_string + "AAA"
    return indent_string


# Remove indent level from current string, if minimal string, nothing will happen.
def remove_indent_level(indent_string: str) -> str:
    if len(indent_string) <= 3:
        return indent_string
    else:
        return indent_string[:-3]


# Increment current outermost indent level, if max string ("ZZZ"), will return input.
def increment_indent_level(indent_string: str) -> str:
    if indent_string[-3:] == "ZZZ":
        return indent_string

    # Get the last three characters that can be incremented
    last_three_chars = indent_string[-3:]

    # Strip all the trailing Z's and return the string without them
    lpart = last_three_chars.rstrip("Z")

    # How many characters are needed to be replaced now that the maxed out ones are removed ("Z")
    num_replacements = len(last_three_chars) - len(lpart)

    # New string, where it takes everything except the last character.
    # Increment last non-Z character else add an A, only when it has a lpart
    new_string = (
        lpart[:-1] + (lambda c: chr(ord(c) + 1) if c != "Z" else "A")(lpart[-1])
        if lpart
        else "A"
    )

    # Now that it has incremented add the trailing A's that reset the increments on that digit.
    new_string += "A" * num_replacements

    # If the string is largers than 3, add back the rest of the string
    if len(indent_string) > 3:
        return indent_string[:-3] + new_string
    # Else just return this 3-char string
    else:
        return new_string


# Decrement current outermost indent level, if minimal string ("AAA"), will return input.
def decrement_indent_level(indent_string: str) -> str:
    if indent_string[-3:] == "AAA":
        return indent_string

    # Get the last three chars
    last_three_chars = indent_string[-3:]

    # Strip all the trailing A's and return the string without them.
    lpart = last_three_chars.rstrip("A")

    # How many characters are needed to be replaced now that the bottomed out ones are removed ("Z")
    num_replacements = len(last_three_chars) - len(lpart)

    # New string, where it takes everything except the last character.
    # Decrement last non-A character else add a Z, only when it has a lpart
    new_string = (
        lpart[:-1] + (lambda c: chr(ord(c) - 1) if c != "A" else "Z")(lpart[-1])
        if lpart
        else "Z"
    )

    # Now that it decremented add back the trailing Z's that reset to max when it decrement on that digit.
    new_string += "Z" * num_replacements

    # If the string is larger than 3, add back the rest of the string
    if len(indent_string) > 3:
        return indent_string[:-3] + new_string
    # Else just return this 3-char string
    else:
        return new_string


def convert_jira_markup_to_html(jira_connection_dict, skip_ssl, jira_markup: str):
    render_markup_url = jira_connection_dict["jira_base_url"] + "/rest/api/1.0/render"

    if jira_markup is None or jira_markup == "":
        return "--EMPTY--"

    # Strip all the \x unicode chars.
    jira_markup = re.sub(r"\\x([0-9a-fA-F]{2})", "", jira_markup)

    # Try to dump a string to json. If it fails return a standard string and warning messages.
    if not try_json_dump_string(jira_markup):
        return "--MIGRATION OF TEXT FAILED because of error during JSON validation--"

    headers = {
        "Content-Type": "application/json",
    }

    body = {
        "rendererType": "atlassian-wiki-renderer",
        "unrenderedMarkup": jira_markup,
    }

    response = requests.request(
        "POST",
        render_markup_url,
        headers=headers,
        verify=(not skip_ssl),
        data=json.dumps(body),
    )

    if response.status_code != 200:
        print(response.text)
        print("Conversion of text from jira markup to html failed for text:")
        print(jira_markup)
        print(repr(jira_markup))
        return "--MIGRATION OF TEXT FAILED because of jira renderer error--"
    else:
        return response.text


# Try to dump a string to json. False if fails, True if succeeds.
def try_json_dump_string(string_to_dump) -> bool:
    try:
        json.dumps(string_to_dump)
    except Exception as e:
        print(
            "Json validation of input text failed, migration will fail with this text. Following is the text that fails:"
        )
        print("-----------------Error message-----------------")
        print(e)
        print("-----------------Tried String-----------------")
        print(string_to_dump)
        print("--------Tried string in repl version-----------")
        print(repr(string_to_dump))
        return False
    return True


# Combine jira types within a specific list to a single hierarchy level.
def combine_jira_types(artifact_or_program_type: dict) -> list:
    combined_jira_types = []
    for i in artifact_or_program_type.values():
        if isinstance(i, list):
            combined_jira_types = combined_jira_types + i
        else:
            combined_jira_types = combined_jira_types + [i]
    return combined_jira_types


# Function for pretty printing dictionaries to JSON-like pretty print structure.
def pretty_print(input_dict):
    print("------ Data -------")
    if isinstance(input_dict, dict):
        print(
            json.dumps(input_dict, indent=4, default=str)
        )  # Default=str converts anything unserializable to str
    else:
        try:
            print(
                json.dumps(json.loads(input_dict), indent=4, default=str)
            )  # Default=str converts anything unserializable to str
        except Exception as e:
            print(str(input_dict))
    print("------------------")
