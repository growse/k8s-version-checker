import functools
import logging
import re
from typing import Tuple, Optional

import requests
from packaging.version import Version, parse
from requests import Response

logger = logging.getLogger(__name__)

# List of hosts that return the correct docker digest even on schema v1
digest_correct_hosts = ["quay.io"]


def get_newest_tag(image_name: str, match_pattern: str = "") -> Optional[str]:
    registry_tags = get_docker_registry_tags(image_name)
    logger.debug("Available registry tags: {tags}".format(tags=registry_tags))
    if match_pattern:
        logger.info(
            "Only matching tags against {pattern}".format(pattern=match_pattern)
        )
    mapped_tags = sorted(
        [
            parse(tag)
            for tag in registry_tags
            if isinstance(parse(tag), Version) and re.match(match_pattern, tag)
        ],
        reverse=True,
    )
    logger.debug("Filtered version tags: {tags}".format(tags=list(mapped_tags)))
    if len(mapped_tags) > 0:
        newest_tag = mapped_tags[0]
        return newest_tag
    return None


def docker_registry_api_get(url: str, headers=None) -> Response:
    if headers is None:
        headers = {}
    logger.debug("Fetching {url}".format(url=url))
    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        authenticate_header = response.headers["WWW-Authenticate"]
        if not authenticate_header.startswith("Bearer "):
            raise Exception("Invalid authentication header in registry response")
        header_dictionary = dict(
            part.split("=", 1)
            for part in authenticate_header[len("Bearer ") :].strip().split(",")
        )

        token = docker_registry_auth(
            header_dictionary["realm"].strip('"'),
            header_dictionary["service"].strip('"'),
            header_dictionary["scope"].strip('"'),
        )
        response = requests.get(
            url,
            headers={
                "authorization": "Bearer {token}".format(token=token),
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            },
        )
    return response


def get_registry_host_and_image(image: str) -> Tuple[str, str]:
    host = "registry-1.docker.io"
    image_name = image
    if image.count("/") == 0:
        image_name = "library/{image}".format(image=image)
    elif image.count("/") == 2:
        host, image_name = image.split("/", 1)
    elif image.count("/") == 1 and "." in image.split("/", 1)[0]:
        host, image_name = image.split("/", 1)
    elif image.count("/") > 2:
        raise Exception("Illegal docker image name: {image}".format(image=image))

    return host, image_name


def get_docker_registry_tags(image: str) -> dict:
    host, image_name = get_registry_host_and_image(image)
    response = docker_registry_api_get(
        "https://{host}/v2/{image}/tags/list".format(host=host, image=image_name)
    )
    if "tags" not in response.json():
        raise Exception("Registry response did not contain tags structure")
    return response.json()["tags"]


@functools.lru_cache()
def get_docker_tag_digest(image: str, tag: str) -> str:
    host, image_name = get_registry_host_and_image(image)
    response = docker_registry_api_get(
        "https://{host}/v2/{image}/manifests/{tag}".format(
            host=host, image=image_name, tag=tag
        )
    )
    logger.debug(response.json())
    if response.status_code != 200:
        raise Exception(
            "Registry response did not contain manifest: {response}".format(
                response=response.text
            )
        )
    if host in digest_correct_hosts or response.json()["schemaVersion"] == 2:
        return response.headers["Docker-Content-Digest"]
    else:
        return ""


def docker_registry_auth(realm: str, service: str, scope: str) -> str:
    client_id = "growse/k8s-version-checker"
    response = requests.get(
        realm, params={"service": service, "scope": scope, "client_id": client_id}
    )
    if response.status_code != 200:
        raise Exception(
            "Error received from token service: {response}".format(response=response)
        )
    return response.json()["token"]


def is_versioned_tag(tag: str) -> bool:
    return isinstance(parse(tag), Version)


def get_digest_from_image_status(image_status: str) -> str:
    if not ("@" in image_status and image_status.startswith("docker-pullable://")):
        raise Exception(
            "Given image status is not a valid status: {status}".format(
                status=image_status
            )
        )
    return image_status.split("@", 1)[1]
