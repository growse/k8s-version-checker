from functools import partial
from typing import Tuple, Optional, Set, FrozenSet

from attr import dataclass


@dataclass(frozen=True)
class Resource:
    kind: str
    name: str
    uid: str
    tag_version_pattern_annotation: str
    image_spec: FrozenSet[str]

    def __str__(self):
        return "{kind}: {name} ({uid})".format(
            kind=self.kind, name=self.name, uid=self.uid
        )


@dataclass(frozen=True)
class Container:
    server: str
    image: str
    image_id: str


@dataclass(frozen=True)
class K8sFetcherFunctions:
    get_deployment_fn: partial
    get_pods_fn: partial
    get_replica_set_fn: partial
    get_stateful_set_fn: partial
    get_daemon_set_fn: partial
    get_cronjob_fn: partial
