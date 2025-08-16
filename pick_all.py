#!/usr/bin/env python3
import json
import sys
import urllib.request

BASE = "https://review.lineageos.org"
BRANCH = "lineage-23.0"
# explicit repos to skip (suffix only, after "LineageOS/")
SKIP_REPOS = {
    "android_frameworks_base",
    "android_packages_Settings",
    "android_system_sepolicy",
    "android_frameworks_native",
    "android_device_oneplus_sdm845-common",
    "android_device_sony_tama-common",
    "android_hardware_samsung",
    "android_hardware_xiaomi",
    "android_hardware_sony",
    "android_hardware_oplus",
    "android_vendor_lineage",

}

def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        data = resp.read().decode()
    return json.loads(data[5:])  # strip ")]}'"

def fetch_all_changes(query):
    changes = []
    start = 0
    while True:
        url = f"{BASE}/changes/?q={query}&n=500&S={start}"
        batch = fetch_json(url)
        if not batch:
            break
        changes.extend(batch)
        if '_more_changes' not in batch[-1]:
            break
        start += 500
    return changes

def main():
    # extra args to repopick (like -f, -i, etc.)
    args = sys.argv[1:]

    query = f"status:open+-is:wip+branch:{BRANCH}"
    changes = fetch_all_changes(query)

    ids = []
    for c in changes:
        # Gerrit project looks like "LineageOS/android_frameworks_base"
        suffix = c['project'].split("/", 1)[-1]

        # skip if explicitly listed OR starts with android_device_
        if suffix in SKIP_REPOS or suffix.startswith("android_device_") or suffix.startswith("android_kernel_"):
            continue

        ids.append(str(c['_number']))

    print("repopick", *args, *ids)

if __name__ == "__main__":
    main()
