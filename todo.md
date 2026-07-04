# TODO: Fix Torrent Year Mismatch (e.g., Scarface 1932 vs 1983)

## Problem
Movies with the same title but different release years are showing incorrect torrents. 
Currently, the `score_torrent` logic rejects torrents with the **wrong** year but accepts torrents with **no year**. Because popular movies (like Scarface 1983) often omit the year in the filename, they are incorrectly matched to movies of the same name from different years (like Scarface 1932).

## Goal
Implement a "Confidence-Based" matching system where torrents that explicitly match the movie's year are prioritized, and torrents with no year are treated as low-confidence matches.

## Technical Tasks

### 1. Modify `score_torrent` in `movietime`
- [ ] **Implement Confidence Levels**:
    - **High Confidence**: Torrent name explicitly contains the correct year $\rightarrow$ Assign a high score bonus.
    - **Low Confidence**: Torrent name contains no year $\rightarrow$ Assign a significantly lower score or a penalty.
    - **Wrong Match**: Torrent name contains a different year $\rightarrow$ Continue returning 0 (Reject).
- [ ] **Rank Priority**: Ensure that any "High Confidence" match always ranks above a "Low Confidence" match, regardless of the seeder count.

### 2. Refine API Queries
- [ ] Verify that `search_apibay` and `search_magnetz` are passing the year correctly in the search query to minimize the return of unrelated versions.

### 3. Verification & Testing
- [ ] **Test Case**: Search for "Scarface".
- [ ] **Verify**: Ensure the movie card for "Scarface (1932)" does NOT display torrents for the 1983 version.
- [ ] **Verify**: Ensure the movie card for "Scarface (1983)" correctly displays its own torrents.
- [ ] **Edge Case**: Verify that torrents with no year are still shown if they are the only available matches, but they are listed below those with the correct year.
