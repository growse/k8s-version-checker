#!/usr/bin/env python3
import functools
import logging
import re

import coloredlogs
import packaging
import requests
from kubernetes import client, config
from packaging.version import parse, LegacyVersion, Version

from requests import Response

logger = logging.getLogger(__name__)


def main():
    # it works only if this script is run by K8s as a POD
    try:
        config.load_incluster_config()
    except config.config_exception.ConfigException:
        config.load_kube_config()

    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    pods = {(item.spec.node_name, status.image): {item.spec.node_name: status.image_id} for item in ret.items for status
            in filter(is_docker_hub_image, item.status.container_statuses)}

    for pod in pods:
        image_name, tag = pod[1].split(":", 1)
        registry_digest = get_docker_tag_digest(image_name, tag)
        registry_tags = get_docker_registry_tags(image_name)
        logger.info("Deployed Image: {image}:{tag}".format(image=image_name, tag=tag, server=pod[0]))
        if is_versioned_tag(tag):
            logger.debug("Available registry tags: {tags}".format(tags=registry_tags))
            mapped_tags = sorted(filter(lambda x: isinstance(x, Version), map(parse, registry_tags)), reverse=True)
            logger.debug("Filtered version tags: {tags}".format(tags=list(mapped_tags)))
            if len(list(mapped_tags)) > 0:
                newest_tag = list(mapped_tags)[0]
                logger.debug("Newest tag is {tag}".format(tag=newest_tag))
                if newest_tag > parse(tag):
                    logger.warning("Newer tag available for {image}:{tag}: {new_tag}".format(image=image_name, tag=tag,
                                                                                             new_tag=str(newest_tag)))

        logger.info("Digest on registry for this image: {digest}".format(digest=registry_digest))
        for deployed_server in pods[pod]:
            deployed_digest = pods[pod][deployed_server].split("@", 1)[1]
            logger.info("Version on {server} is {digest}".format(server=deployed_server, digest=deployed_digest))
            if deployed_digest != registry_digest:
                logger.warning(
                    "Updated image digest exists for {image}:{tag} running on {server}".format(image=image_name,
                                                                                               tag=tag,
                                                                                               server=deployed_server))
        break


def is_docker_hub_image(status) -> bool:
    image_id = status.image_id
    return "." not in image_id.split("@", 1)[0].split("/")[-2]


def docker_registry_api_get(url: str) -> Response:
    logger.debug("Fetching {}".format(url))
    response = requests.get(url)
    if response.status_code == 401:
        authenticate_header = response.headers["WWW-Authenticate"]
        if not authenticate_header.startswith("Bearer "):
            raise Exception("Invalid authentication header in registry response")
        header_dictionary = dict(part.split("=", 1) for part in authenticate_header[len("Bearer "):].strip().split(","))

        token = docker_auth(header_dictionary["realm"].strip("\""), header_dictionary["service"].strip("\""),
                            header_dictionary["scope"].strip("\""))
        response = requests.get(url, headers={'authorization': "Bearer {}".format(token)})
    return response


@functools.lru_cache(maxsize=100, typed=False)
def get_docker_registry_tags(image: str) -> dict:
    response = docker_registry_api_get("https://registry-1.docker.io/v2/{}/tags/list".format(image))
    if "tags" not in response.json():
        raise Exception("Registry response did not contain tags structure")
    return response.json()["tags"]


@functools.lru_cache(maxsize=100, typed=False)
def get_docker_tag_digest(image: str, tag: str) -> str:
    response = docker_registry_api_get(
        "https://registry-1.docker.io/v2/{image}/manifests/{tag}".format(image=image, tag=tag))
    if response.status_code != 200:
        raise Exception("Registry response did not contain manifest: {}".format(response.text))
    return response.headers["Docker-Content-Digest"]


tag_version_regex = re.compile("v?(\\d+)")


def is_versioned_tag(tag: str) -> bool:
    return isinstance(parse(tag), Version)


def docker_auth(realm: str, service: str, scope: str) -> str:
    client_id = "k8s-version-checker"
    response = requests.get(realm, params={"service": service, "scope": scope, "client_id": client_id})
    if response.status_code != 200:
        raise Exception("Error received from token service: {}".format(response))
    return response.json()["token"]


if __name__ == '__main__':
    # Create a logger object.

    # By default the install() function installs a handler on the root logger,
    # this means that log messages from your code and log messages from the
    # libraries that you use will all show up on the terminal.
    coloredlogs.install(level='DEBUG', logger=logger)
    try:
        main()
    except Exception:
        logger.exception("Caught exception")
