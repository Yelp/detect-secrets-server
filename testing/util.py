from detect_secrets_server.core.usage.common import storage


def cache_buster():
    storage.get_storage_options.cache_clear()
    storage.should_enable_s3_options.cache_clear()
