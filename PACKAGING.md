# Packaging status: `feat/py-opensonic`

This branch is not ready to ship. It swaps the vendored `lib/libsonic`
(py-sonic) for `lib/libopensonic` (py-opensonic), which unlocks OpenSubsonic
API-key auth but pulls in dependencies a Kodi add-on can't easily vendor:

- **`aiohttp`** - has native (C) extensions. It ships pure-Python fallbacks
  for its own compiled bits, but its dependencies (`multidict`, `yarl`,
  `frozenlist`, `aiosignal`, `propcache`) would each need to be vendored too,
  and each checked for a working pure-Python fallback across every platform
  this add-on installs on (Windows, Linux, macOS, Android, and ARM set-top
  boxes like LibreELEC/CoreELEC, none of which have a C compiler available at
  install time). None of that has been done or verified here.
- **`mashumaro`** - pure Python, no extensions; vendoring it is straightforward
  whenever the `aiohttp` question above is resolved.

Until that dependency tree is either fully vendored (with fallback paths
verified on the platforms above) or Kodi gains a shared `script.module.aiohttp`
add-on to depend on instead, this can't be packaged. Neither currently exists.

## Also unresolved

- **Self-signed certs**: py-opensonic's `Connection` has no equivalent of
  py-sonic's `insecure=True` (it always uses a default `aiohttp.ClientSession()`
  with certificate verification on, created inline in several places rather
  than through one hook). The `insecure` setting is present in `settings.xml`
  but currently has no effect.
- **Cover art caching**: py-opensonic has no synchronous "give me the URL"
  method for cover art (only an async binary fetch). `client.art_path()` works
  around this by fetching and caching images to a file under the profile
  directory, keyed by cover art id, with no eviction. Fine for now; revisit if
  the cache grows unbounded on a large library.
