from kubernetes import client

from version_checker.registry import is_docker_hub_image


def get_images_from_running_pods() -> dict:
    v1core = client.CoreV1Api()
    ret = v1core.list_pod_for_all_namespaces(watch=False)
    v1apps = client.AppsV1Api()
    pods = {(item.spec.node_name, status.image): status.image_id for item in ret.items for status
            in filter(is_docker_hub_image, item.status.container_statuses)}

    images = {}
    for pod in pods:
        images.setdefault(pod[1], {})[pod[0]] = pods[pod]
    return images
