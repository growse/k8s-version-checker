from functools import partial
from typing import Dict, List

from kubernetes.client import V1Pod, V1StatefulSet, V1DaemonSet

from version_checker.k8s import (
    get_api_functions,
    top_level_not_ignored_resource,
    VERSION_PATTERN_ANNOTATION,
    get_container_from_status,
    get_label_selector_from_dict,
)
from version_checker.k8s.model import Resource, Container, K8sFetcherFunctions


def get_top_level_daemon_sets(
    k8s_fetcher_functions: K8sFetcherFunctions
) -> Dict[Resource, Container]:
    k8s_daemon_set_response = k8s_fetcher_functions.get_daemon_set_fn()
    top_level_not_ignored_daemon_set = [
        daemon_set
        for daemon_set in k8s_daemon_set_response.items
        if top_level_not_ignored_resource(daemon_set)
    ]
    return {
        Resource(
            kind="Daemon Set",
            name=daemon_set.metadata.name,
            uid=daemon_set.metadata.uid,
            tag_version_pattern_annotation=daemon_set.metadata.annotations.get(
                VERSION_PATTERN_ANNOTATION, ""
            ),
            image_spec=frozenset(
                {
                    str(container_spec.image)
                    for container_spec in daemon_set.spec.template.spec.containers
                }
            ),
        ): [
            get_container_from_status(pod.spec.node_name, container)
            for pod in get_pods_for_daemon_set(
                daemon_set, k8s_fetcher_functions.get_pods_fn
            )
            for container in pod.status.container_statuses
        ]
        for daemon_set in top_level_not_ignored_daemon_set
    }


def get_pods_for_daemon_set(
    daemon_set: V1DaemonSet, get_pods_fn: partial
) -> List[V1Pod]:
    pod_label_specs = daemon_set.spec.template.metadata.labels

    return [
        pod
        for pod in get_pods_fn(
            label_selector=get_label_selector_from_dict(pod_label_specs)
        ).items
    ]
