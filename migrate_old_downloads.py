#!/usr/bin/env python3
"""Migrate old-downloads/ to the new download/<tmdb_id>/<info_hash>/ structure."""

import hashlib
import json
import os
import shutil
import sys

OLD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "old-downloads")
NEW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download")


def is_hash(s):
    return len(s) == 40 and all(c in "0123456789ABCDEF" for c in s.upper())


def pseudo_hash(name):
    return hashlib.sha1(name.encode()).hexdigest().upper()


def count_files(path):
    """Count non-.movietimeStatus entries in a directory."""
    count = 0
    try:
        for entry in os.listdir(path):
            if entry != ".movietimeStatus":
                count += 1
    except (OSError, PermissionError):
        pass
    return count


def dir_size(path):
    """Sum of file sizes in a directory (non-recursive)."""
    total = 0
    try:
        for entry in os.listdir(path):
            entry_path = os.path.join(path, entry)
            if entry != ".movietimeStatus" and os.path.isfile(entry_path):
                total += os.path.getsize(entry_path)
    except (OSError, PermissionError):
        pass
    return total


def migrate():
    if not os.path.isdir(OLD_DIR):
        print(f"Error: {OLD_DIR}/ not found")
        sys.exit(1)

    os.makedirs(NEW_DIR, exist_ok=True)

    migrated = 0
    skipped = 0
    errors = 0

    for entry in sorted(os.listdir(OLD_DIR)):
        entry_path = os.path.join(OLD_DIR, entry)

        if not os.path.isdir(entry_path):
            print(f"SKIP (loose file, no metadata): {entry}")
            skipped += 1
            continue

        status_path = os.path.join(entry_path, ".movietimeStatus")
        if not os.path.exists(status_path):
            print(f"SKIP (no .movietimeStatus): {entry}")
            skipped += 1
            continue

        with open(status_path) as f:
            status = json.load(f)

        tmdb_id = status.get("tmdb_id")
        if tmdb_id is None:
            print(f"SKIP (no tmdb_id in status): {entry}")
            skipped += 1
            continue

        file_count = count_files(entry_path)
        if file_count == 0:
            print(f"SKIP (empty dir, nothing to move): {entry}")
            skipped += 1
            continue

        if is_hash(entry):
            info_hash = entry
        else:
            info_hash = pseudo_hash(entry)

        new_dir = os.path.join(NEW_DIR, str(tmdb_id), info_hash)

        if os.path.exists(new_dir) and count_files(new_dir) > 0:
            print(f"SKIP (destination already exists): {tmdb_id}/{info_hash} ({entry})")
            skipped += 1
            continue

        # Ensure parent dir exists
        os.makedirs(os.path.join(NEW_DIR, str(tmdb_id)), exist_ok=True)

        # Create fresh target
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        os.makedirs(new_dir, exist_ok=True)

        # Move all content (except status file)
        for item in os.listdir(entry_path):
            item_path = os.path.join(entry_path, item)
            if item == ".movietimeStatus":
                continue
            shutil.move(item_path, os.path.join(new_dir, item))

        # Compute clean status
        total = status.get("total_bytes") or 0
        downloaded = status.get("downloaded_bytes") or 0

        # Recovered items are fully downloaded — mark complete
        if status.get("status") == "recovered":
            if total == 0 and downloaded == 0:
                total = dir_size(new_dir)
                downloaded = total
            elif total == 0 and downloaded > 0:
                total = downloaded
            new_status = {
                "progress": 100,
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "status": "completed",
                "is_playable": True,
                "last_updated": status.get("last_updated"),
                "name": status.get("name", entry),
                "tmdb_id": tmdb_id,
            }
        else:
            new_status = {
                "progress": status.get("progress", 0) or 0,
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "status": status.get("status", "downloading"),
                "is_playable": status.get("is_playable", False),
                "last_updated": status.get("last_updated"),
                "name": status.get("name", entry),
                "tmdb_id": tmdb_id,
            }
            if status.get("magnet"):
                new_status["magnet"] = status["magnet"]

        with open(os.path.join(new_dir, ".movietimeStatus"), "w") as f:
            json.dump(new_status, f)

        shutil.rmtree(entry_path)

        print(f"MIGRATED: {entry} → {tmdb_id}/{info_hash}  ({new_status['status']}, {new_status['progress']}%)")
        migrated += 1

    print(f"\nDone: {migrated} migrated, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    migrate()
