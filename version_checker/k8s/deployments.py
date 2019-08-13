from functools import partial
from typing import Dict, List

from kubernetes.client import V1Deployment, V1Pod

from version_checker.k8s import (
    top_level_not_ignored_resource,
    get_api_functions,
    get_container_from_status,
    VERSION_PATTERN_ANNOTATION,
    get_label_selector_from_dict,
)
from version_checker.k8s.model import Resource, Container


def get_top_level_deployments(namespace: str) -> Dict[Resource, Container]:
    get_deployment_fn, get_pod_fun, get_replica_set_fn = get_api_functions(namespace)

    k8s_deployment_response = get_deployment_fn()
    top_level_not_ignored_deployments = [
        deployment
        for deployment in k8s_deployment_response.items
        if top_level_not_ignored_resource(deployment)
    ]

    top_level_deployments = {
        Resource(
            kind="Deployment",
            name=deployment.metadata.name,
            uid=deployment.metadata.uid,
            tag_version_pattern_annotation=deployment.metadata.annotations.get(
                VERSION_PATTERN_ANNOTATION, ""
            ),
            image_spec=frozenset(
                {
                    str(container_spec.image)
                    for container_spec in deployment.spec.template.spec.containers
                }
            ),
        ): [
            get_container_from_status(pod.spec.node_name, container)
            for pod in get_pods_for_deployment(
                deployment, get_replica_set_fn, get_pod_fun
            )
            for container in pod.status.container_statuses
        ]
        for deployment in top_level_not_ignored_deployments
    }

    return top_level_deployments


def get_pods_for_deployment(
    deployment: V1Deployment, get_replica_sets: partial, get_pods: partial
) -> List[V1Pod]:
    replica_set_labels = deployment.spec.template.metadata.labels

    replica_set_label_selector = get_label_selector_from_dict(replica_set_labels)
    replica_sets = get_replica_sets(label_selector=replica_set_label_selector)
    pod_label_specs: List[Dict[str, str]] = [
        item.spec.template.metadata.labels for item in replica_sets.items
    ]
    return [
        pod
        for labels in pod_label_specs
        for pod in get_pods(label_selector=get_label_selector_from_dict(labels)).items
    ]
