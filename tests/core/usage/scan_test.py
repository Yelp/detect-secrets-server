from __future__ import absolute_import

import pytest

from detect_secrets_server.hooks.external import ExternalHook
from testing.base_usage_test import UsageTest


class TestScanOptions(UsageTest):

    def test_invalid_local_file(self):
        with pytest.raises(SystemExit):
            self.parse_args('scan --output-hook examples/standalone_hook.py fake_dir -L')

    def test_valid_local_file(self):
        args = self.parse_args('scan examples -L --output-hook examples/standalone_hook.py')

        assert args.action == 'scan'
        assert args.local
        assert isinstance(args.output_hook, ExternalHook)
