import pkg_resources
__version__ = pkg_resources.require("vimbox")[0].version


class VimboxClientError(Exception):
    pass


class VimboxOfflineError(Exception):
    pass
