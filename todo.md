# TODO: Migrate Download Storage to `tmdb_id/hash/` Layout

## Goal
Restructure from `download/<info_hash>/` to `download/<tmdb_id>/<info_hash>/`.
TMDB ID becomes the directory root — the path itself defines the relationship,
eliminating all dedup/matching/healing logic.

## Strategy — `find_video_file` with optional tmdb_id

`find_video_file(info_hash, tmdb_id=None)` — when `tmdb_id` is provided, look
directly in `download/<tmdb_id>/<info_hash>/`. When not, scan `download/` for
any `<tmdb_id>/<info_hash>/` match. This way all existing callers still work.

## Backend — Every Function Change

### Path helpers — add tmdb_id parameter
- [ ] `save_torrent_status(tmdb_id, info_hash, status_data)` — write to `download/<tmdb_id>/<info_hash>/.movietimeStatus`
- [ ] `get_torrent_status(tmdb_id, info_hash)` — read from `download/<tmdb_id>/<info_hash>/.movietimeStatus`
- [ ] `find_video_file(info_hash, tmdb_id=None)` — search `download/<tmdb_id>/<info_hash>/` if tmdb_id, else scan all tmdb dirs

### `download_torrent(magnet_link, info_hash, name, tmdb_id)` (line 1092)
- [ ] Add `tmdb_id` param
- [ ] Change save path: `download/<tmdb_id>/<info_hash>/` (was `download/<info_hash>/`)

### `update_active_download_status_loop()` (line 1250)
- [ ] Pass `current_download["tmdb_id"]` to `find_video_file()` (line 1272)
- [ ] Pass `current_download["tmdb_id"]` to `save_torrent_status()` (line 1275)

### `/api/start` (line 1998)
- [ ] Pass `tmdb_id` to `download_torrent()` so save path is correct
- [ ] Remove `save_torrent_status` call (download_torrent will create the dir)

### `/api/status` (line 2054)
- [ ] Pass `current_download["tmdb_id"]` to `find_video_file()` (lines 2069, 2084)
- [ ] Pass `current_download["tmdb_id"]` to `get_torrent_status()` (line 2129)

### `/api/downloads/list` (line 1788) — COMPLETE REWRITE
- [ ] Iterate `download/<tmdb_id>/` directories, then `<info_hash>/` subdirs
- [ ] For each hash subdir, read `.movietimeStatus`
- [ ] Look up movie by `tmdb_id` in cache — simple dict lookup
- [ ] Return movie data with all resolution items
- [ ] REMOVE: fallback name/year matching (lines 1837-1878)
- [ ] REMOVE: orphan recovery / self-heal (lines 1814-1827)
- [ ] REMOVE: `movie_id_map` / `sorted_movies` setup (lines 1799-1801)

### `/api/torrent` (line 1905) — REMOVE SELF-HEAL
- [ ] REMOVE: healing missing status files (lines 1941-1963)
- [ ] REMOVE: self-heal tmdb_id on hover (lines 1965-1979)
- [ ] KEEP: status lookup by `download/<tmdb_id>/<info_hash>/` — just read and annotate
- [ ] KEEP: dedup by info_hash (lines 1928-1937) — still useful for search results

### `/api/play` (line 2186) — accept tmdb_id from frontend
- [ ] Accept `tmdb_id` in request JSON
- [ ] Pass `tmdb_id` to `find_video_file()` (lines 2200, 2234)
- [ ] Pass `tmdb_id` to `get_torrent_status()` (line 2201)
- [ ] Pass `tmdb_id` to `download_torrent()` for resume (lines 2221, 2228)

### `/api/cancel` (line 2306)
- [ ] Pass `current_download["tmdb_id"]` to `get_torrent_status()` (line 2325)
- [ ] Pass `current_download["tmdb_id"]` to `save_torrent_status()` (line 2328)

## Frontend — Every Change

### `startPlayback(infoHash)` → sends `{info_hash, tmdb_id}` to backend
- [ ] Change POST body to `{info_hash: infoHash, tmdb_id: tmdbId}` (line 1642)
- [ ] Update all callers to pass `tmdb_id` where available
- [ ] Callers: lines 1101, 1211, 1423, 1428, 1476, 1557, 1597, 1610, 1623

### Info hash collision guards — add tmdb_id comparison
- [ ] Line 1106: add `statusData.tmdb_id !== card.dataset.movieId` check
- [ ] Line 1343: add tmdb_id check alongside info_hash comparison
- [ ] Line 1462: add tmdb_id check

### Card selectors — use `data-movie-id` alongside `data-info-hash`
- [ ] Line 1115: `[data-movie-id="..."]` instead of `[data-info-hash="..."]`
- [ ] Line 1307: add `card.dataset.movieId` check
- [ ] Line 1626: add `data-movie-id` to selector
- [ ] Line 1672: add `card.dataset.movieId` check
- [ ] Line 962: save `prevMovieId` alongside `prevInfoHash`

### Remove dedup logic
- [ ] `applyCurrentView()` lines 774-781 — remove `seen` filter
- [ ] `performSearch()` lines 1779-1786 — remove `seen` filter

## Code to Remove Entirely
- `score_torrent()` function (lines 600-662) — only used for download matching, not needed
- Fallback name/year matching in `/api/downloads/list` (lines 1837-1878)
- Self-heal / healing logic in `/api/torrent` (lines 1941-1979)
- Orphan recovery in `/api/downloads/list` (lines 1814-1827)

## Code to Keep As-Is
- `search_apibay()` / `search_magnetz()` — search still uses score_torrent for relevance
- `rebuild_combined_final()` — search result merging
- `find_subtitle_files()` — operates on video path, no change
- `apply_sequential_priority()` — libtorrent logic, no change
- All CSS / HTML structure in frontend
- `/api/open-downloads` — opens base folder, no change
