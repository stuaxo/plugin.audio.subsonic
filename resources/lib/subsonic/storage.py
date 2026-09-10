"""Minimal pickle-backed persistent dict, used as a context manager."""

import os
import pickle

from . import addon

_PATH = os.path.join(addon.ADDON_PROFILE, "storage.pcl")


class Storage(dict):
    def __enter__(self):
        try:
            with open(_PATH, "rb") as handle:
                self.update(pickle.load(handle))
        except (OSError, pickle.PickleError, EOFError, AttributeError):
            pass
        return self

    def __exit__(self, *exc):
        try:
            with open(_PATH, "wb") as handle:
                pickle.dump(dict(self), handle, protocol=2)
        except OSError as error:
            addon.log_error("storage write failed: %r" % error)
        return False
