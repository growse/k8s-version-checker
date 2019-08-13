from functools import partial
from typing import Tuple, Dict

from kubernetes import client

from version_checker.k8s.model import Container

IGNORE_ANNOTATION = "growse.com/k8s-version-checker-ignore"
VERSION_PATTERN_ANNOTATION = "growse.com/k8s-version-checker-tag-regex"


def get_label_selector_from_dict(labels: Dict[str, str]) -> str:
    return ",".join(["{k}={v}".format(k=key, v=val) for key, val in labels.items()])


def get_api_functions(namespace: str = None) -> Tuple[partial, partial, partial]:
    v1apps = client.AppsV1Api()
    v1core = client.CoreV1Api()
    if namespace:
        get_replica_set_fn = partial(
            v1apps.list_namespaced_replica_set, namespace, watch=False
        )
        get_pod_fun = partial(v1core.list_namespaced_pod, namespace, watch=False)
        get_deployment_fn = partial(
            v1apps.list_namespaced_deployment, namespace, watch=False
        )

    else:
        get_replica_set_fn = partial(
            v1apps.list_replica_set_for_all_namespaces, watch=False
        )
        get_pod_fun = partial(v1core.list_pod_for_all_namespaces, watch=False)
        get_deployment_fn = partial(
            v1apps.list_deployment_for_all_namespaces, watch=False
        )
    return get_deployment_fn, get_pod_fun, get_replica_set_fn


def get_container_from_status(node_name: str, container_status) -> Container:
    return Container(node_name, container_status.image, container_status.image_id)


def top_level_not_ignored_resource(item) -> bool:
    return not item.metadata.owner_references and not item.metadata.annotations.get(
        IGNORE_ANNOTATION, False
    )
