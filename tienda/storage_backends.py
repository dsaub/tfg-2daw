from __future__ import annotations

from storages.backends.s3 import S3ManifestStaticStorage, S3Storage


class StaticStorage(S3ManifestStaticStorage):
    location = 'static'
    default_acl = 'public-read'
    querystring_auth = False
    file_overwrite = True
    object_parameters = {
        'CacheControl': 'public, max-age=31536000, immutable',
    }


class MediaStorage(S3Storage):
    location = 'media'
    default_acl = 'public-read'
    querystring_auth = False
    file_overwrite = False
    object_parameters = {
        'CacheControl': 'public, max-age=604800',
    }