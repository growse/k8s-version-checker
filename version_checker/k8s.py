import logging
from functools import partial
from pprint import pprint, pformat
from typing import Dict, Tuple

from attr import dataclass
from kubernetes import client

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
    v1core = client.CoreV1Api()
    if namespace:
        k8s_pod_response = v1core.list_namespaced_pod(namespace, watch=False)
    else:
        k8s_pod_response = v1core.list_pod_for_all_namespaces(watch=False)

    top_level_not_ignored_pods = filter(
        lambda item: not item.metadata.owner_references and not item.metadata.annotations.get(IGNORE_ANNOTATION, False)
        , k8s_pod_response.items)
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
