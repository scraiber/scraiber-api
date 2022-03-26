import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.api.models.projects import ProjectPrimaryKeyNameEmail

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


async def mail_project_post(payload: ProjectPrimaryKeyNameEmail):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Project {name} has been created by you".format(name=payload.name)
    html_content = """Hi, 

the project {name} (UUID: {project_id}) has been created by you. 

Congrats!""".format(name=payload.name, project_id=payload.project_id)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


async def mail_project_name_put(payload: ProjectPrimaryKeyNameEmail, new_name: str):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Project {name} has been renamed to {new_name}".format(name=payload.name, new_name=new_name)
    html_content = """Hi, 
    
project {name} (UUID: {project_id}) has been renamed to {new_name}.
""".format(name=payload.name, project_id=payload.project_id, new_name=new_name)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)    


async def mail_project_delete(payload: ProjectPrimaryKeyNameEmail):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Project {name} has been deleted".format(name=payload.name)
    html_content = """Hi, 

the project {name} (UUID: {project_id}) has been deleted. 
""".format(name=payload.name, project_id=payload.project_id)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)