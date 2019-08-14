import logging
from pprint import pformat
from typing import Dict

from version_checker.k8s import (
    Container,
    top_level_not_ignored_resource,
    VERSION_PATTERN_ANNOTATION,
    get_container_from_status,
    get_api_functions,
)
from version_checker.k8s.model import Resource

logger = logging.getLogger(__name__)


def get_top_level_pods(namespace: str) -> Dict[Resource, Container]:
    get_deployment_fn, get_pod_fn, get_replica_set_fn, get_stateful_set_fn, get_daemon_set_fn = get_api_functions(
        namespace
    )
    k8s_pod_response = get_pod_fn()
    top_level_not_ignored_pods = [
        pod for pod in k8s_pod_response.items if top_level_not_ignored_resource(pod)
    ]

    top_level_pods = {
        Resource(
            kind="Pod",
            name=pod.metadata.name,
            uid=pod.metadata.uid,
            tag_version_pattern_annotation=pod.metadata.annotations.get(
                VERSION_PATTERN_ANNOTATION, ""
            ),
            image_spec=frozenset({c.image for c in pod.spec.containers}),
        ): [
            get_container_from_status(pod.spec.node_name, container)
            for container in pod.status.container_statuses
        ]
        for pod in top_level_not_ignored_pods
    }
    logger.debug(pformat(top_level_pods))
    return top_level_pods
