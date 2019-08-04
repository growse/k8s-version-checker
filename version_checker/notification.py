import logging

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
    def __init__(self, server: str, status: str, registry_digest: str):
        self.server = server
        self.status = status
        self.registry_digest = registry_digest

    def __str__(self):
        return "Registry image has been updated ({registry_digest}) for pod {status} on {server}".format(
            registry_digest=self.registry_digest, status=self.status, server=self.server)


def log_notifications(notifications: list) -> None:
    """
    Outputs a list of notifications to stderr. Useful when running standalone
    :param notifications:
    :return:
    """
    for notification in notifications:
        logger.warning(notification)
