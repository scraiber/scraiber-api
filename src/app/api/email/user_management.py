import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pydantic import EmailStr

from app.api.models.projects import Project2ExternalDB, ProjectPrimaryKeyEmail, ProjectPrimaryKeyNameEmailAdmin, ProjectPrimaryKeyNameEmail

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


async def mail_um_post_internal(payload: ProjectPrimaryKeyNameEmailAdmin):
    admin_term = " and you would be an admin" if payload.is_admin else ""

    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You have been invited to project {name}".format(name=payload.name)
    html_content = """Hi, 

you have been invited to the project {name} (UUID: {project_id}) {admin_term}. 

Congrats!""".format(name=payload.name, project_id=payload.project_id, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_post_internal_admin(payload: ProjectPrimaryKeyNameEmailAdmin, admin_email: EmailStr):
    admin_term = " and would be an admin" if payload.is_admin else ""

    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": admin_email}]

    subject = "The user {changed_user} has been invited to project {name}".format(changed_user=payload.e_mail, name=payload.name)
    html_content = """Hi, 

the user {changed_user} in the project {name} (UUID: {project_id}) has been added{admin_term}.""".format(changed_user=payload.e_mail, name=payload.name, project_id=payload.project_id, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_post_external(payload: ProjectPrimaryKeyNameEmailAdmin):
    admin_term = " and you would be an admin" if payload.is_admin else ""

    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You have been invtied to project {name} at Scraiber".format(name=payload.name)
    html_content = """Hi, 

you have been invited to the project {name} (UUID: {project_id}) at Scraiber{admin_term}. 

Congrats!""".format(name=payload.name, project_id=payload.project_id, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_post_accept_internal(payload: ProjectPrimaryKeyNameEmailAdmin):
    admin_term = " and you are an admin" if payload.is_admin else ""

    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You are now a member of the project {name}".format(name=payload.name)
    html_content = """Hi, 

you are now a member of the project {name} (UUID: {project_id}) {admin_term}. 

Congrats!""".format(name=payload.name, project_id=payload.project_id, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_post_accept_internal_admin(payload: ProjectPrimaryKeyNameEmailAdmin, admin_email: EmailStr):
    admin_term = " and is an admin" if payload.is_admin else ""

    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": admin_email}]

    subject = "The user {changed_user} is now a member of the project {name}".format(changed_user=payload.e_mail, name=payload.name)
    html_content = """Hi, 

the user {changed_user} is now a member of the project {name} (UUID: {project_id}){admin_term}.""".format(changed_user=payload.e_mail, name=payload.name, project_id=payload.project_id, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_put_admin(payload: ProjectPrimaryKeyNameEmailAdmin, admin_email: EmailStr):
    admin_term = "an admin now" if payload.is_admin else "no admin anymore"

    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": admin_email}]

    subject = "The admin state of {changed_user} in project {name} has been changed".format(changed_user=payload.e_mail, name=payload.name)
    html_content = """Hi, 

the user {changed_user} in the project {name} (UUID: {project_id}) is {admin_term}.""".format(changed_user=payload.e_mail, name=payload.name, project_id=payload.project_id, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_put_changed_user(payload: ProjectPrimaryKeyNameEmailAdmin):
    admin_term = "an admin now" if payload.is_admin else "no admin anymore"

    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "Your admin state in project {name} has been changed".format(name=payload.name)
    html_content = """Hi, 

in the project {name} (UUID: {project_id}) you are {admin_term}.""".format(name=payload.name, project_id=payload.project_id, admin_term=admin_term)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_external(payload: ProjectPrimaryKeyNameEmail, admin_email: EmailStr):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": admin_email}]

    subject = "External user {user} has been deleted from project {name}".format(user=payload.e_mail, name=payload.name)
    html_content = """Hi, 

the external user {user} has been deleted from project {name} (UUID: {project_id}).
""".format(user=payload.e_mail, name=payload.name, project_id=payload.project_id)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_all_externals(payload: ProjectPrimaryKeyNameEmail):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "All external users have been deleted from project {name}".format(name=payload.name)
    html_content = """Hi, 

all the external users have been deleted from project {name} (UUID: {project_id}).
""".format(name=payload.name, project_id=payload.project_id)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_admin(payload: ProjectPrimaryKeyNameEmail, admin_email: EmailStr):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": admin_email}]

    subject = "The user {changed_user} in project {name} has been deleted".format(changed_user=payload.e_mail, name=payload.name)
    html_content = """Hi, 

the user {changed_user} in the project {name} (UUID: {project_id}) has been deleted.""".format(changed_user=payload.e_mail, name=payload.name, project_id=payload.project_id)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_deleted_user(payload: ProjectPrimaryKeyNameEmail):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You have been deleted from project {name}".format(name=payload.name)
    html_content = """Hi, 

you have been deleted from the project {name} (UUID: {project_id}).""".format(name=payload.name, project_id=payload.project_id)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_accept_internal(payload: ProjectPrimaryKeyNameEmail):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "You declined the membership of the project {name}".format(name=payload.name)
    html_content = """Hi, 

you declined the membership of the project {name} (UUID: {project_id}). 

Congrats!""".format(name=payload.name, project_id=payload.project_id)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_um_delete_accept_internal_admin(payload: ProjectPrimaryKeyNameEmail, admin_email: EmailStr):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": admin_email}]

    subject = "The user {changed_user} declined the membership of the project {name}".format(changed_user=payload.e_mail, name=payload.name)
    html_content = """Hi, 

the user {changed_user} declined the membership of the project {name} (UUID: {project_id}).""".format(changed_user=payload.e_mail, name=payload.name, project_id=payload.project_id)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
