import logging
from itertools import groupby, chain
from pprint import pprint

from attr import dataclass
from kubernetes import client
from kubernetes.client import V1ReplicaSetList, V1DeploymentList, V1StatefulSetList, V1DaemonSetList

from version_checker.registry import is_docker_hub_image

logger = logging.getLogger(__name__)

IGNORE_ANNOTATION = "growse.com/k8s-version-checker-ignore"
VERSION_PATTERN_ANNOTATION = "growse.com/k8s-version-checker-tag-regex"


@dataclass(frozen=True)
class Owner:
    kind: str
    name: str
    uid: str


@dataclass(frozen=True)
class Pod:
    server: str
    image: str
    owners: list
    image_id: str
    tag_version_pattern_annotation: str


def get_images_from_running_pods(namespace: str) -> dict:
    v1core = client.CoreV1Api()
    if namespace:
        k8s_pod_response = v1core.list_namespaced_pod(namespace, watch=False)
    else:
        k8s_pod_response = v1core.list_pod_for_all_namespaces(watch=False)

    v1apps = client.AppsV1Api()
    replica_sets = v1apps.list_replica_set_for_all_namespaces()
    deployments = v1apps.list_deployment_for_all_namespaces()
    statefulsets = v1apps.list_stateful_set_for_all_namespaces()
    daemonsets = v1apps.list_daemon_set_for_all_namespaces()
    pods = [
        Pod(item.spec.node_name,
            status.image,
            find_top_owners(flatten_list(item.metadata.owner_references),
                            replica_sets, deployments, statefulsets, daemonsets),
            status.image_id,
            item.metadata.annotations.get(VERSION_PATTERN_ANNOTATION, "")
            )
        for item in filter(is_not_ignored_pod, k8s_pod_response.items) for status in
        filter(is_docker_hub_image, item.status.container_statuses)
    ]
    sorted_pods = sorted(pods, key=get_pod_image)
    grouped_pods = {k: list(v) for k, v in groupby(sorted_pods, get_pod_image)}
    return grouped_pods


def is_not_ignored_pod(item) -> bool:
    return not (IGNORE_ANNOTATION in item.metadata.annotations and item.metadata.annotations[
        IGNORE_ANNOTATION] == 'true')


def find_top_owners(things: list, replica_sets: V1ReplicaSetList, deployments: V1DeploymentList,
                    stateful_sets: V1StatefulSetList, daemon_sets: V1DaemonSetList) -> list:
    """
    Walks the k8s resources to find the ultimate list of owners of a list of things
    :param things:
    :param replica_sets:
    :param deployments:
    :param stateful_sets:
    :param daemon_sets:
    :return:
    """
    logger.debug("Looking for owners for {things}".format(things=things))
    for idx in range(len(things)):
        thing = things[idx]
        items_to_lookup = None
        if thing.kind == "ReplicaSet":
            items_to_lookup = replica_sets.items
        elif thing.kind == "Deployment":
            items_to_lookup = deployments.items
        elif thing.kind == "StatefulSet":
            items_to_lookup = stateful_sets.items
        elif thing.kind == "DaemonSet":
            items_to_lookup = daemon_sets.items
        else:
            logger.error("Cannot find the owner for {thing}".format(thing=thing))
        if items_to_lookup:
            owners = next(filter(lambda r: r.metadata.uid == thing.uid, items_to_lookup)).metadata.owner_references
            logger.debug("{thing} has owners {owners}".format(thing=thing, owners=owners))
            if owners:
                things[idx] = find_top_owners(owners, replica_sets, deployments, stateful_sets, daemon_sets)
                logger.debug("have replaced {thing} with {things}".format(thing=thing, things=things[idx]))
    ret = []
    for thing in things:
        if isinstance(thing, list):
            ret.extend(thing)
        else:
            ret.append(thing)
    return list(map(lambda k8sowner: Owner(k8sowner.kind, k8sowner.name, k8sowner.uid), ret))


def get_pod_image(pod: Pod) -> str:
    return pod.image


def flatten_list(input_list: list) -> list:
    if all(isinstance(elem, list) for elem in input_list):
        return list(chain.from_iterable(input_list))
    else:
        return input_list
