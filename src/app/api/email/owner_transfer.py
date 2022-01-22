import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.api.models.projects import ProjectPrimaryKeyEmail


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


async def mail_ot_post(payload: ProjectPrimaryKeyEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You have been invited to become the owner of project {name}".format(name=payload.name)
    html_content = """Hi, 

you have been invited to become the owner of the project {name} in region {region}.""".format(name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


async def mail_project_put_old_owner(payload: ProjectPrimaryKeyEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "The ownership of project {name} has been transferred".format(name=payload.name)
    html_content = """Hi, 

the owner ship of the project {name} in region {region} has been transferred.""".format(name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)    


async def mail_project_put_new_owner(payload: ProjectPrimaryKeyEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "The ownership of project {name} has been transferred to you".format(name=payload.name)
    html_content = """Hi, 

the owner ship of the project {name} in region {region} has been transferred to you.""".format(name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)    


async def mail_project_delete_inform_owner(payload: ProjectPrimaryKeyEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "There is no ownership candidate of project {name} anymore".format(name=payload.name)
    html_content = """Hi, 

there is no ownership candidate of project {name} in region {region} anymore. 
""".format(name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


async def mail_project_delete_inform_candidate(payload: ProjectPrimaryKeyEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You are not ownership candidate of project {name} anymore".format(name=payload.name)
    html_content = """Hi, 

you are not ownership candidate of project {name} in region {region} anymore. 
""".format(name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)