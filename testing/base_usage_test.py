from abc import ABCMeta

import mock

from detect_secrets_server.core.usage.parser import ServerParserBuilder


class UsageTest(object):

    __metaclass__ = ABCMeta

    def parse_args(self, argument_string='', has_boto=False):
        with mock.patch(
            'detect_secrets_server.core.usage.common.options.s3.should_enable_s3_options',
            return_value=has_boto,
        ):
            return ServerParserBuilder().parse_args(argument_string.split())
