from detect_secrets_server.plugins import PluginsConfigParser


class TestPluginsConfigParser(object):

    def test_from_config_output_config(self):
        assert PluginsConfigParser.from_config(self.mock_config)\
            .to_config() == self.mock_config

    def test_from_config_output_args(self):
        assert PluginsConfigParser.from_config(self.mock_config)\
            .to_args() == self.mock_args

    def test_from_args_output_config(self):
        assert PluginsConfigParser.from_args(self.mock_args)\
            .to_config() == self.mock_config

    def test_from_args_output_args(self):
        assert PluginsConfigParser.from_args(self.mock_args)\
            .to_args() == self.mock_args

    @property
    def mock_config(self):
        return {
            'HexHighEntropyString': 3,
            'PrivateKeyDetector': True,
            'Base64HighEntropyString': False,
        }

    @property
    def mock_args(self):
        return {
            'HexHighEntropyString': {
                'hex_limit': [3],
            },
            'PrivateKeyDetector': True,
        }
