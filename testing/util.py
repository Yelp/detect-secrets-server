from detect_secrets_server.core.usage.common import storage


EICAR = 'aHR0cHM6Ly93d3cueW91dHViZS5jb20vd2F0Y2g/dj1vSGc1U0pZUkhBMA=='
JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.1YeuHyvmlKMBvPDchxf71EkHMSRmYPD0Vb8Hza1ypbM'


def cache_buster():
    storage.get_storage_options.cache_clear()
    storage.should_enable_s3_options.cache_clear()
