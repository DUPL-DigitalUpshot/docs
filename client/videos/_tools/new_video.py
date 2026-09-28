"""Start a new client video: copy _template/ to <type>/<name>/ and list it in catalog.json.

    python3 new_video.py demo brand-team-view "Brand team view"
    python3 new_video.py training add-a-mailbox "Adding an OTP mailbox" --type-label "Training"

Then: write source/narration.json and source/record.py, fill in video.json, and
record → voice → build (see videos/README.md).
"""
import argparse
import json
import pathlib
import re
import shutil
import sys

VIDEOS = pathlib.Path(__file__).resolve().parents[1]
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

ap = argparse.ArgumentParser()
ap.add_argument("type", help="kebab-case video type, e.g. demo, training, release-notes")
ap.add_argument("name", help="kebab-case folder name, e.g. brand-team-view")
ap.add_argument("title", help="human title, e.g. 'Brand team view'")
ap.add_argument("--type-label", help="heading for a new type on the index page")
a = ap.parse_args()

for label, value in (("type", a.type), ("name", a.name)):
    if not SLUG.match(value):
        sys.exit(f"{label} must be kebab-case (a-z, 0-9, -): {value!r}")

dest = VIDEOS / a.type / a.name
if dest.exists():
    sys.exit(f"{dest.relative_to(VIDEOS)} already exists")

shutil.copytree(VIDEOS / "_template", dest)
for f in (dest / "video.json", dest / "source" / "record.py"):
    f.write_text(f.read_text().replace("__TITLE__", a.title).replace("__TYPE__", a.type)
                 .replace("__NAME__", a.name))

catalog_path = VIDEOS / "catalog.json"
catalog = json.loads(catalog_path.read_text())
catalog.setdefault("types", {}).setdefault(a.type, a.type_label or a.type.replace("-", " ").title())
catalog["videos"].append(f"{a.type}/{a.name}")
catalog_path.write_text(json.dumps(catalog, indent=1, ensure_ascii=False) + "\n")

print(f"Created {dest.relative_to(VIDEOS)}/ and added it to catalog.json.")
print("Next: edit source/narration.json, source/record.py and video.json.")
