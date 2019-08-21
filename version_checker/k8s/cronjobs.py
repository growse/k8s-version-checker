from typing import Dict

from version_checker.k8s import (
    top_level_not_ignored_resource,
    VERSION_PATTERN_ANNOTATION,
)
from version_checker.k8s.model import Resource, Container, K8sFetcherFunctions


def get_top_level_cronjobs(
    k8s_fetcher_functions: K8sFetcherFunctions
) -> Dict[Resource, Container]:
    k8s_cronjob_response = k8s_fetcher_functions.get_cronjob_fn()

    top_level_not_ignored_cronjob = [
        cronjob
        for cronjob in k8s_cronjob_response.items
        if top_level_not_ignored_resource(cronjob)
    ]
    return {
        Resource(
            kind="Cron Job",
            name=cronjob.metadata.name,
            uid=cronjob.metadata.uid,
            tag_version_pattern_annotation=cronjob.metadata.annotations.get(
                VERSION_PATTERN_ANNOTATION, ""
            ),
            image_spec=frozenset(
                {
                    str(container_spec.image)
                    for container_spec in cronjob.spec.job_template.spec.template.spec.containers
                }
            ),
        ): []
        for cronjob in top_level_not_ignored_cronjob
    }
