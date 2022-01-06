import os
import json
import yaml
from kubernetes import client, config



clusters = {}


def setup_client():
    output = {}
    with open("config.yaml", "w") as text_file:
        text_file.write(str(os.environ['CONFIG_FILE']))
    with open("config.yaml", 'r') as stream:
        cluster_info = yaml.safe_load(stream)
    cluster_info = cluster_info["clusters"]

    contexts, _ = config.list_kube_config_contexts("config.yaml")
    cluster_dict = json.loads(os.environ['CLUSTER_DICT'])
    for key in cluster_dict.keys():
        config.load_kube_config("config.yaml", context=cluster_dict[key]["Config-Name"])
        cluster_item = cluster_dict[key].copy()
        client_value = client.CoreV1Api()
        cluster_item.update({"Client-CoreV1Api": client_value})
        client_value = client.RbacAuthorizationV1Api()
        cluster_item.update({"Client-RbacAuthorizationV1Api": client_value})
        client_value = client.CertificatesV1Api()
        cluster_item.update({"Client-CertificatesV1Api": client_value})

        for item in cluster_info:
            if item["name"] == cluster_dict[key]["Config-Name"]:
                cluster_item.update({"ca_cluster": item["cluster"]["certificate-authority-data"]})
                cluster_item.update({"server_endpoint": item["cluster"]["server"]})

        output[key] = cluster_item
    return output

clusters = setup_client()