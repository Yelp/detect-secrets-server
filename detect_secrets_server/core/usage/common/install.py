try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache


@lru_cache(maxsize=1)
def get_install_options():
    return ['cron']
