import logging
from functools import partial
from pprint import pprint, pformat
from typing import Dict, Tuple, List

from attr import dataclass
from kubernetes import client
from kubernetes.client import V1Deployment, V1Pod

logger = logging.getLogger(__name__)

IGNORE_ANNOTATION = "growse.com/k8s-version-checker-ignore"
VERSION_PATTERN_ANNOTATION = "growse.com/k8s-version-checker-tag-regex"


@dataclass(frozen=True)
class Resource:
    kind: str
    name: str
    uid: str
    tag_version_pattern_annotation: str
    image_spec: Tuple[str]


@dataclass(frozen=True)
class Container:
    server: str
    image: str
    image_id: str


def get_container_from_status(node_name: str, container_status) -> Container:
    return Container(node_name, container_status.image, container_status.image_id)


def get_top_level_resources(namespace: str) -> Dict[Resource, Container]:
    get_top_level_deployments(namespace)
    return get_top_level_pods(namespace)


def top_level_not_ignored_resource(item) -> bool:
    return not item.metadata.owner_references and not item.metadata.annotations.get(IGNORE_ANNOTATION, False)


def get_pods_for_deployment(deployment: V1Deployment, namespace) -> List[V1Pod]:
    get_deployment_fn, get_pod_fun, get_replica_set_fn = get_api_functions(namespace)
    replica_set_labels = deployment.spec.template.metadata.labels

    replica_set_label_selector = get_label_selector_from_dict(replica_set_labels)
    replica_sets = get_replica_set_fn(label_selector=replica_set_label_selector)
    pod_label_specs = map(lambda item: item.spec.template.metadata.labels, replica_sets.items)

    return list(
        map(lambda pod_label: get_pod_fun(label_selector=get_label_selector_from_dict(pod_label)), pod_label_specs))


def get_top_level_deployments(namespace: str) -> Dict[Resource, Container]:
    get_deployment_fn, get_pod_fun, get_replica_set_fn = get_api_functions(namespace)

    k8s_deployment_response = get_deployment_fn()
    get_replica_set_fn()
    get_pod_fun()
    top_level_not_ignored_deployments = list(filter(top_level_not_ignored_resource, k8s_deployment_response.items))

    top_level_deployments = {
        Resource("Deployment", deployment.metadata.name, deployment.metadata.uid,
                 deployment.metadata.annotations.get(VERSION_PATTERN_ANNOTATION, ""),
                 ()): get_pods_for_deployment(deployment, namespace)
        for deployment in top_level_not_ignored_deployments
    }
    pprint(top_level_deployments)


def get_api_functions(namespace: str = None) -> Tuple[partial, partial, partial]:
    v1apps = client.AppsV1Api()
    v1core = client.CoreV1Api()
    if namespace:
        get_replica_set_fn = partial(v1apps.list_namespaced_replica_set, namespace, watch=False)
        get_pod_fun = partial(v1core.list_namespaced_pod, namespace, watch=False)
        get_deployment_fn = partial(v1apps.list_namespaced_deployment, namespace, watch=False)

    else:
        get_replica_set_fn = partial(v1apps.list_replica_set_for_all_namespaces, watch=False)
        get_pod_fun = partial(v1core.list_pod_for_all_namespaces, watch=False)
        get_deployment_fn = partial(v1apps.list_deployment_for_all_namespaces, watch=False)
    return get_deployment_fn, get_pod_fun, get_replica_set_fn


def get_label_selector_from_dict(labels):
    return ",".join(["{k}={v}".format(k=key, v=val) for key, val in labels.items()])


def get_top_level_pods(namespace: str) -> Dict[Resource, Container]:
    v1core = client.CoreV1Api()
    if namespace:
        k8s_pod_response = v1core.list_namespaced_pod(namespace, watch=False)
    else:
        k8s_pod_response = v1core.list_pod_for_all_namespaces(watch=False)

    top_level_not_ignored_pods = filter(top_level_not_ignored_resource, k8s_pod_response.items)
    top_level_pods = {
        Resource("Pod", item.metadata.name, item.metadata.uid,
                 item.metadata.annotations.get(VERSION_PATTERN_ANNOTATION, ""),
                 tuple(map(lambda c: str(c.image), item.spec.containers))): list(
            map(partial(get_container_from_status, item.spec.node_name),
                item.status.container_statuses))
        for item in top_level_not_ignored_pods
    }
    logger.debug(pformat(top_level_pods))
    return top_level_pods
