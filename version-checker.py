#!/usr/bin/env python3
import coloredlogs
from kubernetes import client, config
import pprint
import requests
import functools
import logging

logger = logging.getLogger(__name__)


def is_docker_hub_image(status) -> bool:
    image_id = status.image_id
    return "." not in image_id.split("@", 1)[0].split("/")[-2]


@functools.lru_cache(maxsize=100, typed=False)
def get_docker_registry_tags(image: str) -> dict:
    response = requests.get("https://registry-1.docker.io/v2/{}/tags/list".format(image))
    if response.status_code == 401:
        authenticate_header = response.headers["WWW-Authenticate"]
        if not authenticate_header.startswith("Bearer "):
            raise Exception("Invalid authentication header in registry response")
        header_dictionary = dict(part.split("=", 1) for part in authenticate_header[len("Bearer "):].strip().split(","))

        token = docker_auth(header_dictionary["realm"].strip("\""), header_dictionary["service"].strip("\""),
                            header_dictionary["scope"].strip("\""))
        response = requests.get("https://registry-1.docker.io/v2/{}/tags/list".format(image),
                                headers={'authorization': "Bearer {}".format(token)})

    if "tags" not in response.json():
        raise Exception("Registry response did not contain tags structure")
    return response.json()["tags"]


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

    pprint.pprint(pods)

    for pod in pods:
        image_name = pod[1].split(":", 1)[0]
        print("Image: {}".format(image_name))


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
    coloredlogs.install(level='DEBUG')
    try:
        print(get_docker_registry_tags("pihole/pihole"))
    except:
        logger.exception("Caught exception")

###
# tokenUri="https://auth.docker.io/token"
# data=("service=registry.docker.io" "scope=repository:$item:pull")
# token="$(curl --silent --get --data-urlencode ${data[0]} --data-urlencode ${data[1]} $tokenUri | jq --raw-output '.token')"
# listUri="https://registry-1.docker.io/v2/$item/tags/list"
# authz="Authorization: Bearer $token"
# result="$(curl --silent --get -H "Accept: application/json" -H "Authorization: Bearer $token" $listUri | jq --raw-output '.')"
# echo $result
