import logging

from version_checker.k8s import Container, Resource

logger = logging.getLogger(__name__)


class Notification(object):
    pass


class NewTagNotification(Notification):
    def __init__(self, image: str, tag: str, newest_tag: str):
        self.image = image
        self.tag = tag
        self.newest_tag = newest_tag

    def __str__(self):
        return "Newer tag available for {image}:{tag} -> {new_tag}".format(image=self.image, tag=self.tag,
                                                                           new_tag=self.newest_tag)


class OutOfDateContainerNotification(Notification):
    def __init__(self, owner: Resource, container: Container, registry_digest: str):
        self.owner = owner
        self.container = container
        self.registry_digest = registry_digest

    def __str__(self):
        return "Registry image has been updated ({registry_digest}) for pod {status} on {server} (owned by {owner})".format(
            registry_digest=self.registry_digest,
            status=self.container.image,
            server=self.container.server,
            owner=self.owner)


def log_notifications(notifications: list) -> None:
    """
    Outputs a list of notifications to stderr. Useful when running standalone
    :param notifications:
    :return:
    """
    for notification in notifications:
        logger.warning(notification)
