import logging
import re
from typing import Optional, List, Dict

import click
import coloredlogs
from kubernetes import config
from packaging.version import parse

from version_checker.k8s.deployments import get_top_level_deployments
from version_checker.k8s.model import Resource, Container
from version_checker.notification import (
    NewTagNotification,
    log_notifications,
    Notification,
    OutOfDateContainerNotification,
)
from version_checker.registry import (
    is_versioned_tag,
    get_newest_tag,
    get_docker_tag_digest,
    get_digest_from_image_status,
)

logger = logging.getLogger(__name__)


@click.command(
    "K8S pod image version checker",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging")
@click.option("--image-pattern", help="Only look at images matching this pattern")
@click.option("--namespace", help="Only look in this namespace")
def main(debug: bool, image_pattern: str, namespace: str) -> None:
    """
    Checks a kubernetes cluster to see if any running pods, cron jobs or deployments have updated image tags or image
    digests on their repositories.

    Can be run either external to a cluster (requires `~/.kube/config` to be setup correctly) or within a cluster as
    a pod. In the latter case, notifications about available updates will be posted to a webhook.

    This script can be figured using annotations on the pods themselves. Pods can be ignored with:

    `growse.com/version-checker-ignore: "true"`

    And can have their elgiable tags scroped with a regular expression:

    `growse.com/version-checker-tag-regex: "^v.+?-amd64$"
    """
    if debug:
        coloredlogs.set_level("DEBUG")
    try:
        config.load_incluster_config()
    except config.config_exception.ConfigException:
        config.load_kube_config()

    images = get_top_level_resources(namespace)

    notifications = []

    for resource, containers in sorted(images.items()):
        logger.info(
            "Considering {kind}: {name}".format(kind=resource.kind, name=resource.name)
        )
        notifications.extend(check_resouce_for_new_image_tags(resource, image_pattern))
        notifications.extend(
            check_resource_containers_for_updated_image_digests(resource, containers)
        )

    log_notifications(notifications)


def get_top_level_resources(namespace: str) -> Dict[Resource, Container]:
    return get_top_level_deployments(namespace)
    # return get_top_level_pods(namespace)


def check_resource_containers_for_updated_image_digests(
    resource: Resource, containers: List[Container]
) -> List[Notification]:
    notifications = []

    if len(containers) == 0:
        return notifications

    for container in containers:
        logger.info(
            "Container spec'd with is {image} running {image_id}".format(
                image=container.image, image_id=container.image_id
            )
        )
        image_name, tag = container.image.split(":", 1)
        registry_digest = get_docker_tag_digest(image_name, tag)
        if not registry_digest:
            logger.warning(
                "No registry digest found for {image}:{tag}".format(
                    image=image_name, tag=tag
                )
            )
            continue
        logger.info(
            "Digest on registry for this image: {digest}".format(digest=registry_digest)
        )
        if registry_digest != get_digest_from_image_status(container.image_id):
            notifications.append(
                OutOfDateContainerNotification(resource, container, registry_digest)
            )
    return notifications


def check_resouce_for_new_image_tags(
    resource: Resource, image_pattern_to_match: Optional[str]
) -> List[Notification]:
    notifications = []
    for image in resource.image_spec:
        logger.info(
            "{kind} has image defined: {image}".format(kind=resource.kind, image=image)
        )
        image_name, tag = image.split(":", 1)
        if image_pattern_to_match and not re.match(image_pattern_to_match, image_name):
            continue
        if is_versioned_tag(tag):
            newest_tag = get_newest_tag(image_name)
            if newest_tag:
                logger.info("Newest tag for this image is {tag}".format(tag=newest_tag))
                if newest_tag != "" and newest_tag > parse(tag):
                    notifications.append(
                        NewTagNotification(image_name, tag, newest_tag)
                    )
            else:
                logger.warning(
                    "No eligable tags found for {image}".format(image=image_name)
                )
    return notifications


def setup_logging(debug: bool) -> None:
    level = "DEBUG" if debug else "INFO"


coloredlogs.install(milliseconds=True, level="INFO")
main(prog_name="version-checker")
