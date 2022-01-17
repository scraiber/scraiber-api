import os
from pydantic import EmailStr
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.api.models.projects import ProjectPrimaryKeyEmail, ProjectSchemaEmail


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


async def mail_project_post(payload: ProjectPrimaryKeyEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Project {name} has been created by you in region {region}".format(name=payload.name, region=payload.region)
    html_content = """Hi, 

the project {name} has been created by you in region {region} and you are the owner. 

Congrats!""".format(name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


async def mail_project_put(payload: ProjectSchemaEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "The resources of project {name} have been updated".format(name=payload.name, region=payload.region)
    html_content = """Hi, 
    
the project {name} in region {region} have been updated to:

- Maximum cpu for project: {max_project_cpu}
- Maximum memory for project: {max_project_mem} MiB
- Default limit cpu for resource (i.e., pod) in project: {default_limit_pod_cpu}
- Default limit memory for resource (i.e., pod) in project: {default_limit_pod_mem} MiB
""".format(name=payload.name,region=payload.region, max_project_cpu=payload.max_project_cpu, max_project_mem=payload.max_project_mem, 
        default_limit_pod_cpu=payload.default_limit_pod_cpu, default_limit_pod_mem=payload.default_limit_pod_mem)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)    


async def mail_project_delete(payload: ProjectPrimaryKeyEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Project {name} in region {region} has been deleted".format(name=payload.name, region=payload.region)
    html_content = """Hi, 

the project {name} in region {region} has been deleted. 
""".format(name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)