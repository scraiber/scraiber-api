import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

async def write_test_mail(email: str):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": email,"name":"Tobi"}]

    subject = "Scraiber registration"
    html_content = "<html><body>Please use to verify e-mail {0}</body></html>".format("abcd")

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)