import pytest
from pkg_resources import parse_version

from version_checker.notification import NewTagNotification, OutOfDatePodNotification
from version_checker.registry import is_versioned_tag


@pytest.mark.parametrize("valid_version", [
    "1",
    "v1",
    "1.2",
    "1.23.4",
    "v1.23.4",
    "1.23.4-5",
    "v1.23.4-5",
    "1.23.4-rc1",
    "v1.23.4-rc1"
])
def test_versioned_tag_tester_accepts_correct_tags(valid_version):
    assert is_versioned_tag(valid_version)


@pytest.mark.parametrize("invalid_version", [
    "latest",
    "dev",
    "1.23.4_amd64"
])
def test_versioned_tag_tester_rejects_invalid_tags(invalid_version):
    print(parse_version(invalid_version))
    assert not is_versioned_tag(invalid_version)


def test_new_tag_notification_outputs_correct_string_value():
    assert str(NewTagNotification("testimage", "testtag", "v1")) == "Newer tag available for testimage:testtag -> v1"


def test_updated_digest_notification_outputs_correct_string_value():
    assert str(OutOfDatePodNotification("server", "docker-pullable://repo/image:1@sha256:123123123",
                                        "sha256:456456456")) == "Registry image has been updated (sha256:456456456) " \
                                                                "for pod " \
                                                                "docker-pullable://repo/image:1@sha256:123123123 on " \
                                                                "server"
