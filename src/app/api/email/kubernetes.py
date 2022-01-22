import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.api.models.projects import RegionEmail


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


async def mail_kubernetes_new_kubeconfig(payload: RegionEmail):
    sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
    to = [{"email": payload.e_mail}]

    subject = "A new kubeconfig has been created for you in region {region}".format(region=payload.region)
    html_content = """Hi, 

a new kubeconfig has been created for you in region {region}.

In case, it does not work or was not you who did that, please generate a new one.""".format(region=payload.region)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)

