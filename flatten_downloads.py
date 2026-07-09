#!/usr/bin/env python3
"""Move everything in subdirs up to the hash dir, then delete the subdirs."""

import os
import shutil

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "download")


def main():
    for tmdb_id in sorted(os.listdir(DOWNLOAD_DIR)):
        tmdb_path = os.path.join(DOWNLOAD_DIR, tmdb_id)
        if not os.path.isdir(tmdb_path):
            continue

        for info_hash in sorted(os.listdir(tmdb_path)):
            hash_path = os.path.join(tmdb_path, info_hash)
            if not os.path.isdir(hash_path):
                continue

            for entry in os.listdir(hash_path):
                entry_path = os.path.join(hash_path, entry)
                if not os.path.isdir(entry_path):
                    continue

                for item in os.listdir(entry_path):
                    src = os.path.join(entry_path, item)
                    dst = os.path.join(hash_path, item)
                    if os.path.exists(dst):
                        print(f"SKIP collision: {dst} already exists")
                        continue
                    shutil.move(src, dst)

                try:
                    os.rmdir(entry_path)
                    print(f"FLATTENED: {tmdb_id}/{info_hash}/{entry}")
                except OSError:
                    print(f"NOT EMPTY: {tmdb_id}/{info_hash}/{entry}")


if __name__ == "__main__":
    main()
