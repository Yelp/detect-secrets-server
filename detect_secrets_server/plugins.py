class PluginsConfigParser(object):
    """This entire class assumes that there is at most, only one
    initialization value for plugins.
    """

    def __init__(self, data):
        self.plugins = data

    @classmethod
    def from_config(cls, config):
        """
        Config format is as follows:
            >>> {
            ...     'HexHighEntropyString': 3,
            ...     '<plugin_class_name>': '<initialization_value>',
            ... }

        This format is used for nice layout and config files.
        """
        return cls(config)

    @classmethod
    def from_args(cls, args):
        """
        After getting consolidated through detect_secrets_server.usage, the
        format is as follows:
            >>> {
            ...     'HexHighEntropyString': {
            ...         'hex_limit': [3],
            ...     },
            ...     'PrivateKeyDetector': True,
            ...     '<plugin_class_name>': {
            ...         '<arg_name>': ['<list_of_initialization_args>'],
            ...     },
            ... }

        This format is used for initialization of plugin classes.
        """
        data = {}
        for key in args:
            try:
                data[key] = list(args[key].values())[0][0]
            except AttributeError:
                data[key] = args[key]
            except IndexError:
                data[key] = True

        for key in cls.class_name_to_arg_names():
            if key not in data:
                data[key] = False

        return cls(data)

    def to_config(self):
        return self.plugins

    def to_args(self):
        output = {}

        for key, value in self.plugins.items():
            # For disabling
            if value is False or value is None:
                continue

            # For those keys without initialization values
            elif value is True:
                output[key] = True

            else:
                arg_name = self.class_name_to_arg_names(key)[False]
                output[key] = {
                    arg_name: [value]
                }

        return output

    def update(self, config):
        """Whatever that is in config takes precedence over current settings.

        :type config: PluginsConfigParser
        """
        self.plugins.update(config.plugins)

    @staticmethod
    def class_name_to_arg_names(class_name=None):
        """This mapping should contain a enumeration of all possible
        plugin classes.

        :type class_name: str
        :param class_name: plugin classname

        :rtype: dict(bool => str)
        :returns: bool key references plugin's disabled flag argument name
        """
        mapping = {
            'Base64HighEntropyString': {
                False: 'base64_limit',
                True: 'no_base64_string_scan',
            },
            'HexHighEntropyString': {
                False: 'hex_limit',
                True: 'no_hex_string_scan',
            },
            'PrivateKeyDetector': {
                False: None,
                True: 'no_private_key_scan',
            },
        }

        if not class_name:
            return mapping

        return mapping[class_name]
