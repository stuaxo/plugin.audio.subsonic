#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Service entry point. Bootstraps sys.path, then runs the scrobble loop."""

import os
import sys

import xbmcaddon
import xbmcvfs

_ROOT = xbmcaddon.Addon("plugin.audio.subsonic").getAddonInfo("path")
for _sub in ("lib", os.path.join("resources", "lib")):
    sys.path.append(xbmcvfs.translatePath(os.path.join(_ROOT, _sub)))

from subsonic.scrobbler import main  # noqa: E402

if __name__ == "__main__":
    main()
