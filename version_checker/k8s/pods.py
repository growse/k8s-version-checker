import logging
from pprint import pformat
from typing import Dict

from version_checker.k8s import (
    Container,
    top_level_not_ignored_resource,
    VERSION_PATTERN_ANNOTATION,
    get_container_from_status,
)
from version_checker.k8s.model import Resource, K8sFetcherFunctions

logger = logging.getLogger(__name__)


def get_top_level_pods(
    k8s_fetcher_functions: K8sFetcherFunctions
) -> Dict[Resource, Container]:

    k8s_pod_response = k8s_fetcher_functions.get_pods_fn()
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
