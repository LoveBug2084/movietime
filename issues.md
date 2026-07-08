# Issues Discovered

## Critical

### 1. `ADULT_CATEGORIES` is undefined — will crash at runtime
**File:** `movietime:707`

`search_apibay()` references `ADULT_CATEGORIES` but it is never defined anywhere in the file. This code path is currently dead (apibay calls are commented out), but if uncommented it would raise `NameError`.

### 2. Dead code after `return` in `api_search()`
**File:** `movietime:1613-1728`

After the `return jsonify(...)` on line 1610, there is an entire ~116-line duplicate implementation of the search logic that is completely unreachable. Dead code adds maintenance burden.

### 3. `fetch_and_cache_popular_movies()` writes single JSON object, but load functions expect line-delimited JSON
**File:** `movietime:498-499`, `movietime:514`

- `fetch_and_cache_popular_movies()` saves via `json.dump(cache_data, f)` — a single JSON blob
- `load_cached_movies()` and `load_movies_from_cache()` call `load_json_file()` which expects one JSON object per line
- If `fetch_and_cache_popular_movies()` is ever called, it corrupts `movies_active.json`

### 4. No backend endpoint to cancel torrent downloads
**File:** `index.html:1697`, `movietime` (missing endpoint)

The frontend `cancelDownload()` only calls `/api/play/stop` (stops mpv), but there is no `/api/cancel` to remove the torrent from the libtorrent session. Clicking "Cancel" in the UI only stops playback — the download continues silently.

## Moderate

### 5. `QLocalServer` imported but never used
**File:** `movietime:34`

Unused import from PyQt5.

### 6. Duplicate CSS rule
**File:** `index.html:283-285` vs `index.html:308-311`

`.movie-card .resolution-item:hover` is defined twice with identical values.

### 7. `import shutil` is local to a function
**File:** `movietime:1431`

`import shutil` is inside `api_movies_all()` instead of at the top of the file with all other imports.

### 8. Search results from `displayMovies` can go stale
**File:** `index.html:853`

`displayMovies` is only loaded once on initial page load (or on manual "R" refresh). Background sync continuously adds new movies, but the frontend won't see them until a manual refresh.

### 9. `formatSize()` has no guard against undefined/null
**File:** `index.html:1627`

If `bytes` is `undefined` or `null`, it returns strings like `"undefined B"`.

### 10. `HEADER_MIN_SIZE` definition is duplicated
**File:** `index.html:695` (JS), `movietime:2173` (Python)

Both frontend and backend independently define `HEADER_MIN_SIZE = 100 * 1024 * 1024`. If one changes, the other becomes inconsistent.

### 11. `get_torrent_status` returns bare dict with no schema validation
**File:** `movietime:1200`

Reads JSON from disk with no validation. A corrupted `.movietimeStatus` file returns a partial/faulty dict, and the code proceeds without checking for missing keys.

### 12. Stale outer closure reference in `searchPollInterval`
**File:** `index.html:1717,1732`

The `searchPollInterval` variable is closed over by `pollSearchProgress()` and `cancelCurrentSearch()`. If multiple searches are triggered rapidly, stale intervals can leak.
