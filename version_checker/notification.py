import logging

from version_checker.k8s import Pod

logger = logging.getLogger(__name__)


class NewTagNotification(object):
    def __init__(self, image: str, tag: str, newest_tag: str):
        self.image = image
        self.tag = tag
        self.newest_tag = newest_tag

    def __str__(self):
        return "Newer tag available for {image}:{tag} -> {new_tag}".format(image=self.image, tag=self.tag,
                                                                           new_tag=self.newest_tag)


class OutOfDatePodNotification(object):
    def __init__(self, pod: Pod, registry_digest: str):
        self.pod = pod
        self.registry_digest = registry_digest

    def __str__(self):
        return "Registry image has been updated ({registry_digest}) for pod {status} on {server} (owned by {owners})".format(
            registry_digest=self.registry_digest,
            status=self.pod.image,
            server=self.pod.server,
            owners=", ".join(
                list(map(lambda owner: "{kind}: {name} ({uid})".format(kind=owner.kind, name=owner.name, uid=owner.uid),
                         self.pod.owners))))


def log_notifications(notifications: list) -> None:
    """
    Outputs a list of notifications to stderr. Useful when running standalone
    :param notifications:
    :return:
    """
    for notification in notifications:
        logger.warning(notification)
