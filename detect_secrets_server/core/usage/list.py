from .common.options import CommonOptions


class ListOptions(CommonOptions):

    def __init__(self, subparser):
        super(ListOptions, self).__init__(subparser, 'list')
