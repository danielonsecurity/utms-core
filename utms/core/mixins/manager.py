from abc import ABC
from collections.abc import MutableMapping

from .persistence import HyPersistenceMixin


class ManagerMixin(HyPersistenceMixin, MutableMapping, ABC):
    """Base mixin for all managers, combining common manager functionality.

    Currently includes:
    - LoggerMixin (via HySaveMixin)
    - HySaveMixin
    """

    pass
