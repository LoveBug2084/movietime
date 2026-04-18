# TV Series Features

## Overview

Add TV series support using TMDB data, with drill-down navigation similar to movies.

## UI Structure

1. **Filter buttons**: `[ Movies ] [ Series ]` at top of page
   - Toggle between movie grid and series grid
   - Default to Movies (existing behavior)
   - Persist selection in URL query param

2. **Drill-down navigation**:
   - Series grid → Season cards → Episode cards
   - Each level uses same card UI with different data
   - Back button to return to previous level

## Card Types

- **Show card**: Poster, title, badge "TV"
- **Season card**: Poster, season number, year, episode count
- **Episode card**: Thumbnail, episode number, title, air date

## Back Navigation

- When viewing seasons: "← Back to Series"
- When viewing episodes: "← Back to Seasons"

## Data Sync

- Use TMDB `/discover/tv` endpoint
- Use `first_air_year` instead of `primary_release_year`
- Collect all episodes for each show
- Store Unaite: unaired/hidden seasons handled as needed

## TV Card Layout

- Single card per show (not separate grids)
- Below poster: title + rating
- Below rating: clickable season list (Season 1 • Season 2 • Season 3 • ...)
- Click season: show episode list below (or replace season list)

## Torrent Handling

Three torrent types supported:
1. **Episode torrent**: Single episode
2. **Season pack**: All episodes in one season
3. **Complete series**: All seasons, all episodes

Display rules:
- **Show view**: Complete series torrents
- **Season view**: Season pack + episode torrents for that season
- **Episode view**: Episode-specific torrents

Torrent labeling: Add badge showing "S1" / "All Seasons" so users know torrent scope.

## Implementation Order

1. Add filter buttons UI
2. Sync TMDB TV data (new script or extend existing)
3. Series grid display
4. TV card layout (single card with season list)
5. Episode list display
6. Torrent handling per level