import json
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")

for filename in ["movies_active.json", "movies_building.json"]:
    filepath = os.path.join(DB_DIR, filename)
    if not os.path.exists(filepath):
        print(f"Skipping {filename} - not found")
        continue

    print(f"Processing {filename}...")
    fixed = 0
    lines = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if isinstance(entry.get("id"), int):
                entry["id"] = str(entry["id"])
                fixed += 1
            lines.append(json.dumps(entry))

    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"  Fixed {fixed} entries")

print("Done.")
