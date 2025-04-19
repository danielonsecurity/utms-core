from functools import lru_cache

from utms.core.config import UTMSConfig as Config


@lru_cache()
def get_config() -> Config:
    return Config()
