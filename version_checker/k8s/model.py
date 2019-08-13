from typing import Tuple, Optional, Set, FrozenSet

from attr import dataclass


@dataclass(frozen=True)
class Resource:
    kind: str
    name: str
    uid: str
    tag_version_pattern_annotation: str
    image_spec: FrozenSet[str]


@dataclass(frozen=True)
class Container:
    server: str
    image: str
    image_id: str
