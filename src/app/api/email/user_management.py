import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pydantic import EmailStr

from app.api.models.projects import Project2ExternalDB, ProjectPrimaryKeyEmail, ProjectSchemaEmail


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


async def mail_um_post_internal(payload: Project2ExternalDB):
    admin_term = " and you are an admin" if payload.is_admin else ""

    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You have been added to project {name}".format(name=payload.name)
    html_content = """Hi, 

you have been added to the project {name} in region {region}{admin_term}. 

Congrats!""".format(name=payload.name, region=payload.region, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_post_internal_owner(payload: Project2ExternalDB, owner_email: EmailStr):
    admin_term = " and is an admin" if payload.is_admin else ""

    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": owner_email}]

    subject = "the user {changed_user} has been added to project {name}".format(changed_user=payload.e_mail, name=payload.name)
    html_content = """Hi, 

the user {changed_user} in the project {name} in region {region} has been added{admin_term}.""".format(changed_user=payload.e_mail, name=payload.name, region=payload.region, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_post_external(payload: Project2ExternalDB):
    admin_term = " and you are an admin" if payload.is_admin else ""

    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You have been invtied to project {name} at Scraiber".format(name=payload.name)
    html_content = """Hi, 

you have been invited to the project {name} at Scraiber in region {region}{admin_term}. 

Congrats!""".format(name=payload.name, region=payload.region, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_put_owner(payload: Project2ExternalDB, owner_email: EmailStr):
    admin_term = "an admin now" if payload.is_admin else "no admin anymore"

    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": owner_email}]

    subject = "The admin state of {changed_user} in project {name} has been changed".format(changed_user=payload.e_mail, name=payload.name)
    html_content = """Hi, 

the user {changed_user} in the project {name} in region {region} is {admin_term}.""".format(changed_user=payload.e_mail, name=payload.name, region=payload.region, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_put_changed_user(payload: Project2ExternalDB):
    admin_term = "an admin now" if payload.is_admin else "no admin anymore"

    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Your admin state in project {name} has been changed".format(name=payload.name)
    html_content = """Hi, 

in the project {name} in region {region} you are {admin_term}. """.format(name=payload.name, region=payload.region, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_external(payload: ProjectPrimaryKeyEmail, owner_email: EmailStr):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": owner_email}]

    subject = "External user {user} has been deleted from project {name} in region {region}".format(user=payload.e_mail, name=payload.name, region=payload.region)
    html_content = """Hi, 

the external user {user} has been deleted from project {name} in region {region}.
""".format(user=payload.e_mail, name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_all_externals(payload: ProjectPrimaryKeyEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "All external users have been deleted from project {name} in region {region}".format(name=payload.name, region=payload.region)
    html_content = """Hi, 

all the external users have been deleted from project {name} in region {region}.
""".format(name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_owner(payload: Project2ExternalDB, owner_email: EmailStr):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": owner_email}]

    subject = "The user {changed_user} in project {name} has been deleted".format(changed_user=payload.e_mail, name=payload.name)
    html_content = """Hi, 

the user {changed_user} in the project {name} in region {region} has been deleted.""".format(changed_user=payload.e_mail, name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_deleted_user(payload: Project2ExternalDB):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You have been deleted from project {name}".format(name=payload.name)
    html_content = """Hi, 

you have been deleted from the project {name} in region {region}.""".format(name=payload.name, region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)

