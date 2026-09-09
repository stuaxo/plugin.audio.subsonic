#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Plugin entry point. Bootstraps sys.path, then hands off to the router."""

import os
import sys

import xbmcaddon
import xbmcvfs

_ROOT = xbmcaddon.Addon("plugin.audio.subsonic").getAddonInfo("path")
for _sub in ("lib", os.path.join("resources", "lib")):
    sys.path.append(xbmcvfs.translatePath(os.path.join(_ROOT, _sub)))

from subsonic import views  # noqa: E402,F401  (import registers the actions)
from subsonic.router import run  # noqa: E402

if __name__ == "__main__":
    run()
