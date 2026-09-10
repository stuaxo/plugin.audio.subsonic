"""Settings, localisation and notification helpers.

A single module-level ``xbmcaddon.Addon`` instance, reused for every read.
"""

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon()

ADDON_ID = ADDON.getAddonInfo("id")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_VERSION = ADDON.getAddonInfo("version")
ADDON_ICON = ADDON.getAddonInfo("icon")
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo("path"))
ADDON_PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))

if not xbmcvfs.exists(ADDON.getAddonInfo("profile")):
    xbmcvfs.mkdirs(ADDON.getAddonInfo("profile"))

def setting(setting_id):
    return ADDON.getSetting(setting_id)


def setting_bool(setting_id):
    return ADDON.getSetting(setting_id) == "true"


def setting_int(setting_id, default=0):
    try:
        return int(ADDON.getSetting(setting_id))
    except (ValueError, TypeError):
        return default


def localized(string_id):
    return ADDON.getLocalizedString(string_id)


# Short alias for use at call sites.
L = localized


def log(message, level=xbmc.LOGDEBUG):
    xbmc.log("[{0}] {1}".format(ADDON_ID, message), level)


def log_error(message):
    log(message, xbmc.LOGERROR)


def notify(message, heading=None, icon=None, time_ms=5000):
    xbmcgui.Dialog().notification(
        heading or ADDON_NAME, message, icon or ADDON_ICON, time_ms
    )
