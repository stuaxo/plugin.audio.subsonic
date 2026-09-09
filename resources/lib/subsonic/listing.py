"""Directory-listing and ListItem helpers."""

from collections import namedtuple

import xbmc
import xbmcgui
import xbmcplugin

from .router import HANDLE

ListContext = namedtuple(
    "ListContext",
    "listing succeeded update_listing cache_to_disk sort_methods view_mode content category",
)


def create_listing(listing, succeeded=True, update_listing=False, cache_to_disk=False,
                   sort_methods=None, view_mode=None, content=None, category=None):
    return ListContext(listing, succeeded, update_listing, cache_to_disk,
                       sort_methods, view_mode, content, category)


def build_list_item(item):
    """Build an ``xbmcgui.ListItem`` from a plain dict."""
    li = xbmcgui.ListItem(label=item.get("label", ""), offscreen=True)

    li.setArt({
        "thumb": item.get("thumb", ""),
        "icon": item.get("icon", ""),
        "fanart": item.get("fanart", ""),
    })

    info = item.get("info")
    if info:
        for info_type, info_labels in info.items():
            li.setInfo(info_type, info_labels)

    if item.get("mime"):
        li.setMimeType(item["mime"])
        li.setContentLookup(False)  # skip Kodi's HEAD request on the stream

    if item.get("is_playable"):
        li.setProperty("IsPlayable", "true")

    if item.get("context_menu"):
        li.addContextMenuItems(item["context_menu"])

    for key, value in (item.get("properties") or {}).items():
        li.setProperty(key, value)

    return li


def add_directory_items(context):
    if context.content:
        xbmcplugin.setContent(HANDLE, context.content)
    if context.category:
        xbmcplugin.setPluginCategory(HANDLE, context.category)

    items = []
    for item in context.listing:
        is_folder = not item.get("is_playable", False)
        items.append((item["url"], build_list_item(item), is_folder))
    xbmcplugin.addDirectoryItems(HANDLE, items, len(items))

    for method in context.sort_methods or (xbmcplugin.SORT_METHOD_NONE,):
        xbmcplugin.addSortMethod(HANDLE, method)

    xbmcplugin.endOfDirectory(
        HANDLE, context.succeeded, context.update_listing, context.cache_to_disk
    )

    if context.view_mode is not None:
        xbmc.executebuiltin("Container.SetViewMode(%d)" % context.view_mode)


def set_resolved_url(path, item=None):
    """Resolve a playable URL, carrying metadata/art when ``item`` is given."""
    if item is not None:
        li = build_list_item(dict(item, url=path))
        li.setPath(path)
    else:
        li = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(HANDLE, True, li)
