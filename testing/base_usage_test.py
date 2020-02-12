from abc import ABCMeta
from unittest import mock

from .util import cache_buster
from detect_secrets_server.core.usage.parser import ServerParserBuilder


class UsageTest(object):

    __metaclass__ = ABCMeta

    def parse_args(self, argument_string='', has_boto=False):
        with mock.patch(
            'detect_secrets_server.core.usage.common.storage.should_enable_s3_options',
            return_value=has_boto,
        ), mock.patch(
            'detect_secrets_server.core.usage.s3.should_enable_s3_options',
            return_value=has_boto,
        ):
            return ServerParserBuilder().parse_args(argument_string.split())

    def teardown(self):
        cache_buster()
