import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from uuid import UUID

from app.api.models.namespaces import NamespacePrimaryKeyEmailInfo, NamespaceSchemaProjectNameEmailInfo
from app.api.models.projects import ProjectPrimaryKeyName

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


async def mail_namespace_post(payload: NamespacePrimaryKeyEmailInfo):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Namespace {name} has been created for project {project_name}".format(name=payload.name, project_name=payload.project_name)
    html_content = """Hi, 

the namespace {name} in region {region} has been created for project {project_name} (UUID: {project_id}) by {creator}. 

Have fun!""".format(name=payload.name, region=payload.region, project_name=payload.project_name, project_id=payload.project_id, creator=payload.creator)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


async def mail_namespace_put_resources(payload: NamespaceSchemaProjectNameEmailInfo):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "The resources of namespace {name} for project {project_name} have been updated".format(name=payload.name, project_name=payload.project_name)
    html_content = """Hi, 
    
the resources of namespace {name} in region {region} for project {project_name} (UUID: {project_id}) have been updated by {creator} to:

- Maximum cpu for project: {max_namespace_cpu}
- Maximum memory for project: {max_namespace_mem} MiB
- Default limit cpu for resource (i.e., pod) in project: {default_limit_pod_cpu}
- Default limit memory for resource (i.e., pod) in project: {default_limit_pod_mem} MiB
""".format(name=payload.name,region=payload.region, project_name=payload.project_name, project_id=payload.project_id,
           max_namespace_cpu=payload.max_namespace_cpu, max_namespace_mem=payload.max_namespace_mem,
           default_limit_pod_cpu=payload.default_limit_pod_cpu, default_limit_pod_mem=payload.default_limit_pod_mem,
           creator=payload.creator)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)    


async def mail_namespace_delete(payload: NamespacePrimaryKeyEmailInfo):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Namespace {name} for project {project_name} has been deleted".format(name=payload.name, project_name=payload.project_name)
    html_content = """Hi, 

the namespace {name} in region {region} has been deleted for project {project_name} (UUID: {project_id}) by {creator}. 
""".format(name=payload.name, region=payload.region, project_name=payload.project_name, project_id=payload.project_id, creator=payload.creator)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)