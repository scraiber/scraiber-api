import os
from kubernetes import client
from kubernetes.client.rest import ApiException
from fastapi import HTTPException
from typing import List

from app.kubernetes_setup import clusters
from app.api.models.projects import Project2UserDB, EmailWithUserID
from app.api.models.namespaces import NamespacePrimaryKey, NamespaceSchema, NamespacePrimaryKeyEmail
from app.api.crud import project2user, namespaces



async def namespace_user_list(user_id: str) -> List[NamespacePrimaryKey]:
    projects_response = await project2user.get_by_user(user_id)
    if not projects_response:
        raise HTTPException(status_code=404, detail="User not associated to any project")

    output_list = []
    for projects_response_item in projects_response:
        namespaces_project = await namespaces.get_by_project(Project2UserDB(**projects_response_item).project_id)
        if namespaces_project:
            output_list.extend([NamespacePrimaryKey(**namespace_item) for namespace_item in namespaces_project])
    return output_list


async def region_user_list(user_id: str) -> List[str]:
    associated_projects = await project2user.get_by_user(user_id)
    if not associated_projects:
        raise HTTPException(status_code=404, detail="User not associated to any project")

    regions = set()
    for projects_response_item in associated_projects:
        namespaces_for_project = await namespaces.get_by_project(Project2UserDB(**projects_response_item).project_id)
        if not namespaces_for_project:
            continue
        regions.update([NamespaceSchema(**item).region for item in namespaces_for_project])

    if len(regions) == 0:
        raise HTTPException(status_code=404, detail="No regions associated to user")
    return list(regions)


async def add_user_to_namespace(payload: NamespacePrimaryKeyEmail):
    client_rbacv1api_region = clusters[payload.region]["Client-RbacAuthorizationV1Api"]

    role_binding = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(namespace=payload.name, name="user-role-binding-for-"+payload.e_mail),
        subjects=[client.V1Subject(name=payload.e_mail, kind="User")],
        role_ref=client.V1RoleRef(kind="ClusterRole", api_group="rbac.authorization.k8s.io", name="edit"))
        
    try:
        client_rbacv1api_region.create_namespaced_role_binding(namespace=payload.name,body=role_binding)
    except ApiException as e:
        print("Exception when trying to connect user "+payload.e_mail+" to namespace "+payload.name+" in "+payload.region+": %s\n" % e)
    return payload


async def add_role_bindings_for_user(payload: EmailWithUserID):
    namespace_response = await namespace_user_list(payload.user_id)
    for item in namespace_response:
        await add_user_to_namespace(NamespacePrimaryKeyEmail(name=item.name, region=item.region, e_mail=payload.user_id))
    return payload


async def delete_kubernetes_user(payload: NamespacePrimaryKeyEmail):
    client_rbacv1api_region = clusters[payload.region]["Client-RbacAuthorizationV1Api"]
    try:
        client_rbacv1api_region.delete_namespaced_role_binding(name="user-role-binding-for-"+payload.e_mail, namespace=payload.name)
    except ApiException as e:
        print("Exception when trying to delete user "+payload.e_mail+" from namespace "+payload.name+" in "+payload.region+": %s\n" % e)
    return payload


async def delete_role_bindings_for_user(payload: EmailWithUserID):
    projects_response = await namespace_user_list(payload.user_id)
    for item in projects_response:
        await delete_kubernetes_user(NamespacePrimaryKeyEmail(name=item.name, region=item.region, e_mail=payload.user_id))
    return payload


async def create_kubernetes_config(user_id: str) -> List[str]:
    regions = await region_user_list(user_id)

    if len(regions) == 0:
        return []

    output = ["apiVersion: v1", "clusters:"]

    for region in regions:
        output.append(["- cluster:",
                       "    certificate-authority-data: " + clusters[region]["certificate-authority-data"],
                       "    server: " + clusters[region]["concierge-endpoint"],
                       "  name: scraiber-" + region])

    output.append("contexts:")

    for region in regions:
        output.extend(["- context:",
                       "    cluster: scraiber-" + region,
                       "    user: scraiber-" + region + "-user",
                       "  name: scraiber-" + region])

    output.extend(["current-context: scraiber-" + regions[0],
                   "kind: Config", "preferences: {}",
                   "users:"])

    for region in regions:
        output.extend(["- name: scraiber-" + region + "-user",
                       "  user:",
                       "    exec:",
                       "      apiVersion: client.authentication.k8s.io/v1beta1",
                       "      args:",
                       "      - login",
                       "      - oidc",
                       "      - --enable-concierge",
                       "      - --concierge-api-group-suffix=pinniped.dev",
                       "      - --concierge-authenticator-name=jwt-authenticator",
                       "      - --concierge-authenticator-type=jwt",
                       "      - --concierge-endpoint=" + clusters[region]["concierge-endpoint"],
                       "      - --concierge-ca-bundle-data=" + clusters[region]["certificate-authority-data"],
                       "      - --issuer=" + os.environ["AUTH0_DOMAIN"],
                       "      - --client-id=" + os.environ["AUTH0_CLIENTID_FRONTEND"],
                       "      - --scopes=openid,email",
                       "      - --listen-port=12345",
                       "      - --request-audience=" + os.environ["AUTH0_CLIENTID_FRONTEND"],
                       "      command: /usr/local/bin/pinniped",
                       "      provideClusterInfo: true"])

    return output
