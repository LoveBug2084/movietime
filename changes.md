# Changes

## Torrent content validation on download

Added `validate_torrent_contents()` to check file extensions after torrent metadata arrives. If no video files are found, the download is cancelled immediately, partial files are cleaned up, and the user is shown "Bad torrent" with a hover tooltip explaining why (e.g. "Not a movie - torrent contains: .m4b").

- `movietime` — new `validate_torrent_contents()` function (line 975)
- `movietime` — modified `wait_for_metadata()` to call validation before proceeding
- `movietime` — new `last_cancel_reason` global to track cancellation state
- `movietime` — updated `api_status` to return `"cancelled"` status with reason
- `templates/index.html` — frontend handles cancelled status in `loadDownloads()` and `checkDownload()`, showing "Bad torrent" in red with a styled dark-theme tooltip

## Apibay category filter removed

Removed the `allowed_cats` filter in `search_apibay()` that restricted results to category 207 (movies). The noise filter in `score_torrent()` and the new `validate_torrent_contents()` check now handle filtering.

## Delete routes simplified to single hash-only route

Removed three backend routes that used `<int:tmdb_id>`:
- `GET /api/download/path/<int:tmdb_id>`
- `DELETE /api/download/delete/<int:tmdb_id>`
- `DELETE /api/download/delete/<int:tmdb_id>/<info_hash>`

Replaced with a single route:
- `DELETE /api/download/delete/hash/<info_hash>` — scans all download directories, works for any torrent regardless of tmdb_id. Cleans up empty parent directories automatically.

Frontend updated:
- Movie card delete iterates `movie.resolutions` and calls hash-only delete for each
- Single resolution delete uses hash-only route directly
- Confirm dialogs no longer show filesystem path

## Seeders display improved for downloaded movies

- 100% downloaded + playable movies show "Ready" instead of fake seeders count
- Partially downloaded movies show nothing in the seeders area initially
- On hover, real seeders from search APIs populate for non-ready items
- "Ready" is preserved after hover by checking `libraryMovies` data during list rebuild
- Removed early-return guard in `updateCardWithTorrent` that blocked hover updates
- Fixed sorting to handle string seeders values without NaN
