from detect_secrets_server.core.usage.common import storage


EICAR = 'aHR0cHM6Ly93d3cueW91dHViZS5jb20vd2F0Y2g/dj1vSGc1U0pZUkhBMA=='


def cache_buster():
    storage.get_storage_options.cache_clear()
    storage.should_enable_s3_options.cache_clear()
