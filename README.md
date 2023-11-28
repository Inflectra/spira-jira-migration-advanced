# Advanced Jira to Spira Migration Tool (spira-jira-migration-advanced)

This tool is a migration tool for migrating jira issues to SpiraPlan artifacts that has advanced configuration options on mapping fields, products, and programs.

This tool was originally developed by Tietoevry AB for Saab AB usage. The tool was envisioned for general use in the open source space for SpiraPlan and Inflectra, and it was released under the MIT license in late 2023.

For professional support, please contact Inflectra, who can provide contacts within Tietoevry that can assist with your use case.

## Features the script can currently handle

- Program level:
  - Import Customlists at system level
  - Import Milestones
  - Import Capabilites and map them to milestones
  - Clear artifacts and milestones
- Product level:
  - Import Customlists at product template level
  - Import Releases and put them in a hierarchy
  - Import Components
  - Import Requirements, put them in a hierarchy and map them to Capabilites, Releases and Components
  - Import Incidents
  - Import Tasks
  - Map standard and custom properties from Jira
  - Import Comments
  - Set Artifact associations (within the same spira product)
  - Import Documents to separate folder and set artifact association (within the same spira product)
  - Set document-artifact association (within the same spira product) in separate command.
  - Statuses: sets the correct status of artifacts in Spira, defined in the mapping template in the script
  - Priorities: sets the correct status of artifacts in Spira, defined in the mapping template in the script
  - Clear all artifacts, milestones, releases except documents in one command
  - Clear all documents at product level in one command

## Features the script will be able to handle in the future

- Pre-flight checks to prevent errors during migration
- Migration crash resume feature
- Migration verbose and more useful progress logging
- Add a good example of usage

## Get Started

**Prerequisites**

Python >=3.10

**Managing python dependencies with requirement.txt**

To get the correct dependencies for each project they should be stored in a requirement.txt file inside the project.

To install all dependencies from a requirements.txt file run: pip install -r requirements.txt

**Update the requirements.txt**
If you have added or updated an installed python package, remember redo pip freeze > requirements.txt and overwrite the old requirements.txt file

**Autoformat**
To auto format your code on save go to VSCode settings->TextEditor→Formatting and tick the Format-on-Save-box.

## Usage

### Full issue migration flow with defaults

### Before migration

**Prepare Spira**
Create all users

Create a program and prepare artifacts at program level
Capabilities:

- Set priority
- Set status
- Set type
- Create custom properties set in the mapping template and Jira Id of type text.

Create a product and prepare artifacts at template level:  
Requirments:

- Set importance
- Set status
- Set type
- Create custom properties set in the mapping template and Jira Id of type text.

Incidents:

- Set priority
- Set status
- Set type
- Create custom properties set in the mapping template and Jira Id of type text.

Tasks:

- Set type
- Set priority
- Create custom properties set in the mapping template and Jira Id of type text.

Documents:

- Set custom properties
  - Property name: A
  - Property name: B
  - Property name: C

**Prepare Config files in migration tool**

- The .env.template file needs to be copied and named .env and placed in the root of the script directory. Fill in each variable with the connection info, credentials and correct access rights to Jira/Spira
- The mapping template (mapping_template.yaml) with spira project id and other relevant information needs to be filled in.

**Order of commands and examples**
A program or product identifier can either be the integer Id or the full case sensitive name for the program/product.

```shell
python3 main.py clean_program <program identifier>  -nossl
python3 main.py clean_product <product identifier> -nossl


python3 main.py migrate_customlists <list of jira projects without commas, e.g. PROJ1 PROJ2 PROJ3 > -system -nossl
python3 main.py migrate_customlists <list of jira projects without commas, e.g. PROJ1 PROJ2 PROJ3 > -template <list of spira templateids or templatenames without commas, e.g. 12 13 Migration tool for Jira  >  -nossl

python3 main.py migrate_milestones <program identifier> <jql> <list of jira projects without commas, e.g. PROJ1 PROJ2 PROJ3 > -nossl
python3 main.py migrate_capabilities <program identifier> <jql> -nossl
python3 main.py migrate_releases <product identifier> <list of jira projects without commas> -nossl
python3 main.py migrate_components <product identifier> <list of jira projects without commas> -nossl
python3 main.py migrate_issues <product identifier> <jql> -nossl
python3 main.py migrate_associations <product identifier> <jql> -nossl
python3 main.py migrate_comments <product identifier> <jql> -nossl
```

Document migration handling
If document has not been migrated

```shell
python3 main.py migrate_documents <product identifier> <jql> -nossl
```

If document has been migrated but artifacts av been removed and new one inserted

```shell
python3 main.py add_document_associations <product identifier> -nossl
```

Remove all documents

```shell
python3 main.py clean_product_documents <product identifier> -nossl
```

**Flags**
All of these optional flags exist on most of the commands, but see specific command for help with relevant flags.

```
-m --mapping <file>
```

specify a file other than the default from which to take the mapping config

```
-jo --jira-to-json-output <file>
```

specify a file path other than the default to where the extracted json is going to go.

```
-system --system-level
```

Boolean flag, set when migrating customlists at system level, will only be needed to do once. Will override template flag.

```
-template --spira-templates
```

Flag set when migrating customlists at template level, specifies a list of template name or id .

```
-nossl --skip-ssl-check
```

Boolean flag, specify if we want to disable the ssl check. Disabling SSL opens the script for man-in-the-middle-attacks but might be required if there is no valid HTTPS cert available.
