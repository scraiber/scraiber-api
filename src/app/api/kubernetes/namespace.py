from kubernetes import client
from kubernetes.client.rest import ApiException

from app.kubernetes_setup import clusters
from app.api.models.projects import ProjectSchema, ProjectPrimaryKey


async def create_namespace(project_item: ProjectSchema):
    client_corev1api_region = clusters[project_item.region]["Client-CoreV1Api"]
    body = client.V1Namespace(
        metadata=client.V1ObjectMeta(
            name=project_item.name))

    rq_spec = {
        "limits.cpu": str(project_item.max_project_cpu),
        "limits.memory": str(project_item.max_project_mem)+"Mi"
    }
    rq = client.V1ResourceQuota(
        metadata=client.V1ObjectMeta(name="resource-quota-for-"+project_item.name),
        spec=client.V1ResourceQuotaSpec(hard=rq_spec))

    lr_default = {
        "cpu": str(project_item.default_limit_pod_cpu),
        "memory": str(project_item.default_limit_pod_mem)+"Mi"
    }
    lr = client.V1LimitRange(
        metadata=client.V1ObjectMeta(name="limit-range-for-"+project_item.name),
        spec=client.V1LimitRangeSpec(limits=[client.V1LimitRangeItem(default=lr_default, type="Container")]))

    try:
        client_corev1api_region.create_namespace(body=body)
        client_corev1api_region.create_namespaced_resource_quota(body=rq, namespace=project_item.name)
        client_corev1api_region.create_namespaced_limit_range(body=lr, namespace=project_item.name)
    except ApiException as e:
        print("Exception when trying to create namespace: %s\n" % e)
    return project_item


async def update_namespace(project_item: ProjectSchema):
    client_corev1api_region = clusters[project_item.region]["Client-CoreV1Api"]

    rq_spec = {
        "limits.cpu": str(project_item.max_project_cpu),
        "limits.memory": str(project_item.max_project_mem)+"Mi"
    }
    rq = client.V1ResourceQuota(spec=client.V1ResourceQuotaSpec(hard=rq_spec))

    lr_default = {
        "cpu": str(project_item.default_limit_pod_cpu),
        "memory": str(project_item.default_limit_pod_mem)+"Mi"
    }
    lr = client.V1LimitRange(spec=client.V1LimitRangeSpec(limits=[client.V1LimitRangeItem(default=lr_default, type="Container")]))

    try:
        client_corev1api_region.patch_namespaced_resource_quota(body=rq, name="resource-quota-for-"+project_item.name, namespace=project_item.name)
        client_corev1api_region.patch_namespaced_limit_range(body=lr, name="limit-range-for-"+project_item.name, namespace=project_item.name)
    except ApiException as e:
        print("Exception when trying to update resource quote of namespace: %s\n" % e)
    return project_item


async def delete_namespace(project_item: ProjectPrimaryKey):
    client_corev1api_region = clusters[project_item.region]["Client-CoreV1Api"]

    delete_body = client.V1DeleteOptions()

    try:
        client_corev1api_region.delete_namespace(body=delete_body, name=project_item.name)
    except ApiException as e:
        print("Exception when trying to update resource quote of namespace: %s\n" % e)
    return project_item