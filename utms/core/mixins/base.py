from utms.utils import get_logger


class LoggerMixin:
    @property
    def logger(self):
        if not hasattr(self, "_logger"):
            self._logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        return self._logger
