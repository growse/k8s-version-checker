import logging
from functools import partial
from pprint import pformat
from typing import Dict

from kubernetes import client

from version_checker.k8s import (
    Container,
    top_level_not_ignored_resource,
    VERSION_PATTERN_ANNOTATION,
    get_container_from_status,
)
from version_checker.k8s.model import Resource

logger = logging.getLogger(__name__)


def get_top_level_pods(namespace: str) -> Dict[Resource, Container]:
    v1core = client.CoreV1Api()
    if namespace:
        k8s_pod_response = v1core.list_namespaced_pod(namespace, watch=False)
    else:
        k8s_pod_response = v1core.list_pod_for_all_namespaces(watch=False)

    top_level_not_ignored_pods = [
        pod for pod in k8s_pod_response.items if top_level_not_ignored_resource(pod)
    ]

    top_level_pods = {
        Resource(
            "Pod",
            item.metadata.name,
            item.metadata.uid,
            item.metadata.annotations.get(VERSION_PATTERN_ANNOTATION, ""),
            tuple(map(lambda c: str(c.image), item.spec.containers)),
        ): list(
            map(
                partial(get_container_from_status, item.spec.node_name),
                item.status.container_statuses,
            )
        )
        for item in top_level_not_ignored_pods
    }
    logger.debug(pformat(top_level_pods))
    return top_level_pods
