import logging
import re

import click
import coloredlogs
from kubernetes import config
from packaging.version import parse

from version_checker.k8s import get_images_from_running_pods
from version_checker.notification import NewTagNotification, log_notifications, OutOfDatePodNotification
from version_checker.registry import is_versioned_tag, get_newest_tag, get_docker_tag_digest


def get_digest_from_image_status(image_status: str) -> str:
    if not ("@" in image_status and image_status.startswith("docker-pullable://")):
        raise Exception("Given image status is not a valid status: {status}".format(status=image_status))
    return image_status.split("@", 1)[1]


@click.command("K8S pod image version checker", context_settings=dict(help_option_names=["-h", "--help"]))
@click.option('--debug', is_flag=True, default=False, help='Enable debug logging')
@click.option('--image-pattern', help='Only look at images matching this pattern')
@click.option('--namespace', help='Only look in this namespace')
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
    setup_logging(debug)
    try:
        config.load_incluster_config()
    except config.config_exception.ConfigException:
        config.load_kube_config()

    images = get_images_from_running_pods(namespace)

    notifications = []

    for image, pods in sorted(images.items()):
        image_name, tag = image.split(":", 1)
        if image_pattern and not re.match(image_pattern, image_name):
            continue
        logger.info("Considering: {image}:{tag}".format(image=image_name, tag=tag))

        if is_versioned_tag(tag):
            newest_tag = get_newest_tag(image_name)
            logger.info("Newest tag for this image is {tag}".format(tag=newest_tag))
            if newest_tag != "" and newest_tag > parse(tag):
                notifications.append(NewTagNotification(image_name, tag, newest_tag))
        if len(pods) == 0:
            continue

        registry_digest = get_docker_tag_digest(image_name, tag)
        if not registry_digest:
            logger.warning("No registry digest found for {image}:{tag}".format(image=image_name, tag=tag))
            continue
        logger.info("Digest on registry for this image: {digest}".format(digest=registry_digest))
        logger.debug("Pod digests: {digests}".format(digests=list(map(lambda pod: pod.image_id, pods))))
        out_of_date_pods = filter(lambda p: get_digest_from_image_status(p.image_id) != registry_digest, pods)

        for pod in out_of_date_pods:
            notifications.append(OutOfDatePodNotification(pod, registry_digest))

    log_notifications(notifications)


def setup_logging(debug: bool) -> None:
    level = 'DEBUG' if debug else 'INFO'
    coloredlogs.install(level=level, logger=logger)


logger = logging.getLogger(__name__)
logging.basicConfig()
main(prog_name="version-checker")
