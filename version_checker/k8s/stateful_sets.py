from functools import partial
from typing import Dict, List

from kubernetes.client import V1StatefulSet, V1Pod

from version_checker.k8s import (
    top_level_not_ignored_resource,
    VERSION_PATTERN_ANNOTATION,
    get_container_from_status,
    get_label_selector_from_dict,
)
from version_checker.k8s.model import Resource, Container, K8sFetcherFunctions


def get_top_level_stateful_sets(
    k8s_fetcher_functions: K8sFetcherFunctions
) -> Dict[Resource, Container]:

    k8s_stateful_set_response = k8s_fetcher_functions.get_stateful_set_fn()
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
            for pod in get_pods_for_stateful_set(
                stateful_set, k8s_fetcher_functions.get_pods_fn
            )
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
