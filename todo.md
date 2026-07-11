# Unified download/playback system

## Problem
- 5+ entry points for starting downloads and playback
- Some refresh `libraryMovies`, some don't
- Stale data in full view when torrents are deleted
- `playMovie()` (most common path) never updates `libraryMovies`

## Plan

### 1. Backend: write stub status file in `/api/start`
File: `movietime`, function `api_start()` (line 1967)
After `threading.Thread(...).start()` at line 1986, write initial `.movietimeStatus` with `save_torrent_status()` so `/api/downloads/list` finds the entry immediately with no race condition.

### 2. Frontend: new `startTorrent(torrent, card)` function
File: `templates/index.html`
Combines the download-starting logic from both `startDownloadFromTorrent` and `playMovie`:
- Check status / cancel existing
- Call `/api/start`
- Refresh `libraryMovies` = fetch `/api/downloads/list` + `enrichLibraryMovies()`
- Set card state + start polling

### 3. Frontend: collapse all entry points
- Resolution item click → `startTorrent()` or `startPlayback()`
- Card click → pick best resolution → `startTorrent()` or `startPlayback()`
- `playMovie()` → reduced to decision logic only, calls `startTorrent()`/`startPlayback()` at the end
- Remove `startDownloadFromTorrent()` — fully replaced by `startTorrent()`

### 4. Verify
- Python compiles
- Full flow: search → download → library view shows it
- Full flow: play from library card → works
- Full flow: delete torrent → full view updates
