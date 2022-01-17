import os
import subprocess
import random
from base64 import b64encode
from datetime import datetime, timezone
from kubernetes import client
from kubernetes.client.rest import ApiException
import string
from fastapi import HTTPException

from app.kubernetes_setup import clusters
from app.api.models.projects import PrimaryKeyWithUserID, PrimaryKeyWithUserIDAndCertNo, Project2UserDB
from app.api.models.certificates import Certificate2User, Certificate2UserDB
from app.api.crud import project2user, certificates


async def region_user_list(payload: Certificate2User):
    projects_response = await project2user.get_by_user_and_region(payload)
    if not projects_response:
        raise HTTPException(status_code=404, detail="No Project found for user and region")
    return projects_response

async def add_user_to_namespace(payload: PrimaryKeyWithUserID):
    try:
        certificate_no = await certificates.get_certificate_number(Certificate2User(region=payload.region, user_id=payload.candidate_id))
    except HTTPException:
        #no user added if there is no certificate
        return payload
    client_rbacv1api_region = clusters[payload.region]["Client-RbacAuthorizationV1Api"]

    role_binding = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(namespace=payload.name, name="user-role-binding-for-"+str(payload.candidate_id)),
        subjects=[client.V1Subject(name=str(payload.candidate_id)+"_"+str(certificate_no), kind="User")],
        role_ref=client.V1RoleRef(kind="ClusterRole", api_group="rbac.authorization.k8s.io", name="edit"))
        
    try:
        client_rbacv1api_region.create_namespaced_role_binding(namespace=payload.name,body=role_binding)
    except ApiException as e:
        print("Exception when trying to connect user "+str(payload.candidate_id)+" to namespace "+payload.name+" in "+payload.region+": %s\n" % e)
    return payload


async def add_role_bindings_for_user(payload: Certificate2User):
    projects_response = await region_user_list(payload)
    for item in projects_response:
        project_item = Project2UserDB(**item)
        await add_user_to_namespace(PrimaryKeyWithUserID(name=project_item.name, region=payload.region, candidate_id=payload.user_id))
    return payload


async def patch_kubernetes_user(payload: PrimaryKeyWithUserID):
    try:
        certificate_no = await certificates.get_certificate_number(Certificate2User(region=payload.region, user_id=payload.candidate_id))
    except HTTPException:
        #no user patched if there is no certificate
        return payload

    client_rbacv1api_region = clusters[payload.region]["Client-RbacAuthorizationV1Api"]

    role_binding = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(namespace=payload.name, name="user-role-binding-for-"+str(payload.candidate_id)),
        subjects=[client.V1Subject(name=str(payload.candidate_id)+"_"+str(certificate_no), kind="User")],
        role_ref=client.V1RoleRef(kind="ClusterRole", api_group="rbac.authorization.k8s.io", name="edit"))

    try:
        client_rbacv1api_region.patch_namespaced_role_binding(name="user-role-binding-for-"+str(payload.candidate_id),namespace=payload.name,body=role_binding)
    except ApiException as e:
        print("Exception when trying to update role binding of user "+str(payload.candidate_id)+" to namespace "+payload.name+" in "+payload.region+": %s\n" % e)
    return payload


async def patch_role_bindings_for_user(payload: Certificate2UserDB):
    projects_response = await region_user_list(Certificate2User(region=payload.region, user_id=payload.user_id))
    for item in projects_response:
        project_item = Project2UserDB(**item)
        await patch_kubernetes_user(PrimaryKeyWithUserID(name=project_item.name, region=payload.region, candidate_id=payload.user_id))
    return payload


async def delete_kubernetes_user(payload: PrimaryKeyWithUserID):
    response = await certificates.get(Certificate2User(region=payload.region, user_id=payload.candidate_id))
    if not response:
        return payload

    client_rbacv1api_region = clusters[payload.region]["Client-RbacAuthorizationV1Api"]
    try:
        client_rbacv1api_region.delete_namespaced_role_binding(name="user-role-binding-for-"+str(payload.candidate_id), namespace=payload.name)
    except ApiException as e:
        print("Exception when trying to delete user "+str(payload.candidate_id)+" from namespace "+payload.name+" in "+payload.region+": %s\n" % e)
    return payload


async def delete_role_bindings_for_user(payload: Certificate2User):
    projects_response = await region_user_list(payload)
    for item in projects_response:
        project_item = Project2UserDB(**item)
        await delete_kubernetes_user(PrimaryKeyWithUserIDAndCertNo(name=project_item.name, region=payload.region, candidate_id=payload.user_id))
    return payload


async def create_kubernetes_config(payload: Certificate2User):
    client_cert1api_region = clusters[payload.region]["Client-CertificatesV1Api"]
    server_endpoint = clusters[payload.region]["server_endpoint"]
    ca_cluster = clusters[payload.region]["ca_cluster"]

    await region_user_list(payload)

    increment_schema = await certificates.create_or_increment(payload)
    certificate_no = increment_schema.certificate_no

    if certificate_no==1:
        await add_role_bindings_for_user(payload)
    else:
        await patch_role_bindings_for_user(increment_schema)

    user_id_and_cert_no = str(payload.user_id)+"_"+str(certificate_no)
    random_string = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=30))
    file_path_prefix = "/cache/"+user_id_and_cert_no+"_"+payload.region+"_"+random_string

    key_path = file_path_prefix+".key"
    subprocess.check_output("openssl genrsa -out "+key_path+" 4096", shell=True)
    key = subprocess.check_output('cat '+key_path+' | base64 | tr -d "\n"', shell=True).decode('utf-8')

    conf_file = """[ req ]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn

[ dn ]
CN={USER_ID}
O = user

[ v3_ext ]
authorityKeyIdentifier=keyid,issuer:always
basicConstraints=CA:FALSE
keyUsage=keyEncipherment,dataEncipherment
extendedKeyUsage=serverAuth,clientAuth
""".format(USER_ID=user_id_and_cert_no)
    conf_path = file_path_prefix+".cnf"
    with open(conf_path, 'w') as f:
        f.write(conf_file)
    crt = subprocess.check_output("openssl req -config "+conf_path+" -new -key "+key_path, shell=True)

    if os.path.exists(key_path):
        os.remove(key_path)
    if os.path.exists(conf_path):
        os.remove(conf_path)


    body = client.V1CertificateSigningRequest(
        metadata=client.V1ObjectMeta(name="csr-for-"+user_id_and_cert_no),
        spec=client.V1CertificateSigningRequestSpec(request=b64encode(crt).decode("utf-8"), signer_name="kubernetes.io/kube-apiserver-client", usages=["client auth"])
    )
    client_cert1api_region.create_certificate_signing_request(body, field_manager="Scraiber-admin")


    body = client_cert1api_region.read_certificate_signing_request_status("csr-for-"+user_id_and_cert_no)
    approval_condition = client.V1CertificateSigningRequestCondition(
        last_update_time=datetime.now(timezone.utc).astimezone(),
        status="True",
        type='Approved')
    body.status.conditions = [approval_condition]
    client_cert1api_region.replace_certificate_signing_request_approval("csr-for-"+user_id_and_cert_no, body)
    response = client_cert1api_region.read_certificate_signing_request_status("csr-for-"+user_id_and_cert_no)
    crt_response = response.status.certificate


    output_string = '''apiVersion: v1
current-context: Scraiber-{CLUSTER_NAME}-{USER_ID}
kind: Config
preferences: {EMPTY}
clusters:
- cluster:
    server: {SERVER_ENDPOINT}
    certificate-authority-data: {CA_CLUSTER}
  name: {CLUSTER_NAME}
contexts:
- context:
    cluster: {CLUSTER_NAME}
    user: {USER_ID}
  name: Scraiber-{CLUSTER_NAME}-{USER_ID}
users:
- name: {USER_ID}
  user:
    client-certificate-data: {CLIENT_CERT}
    client-key-data: {CLIENT_KEY}
'''.format(EMPTY="{}", USER_ID=user_id_and_cert_no, CLUSTER_NAME=payload.region, SERVER_ENDPOINT=server_endpoint, CA_CLUSTER=ca_cluster, CLIENT_CERT=crt_response, CLIENT_KEY=key)
 
    return output_string