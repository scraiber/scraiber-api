import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from uuid import UUID

from app.api.models.namespaces import NamespacePrimaryKeyTransferEmailInfo, NamespacePrimaryKeyEmailInfo, NamespaceSchemaProjectNameEmailInfo
from app.api.models.projects import ProjectPrimaryKeyName

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


async def mail_post_project_transfer(payload: NamespacePrimaryKeyTransferEmailInfo):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Namespace {name} is posted for transfer been from project {old_project_name} to {new_project_name}" \
        .format(name=payload.name, old_project_name=payload.old_project_name, new_project_name=payload.new_project_name)
    html_content = """Hi, 

the namespace {name} in region {region} is posted for transfer from project {old_project_name} (UUID: {old_project_id}) to {new_project_name} (UUID: {new_project_id}) by {creator}.
""".format(name=payload.name, region=payload.region, old_project_name=payload.old_project_name,
           old_project_id=payload.old_project_id, new_project_name=payload.new_project_name,
           new_project_id=payload.new_project_id, creator=payload.creator)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


async def mail_accept_project_transfer(payload: NamespacePrimaryKeyTransferEmailInfo):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Namespace {name} has been transferred from project {old_project_name} to {new_project_name}" \
        .format(name=payload.name, old_project_name=payload.old_project_name, new_project_name=payload.new_project_name)
    html_content = """Hi, 

the namespace {name} in region {region} has been transferred from project {old_project_name} (UUID: {old_project_id}) to {new_project_name} (UUID: {new_project_id}) by {creator}.
""".format(name=payload.name, region=payload.region, old_project_name=payload.old_project_name,
           old_project_id=payload.old_project_id, new_project_name=payload.new_project_name,
           new_project_id=payload.new_project_id, creator=payload.creator)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


async def mail_delete_project_transfer(payload: NamespacePrimaryKeyTransferEmailInfo):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Namespace {name} is not a transfer candidate from project {old_project_name} to {new_project_name} anymore" \
        .format(name=payload.name, old_project_name=payload.old_project_name, new_project_name=payload.new_project_name)
    html_content = """Hi, 

the namespace {name} in region {region} is not a transfer candidate from project {old_project_name} (UUID: {old_project_id}) to {new_project_name} (UUID: {new_project_id}) anymore.
User {creator} has removed it.
""".format(name=payload.name, region=payload.region, old_project_name=payload.old_project_name,
           old_project_id=payload.old_project_id, new_project_name=payload.new_project_name,
           new_project_id=payload.new_project_id, creator=payload.creator)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)