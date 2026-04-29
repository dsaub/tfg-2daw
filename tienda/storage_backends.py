from __future__ import annotations

import os

from django.utils.encoding import iri_to_uri
from storages.backends.s3 import S3ManifestStaticStorage, S3Storage


def _use_local_asset_urls() -> bool:
    return os.getenv('S3_USE_LOCAL_URLS', '').strip().lower() in {'1', 'true', 'yes', 'on'}


def _local_asset_url(prefix: str, name: str) -> str:
    return iri_to_uri(f'/{prefix}/{name.lstrip("/")}')


class StaticStorage(S3ManifestStaticStorage):
    location = 'static'
    default_acl = 'public-read'
    querystring_auth = False
    file_overwrite = True
    object_parameters = {
        'CacheControl': 'public, max-age=31536000, immutable',
    }

    def url(self, name: str) -> str:
        if _use_local_asset_urls():
            return _local_asset_url('static', name)
        return super().url(name)


class MediaStorage(S3Storage):
    location = 'media'
    default_acl = 'public-read'
    querystring_auth = False
    file_overwrite = False
    object_parameters = {
        'CacheControl': 'public, max-age=604800',
    }

    def url(self, name: str) -> str:
        if _use_local_asset_urls():
            return _local_asset_url('media', name)
        return super().url(name)