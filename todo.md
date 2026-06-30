# MovieTime TODO - Download Persistence

## Goal
Show progress bar and cancel/play buttons on movies that are already downloaded (persistent across sessions).

## Current State
- Movies stored in `database/movies_active.json` and `database/movies_building.json` as line-delimited JSON
- Movies have: `id`, `title`, `poster`, `overview`, `year`, `rating`, `genre_ids`
- Download info not persisted - lost after page refresh

## Plan

### 1. Backend Changes

#### `api/start` endpoint
- Add `movie_id` to request body from frontend
- Find movie by `id` in building.json
- Add `info_hash` and `status: "downloading"` to that entry
- Call `atomic_swap_and_sync()`
- Update building.json again (was active before swap)

#### `api/status` endpoint
- When download completes (status becomes "ready"), find movie by `info_hash` in building.json or active.json
- Update `status: "ready"`

### 2. Frontend Changes

#### API call to `/api/start`
- Include `movie_id` in request body

#### Render movies
- When rendering cards, check for `status` field in movie data
- If `status: "ready"` → show play button immediately (no hover needed)
- If `status: "downloading"` → show progress bar

No new endpoints or files needed - use existing movie API responses which already include movie data.