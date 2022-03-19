import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pydantic import EmailStr

from app.api.models.projects import Project2ExternalDB, ProjectPrimaryKeyEmail

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

domain_name = os.environ['DOMAIN_NAME']


async def mail_registration_confirmation(email: EmailStr):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": email}]

    subject = "You have registered at Scraiber"
    html_content = """Hi, 

you have registered at Scraiber.

Congrats!"""

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_password_reset(email: EmailStr, token: str):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": email}]

    subject = "Reset your password at Scraiber"
    html_content = """Hi, 

in order to reset your password at Scraiber, please visit this page <a href="{domain_name}/password-reset/?token={token}">here</a>.
""".format(domain_name=domain_name, token=token)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_password_reset_confirmation(email: EmailStr):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": email}]

    subject = "You have successfully reset your password at Scraiber"
    html_content = """Hi, 

you have successfully reset your password at Scraiber.

Congrats!"""

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_verify_account(email: EmailStr, token: str):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": email}]

    subject = "Verify your e-mail at Scraiber"
    html_content = """Hi, 

in order to verify your e-mail at Scraiber, please visit this page <a href="{domain_name}/verify-account/?token={token}">here</a>.
""".format(domain_name=domain_name, token=token)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_verification_confirmation(email: EmailStr):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": email}]

    subject = "You have successfully verified your e-mail at Scraiber"
    html_content = """Hi, 

you have successfully verified your e-mail at Scraiber.

Congrats!"""

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)



async def mail_deletion_confirmation(email: EmailStr):
    sender = {"name": "Scraiber", "email": "no-reply@scraiber.com"}
    to = [{"email": email}]

    subject = "Your account at Scraiber has been deleted"
    html_content = """Hi, 

your account at Scraiber has been deleted.

Congrats!"""

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
