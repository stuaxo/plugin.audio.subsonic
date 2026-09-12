# Vendoring notes: `lib/libsonic`

Base: [py-sonic](https://github.com/crustymonkey/py-sonic) `1.1.2` (upstream
tag), vendored as source rather than installed, per Kodi add-on convention -
there's no pip at runtime. `errors.py` is unmodified upstream.

Patches on top of that base, each marked with a `plugin.audio.subsonic patch`
comment at its site in `connection.py`:

- **`streamUrl()` / `getCoverArtUrl()`** - upstream has no equivalent. It only
  offers `stream()`/`getCoverArt()`, which perform the HTTP request and hand
  back the response body. This addon needs a URL string instead, to give
  directly to Kodi's player/art loader without a round trip through this
  process. Both require `useGET=True`: with the default POST, the built
  request has no query string to read back out of.
- **`HTTPSConnectionChain` / `HTTPSHandlerChain` / `PysHTTPRedirectHandler`**,
  wired into `_getOpener()` - upstream's `_getOpener()` is a bare
  `urllib.request.build_opener()`; it stores `insecure` but never acts on it.
  These classes make `insecure=True` actually skip certificate verification
  (self-signed certs), and make redirects preserve POST data across an
  http↔https hop (Python's default `HTTPRedirectHandler` doesn't).
- **`&verifypeer=false`** appended to `streamUrl()`/`getCoverArtUrl()` output
  when `insecure=True` - tells Kodi's own player/image loader, which opens
  that URL independently of this library, to also skip cert verification.
- **Subfolder-aware `baseUrl`** in `__init__` - if `baseUrl` contains a path
  (e.g. `http://host/subsonic`), it's split into a bare host plus
  `serverPath` automatically, so the add-on's single URL setting field can
  carry a proxied/subfolder install without a second setting.

Not carried forward - **not fixed upstream either**: the `urllib2.Request(url,
...)` calls in the `useGET` branch of `_getRequest()`, `_getRequestWithList()`
and `_getRequestWithLists()` reference a name that's never imported
(`urllib2` is the Python 2 module name; this file uses `urllib.request`
everywhere else). Silently fixed to `urllib.request.Request(...)` in all three
spots - upstream 1.1.2 still has this bug in all three, not just the two that
existed in the 0.7.9 base this project vendored previously.

Adopted from upstream instead of re-patching: upstream 1.1.0 added a
`userAgent=` constructor param. This project used to hardcode a browser
User-Agent inside a patched `_getOpener()` to get past Cloudflare/WAF
blocking; that's now passed as `userAgent=` from
`resources/lib/subsonic/client.py` instead, using the same string.
