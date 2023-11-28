from spira import Spira


def clean_spira_product(spira: Spira, spira_product_id):
    # Remove all association between documents and artifacts
    print("Cleaning association between documents and artifacts...")
    clean_document_associations(spira, spira_product_id)

    # Remove all the requirements
    print("Cleaning requirements...")
    clean_requirements(spira, spira_product_id)

    # Remove all the incidents
    print("Cleaning incidents...")
    clean_incidents(spira, spira_product_id)

    # Remove all the tasks
    print("Cleaning tasks...")
    clean_tasks(spira, spira_product_id)

    # Remove all the components
    print("Cleaning components...")
    clean_components(spira, spira_product_id)

    # Remove all the releases
    print("Cleaning releases...")
    clean_releases(spira, spira_product_id)


def clean_spira_product_documents(spira: Spira, spira_product_id):
    # Remove all the documents
    print("Cleaning project documents...")
    clean_documents(spira, spira_product_id)

    # Remove all the document folders
    print("Cleaning project document folders...")
    clean_spira_product_document_folders(spira, spira_product_id)


def clean_spira_program(spira: Spira, program_id):
    # Remove all the capabilites
    print("Cleaning capabilities...")
    clean_capabilities(spira, program_id)

    # Remove all the milestones
    print("Cleaning milestones...")
    clean_milestones(spira, program_id)


def clean_requirements(spira: Spira, spira_product_id):
    requirements = spira.get_all_requirements(spira_product_id)

    for req in requirements:
        try:
            spira.delete_requirement(spira_product_id, req["RequirementId"])
        except Exception as e:
            continue


def clean_incidents(spira: Spira, spira_product_id):
    incidents = spira.get_all_incidents(spira_product_id)

    for inc in incidents:
        try:
            spira.delete_incident(spira_product_id, inc["IncidentId"])
        except Exception as e:
            continue


def clean_tasks(spira: Spira, spira_product_id):
    tasks = spira.get_all_tasks(spira_product_id)

    for task in tasks:
        try:
            spira.delete_task(spira_product_id, task["TaskId"])
        except Exception as e:
            continue


def clean_components(spira: Spira, spira_product_id):
    components = spira.get_all_components(spira_product_id, include_deleted=True)

    for comp in components:
        try:
            spira.delete_component(spira_product_id, comp["ComponentId"])
        except Exception as e:
            continue


def clean_document_associations(spira: Spira, spira_product_id):
    documents = spira.get_all_documents(spira_product_id)

    for doc in documents:
        # When getting all documents the metadata about the attached artifacts are not included
        # that is why we need a separate call to get each document
        document_data = spira.get_document(spira_product_id, doc["AttachmentId"])
        if document_data["AttachedArtifacts"]:
            for attachment in document_data["AttachedArtifacts"]:
                try:
                    spira.remove_artifact_document_association(
                        spira_product_id,
                        attachment["ArtifactTypeId"],
                        attachment["ArtifactId"],
                        doc["AttachmentId"],
                    )
                except Exception as e:
                    print(e)
                    continue


def clean_releases(spira: Spira, spira_product_id):
    releases = spira.get_all_releases(spira_product_id)

    for rel in releases:
        try:
            spira.delete_release(spira_product_id, rel["ReleaseId"])
        except Exception as e:
            continue


def clean_capabilities(spira: Spira, program_id):
    capabilities = spira.get_all_program_capabilities(program_id)
    for cap in capabilities:
        try:
            spira.delete_program_capability(program_id, cap["CapabilityId"])
        except Exception as e:
            continue


def clean_milestones(spira: Spira, program_id):
    milestones = spira.get_all_program_milestones(program_id)
    for mil in milestones:
        try:
            spira.delete_program_milestone(program_id, mil["MilestoneId"])
        except Exception as e:
            continue


def clean_documents(spira: Spira, spira_product_id):
    documents = spira.get_all_documents(spira_product_id)

    for doc in documents:
        try:
            spira.delete_document(spira_product_id, doc["AttachmentId"])
        except Exception as e:
            continue


def clean_spira_product_document_folders(spira: Spira, spira_product_id):
    folders = spira.get_all_document_folders(spira_product_id)

    for folder in folders:
        try:
            spira.delete_document_folder(
                spira_product_id, folder["ProjectAttachmentFolderId"]
            )
        except Exception as e:
            continue
