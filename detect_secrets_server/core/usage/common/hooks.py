from collections import namedtuple


class HookDescriptor(namedtuple(
    'HookDescriptor',
    [
        # The value that users can input, to refer to this hook.
        # e.g. `--output-hook <display_name>`
        'display_name',

        # module name of plugin, used for initialization
        'module_name',

        'class_name',

        # A HookDescriptor config enum
        'config_setting',
    ]
)):
    CONFIG_NOT_SUPPORTED = 0
    CONFIG_OPTIONAL = 1
    CONFIG_REQUIRED = 2

    def __new__(cls, config_setting=None, **kwargs):
        if config_setting is None:
            config_setting = cls.CONFIG_NOT_SUPPORTED

        return super(HookDescriptor, cls).__new__(
            cls,
            config_setting=config_setting,
            **kwargs
        )


ALL_HOOKS = [
    HookDescriptor(
        display_name='pysensu',
        module_name='detect_secrets_server.hooks.pysensu_yelp',
        class_name='PySensuYelpHook',
        config_setting=HookDescriptor.CONFIG_REQUIRED,
    ),
]
