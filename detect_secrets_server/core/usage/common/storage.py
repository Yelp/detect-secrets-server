try:
    from functools import lru_cache
except ImportError:  # pragma: no cover
    from functools32 import lru_cache


@lru_cache(maxsize=1)
def get_storage_options():
    output = ['file']

    if should_enable_s3_options():
        output.append('s3')

    return output


@lru_cache(maxsize=1)
def should_enable_s3_options():  # pragma: no cover
    try:
        import boto3  # noqa: F401
        return True
    except ImportError:
        return False
