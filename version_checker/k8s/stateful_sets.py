from functools import partial
from typing import Dict, List

from kubernetes.client import V1StatefulSet, V1Pod

from version_checker.k8s import (
    get_api_functions,
    top_level_not_ignored_resource,
    VERSION_PATTERN_ANNOTATION,
    get_container_from_status,
    get_label_selector_from_dict,
)
from version_checker.k8s.model import Resource, Container


def get_top_level_stateful_sets(namespace: str) -> Dict[Resource, Container]:
    get_deployment_fn, get_pod_fn, get_replica_set_fn, get_stateful_set_fn, get_daemon_set_fn = get_api_functions(
        namespace
    )

    k8s_stateful_set_response = get_stateful_set_fn()
    top_level_not_ignored_stateful_sets = [
        stateful_set
        for stateful_set in k8s_stateful_set_response.items
        if top_level_not_ignored_resource(stateful_set)
    ]

    top_level_stateful_sets = {
        Resource(
            kind="StatefulSet",
            name=stateful_set.metadata.name,
            uid=stateful_set.metadata.uid,
            tag_version_pattern_annotation=stateful_set.metadata.annotations.get(
                VERSION_PATTERN_ANNOTATION, ""
            ),
            image_spec=frozenset(
                {
                    str(container_spec.image)
                    for container_spec in stateful_set.spec.template.spec.containers
                }
            ),
        ): [
            get_container_from_status(pod.spec.node_name, container)
            for pod in get_pods_for_stateful_set(stateful_set, get_pod_fn)
            for container in pod.status.container_statuses
        ]
        for stateful_set in top_level_not_ignored_stateful_sets
    }

    return top_level_stateful_sets


def get_pods_for_stateful_set(
    stateful_set: V1StatefulSet, get_pods_fn: partial
) -> List[V1Pod]:

    pod_label_specs = stateful_set.spec.template.metadata.labels

    return [
        pod
        for pod in get_pods_fn(
            label_selector=get_label_selector_from_dict(pod_label_specs)
        ).items
    ]
