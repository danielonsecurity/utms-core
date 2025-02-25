from .persistence import HyPersistenceMixin


class ManagerMixin(HyPersistenceMixin):
    """Base mixin for all managers, combining common manager functionality.

    Currently includes:
    - LoggerMixin (via HySaveMixin)
    - HySaveMixin
    """

    pass
