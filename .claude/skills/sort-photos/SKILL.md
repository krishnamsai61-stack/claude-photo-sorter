---
name: sort-photos
description: Open the photo sorter dashboard (setting it up first if needed) so the user can sort a folder of photos and videos into folders. Use when the user says "sort my photos", "open my photo sorter", "organize my trip photos" or similar.
---

Follow CLAUDE.md in this repo. In short:

1. Run `./setup.sh` if `.venv/.ok` is missing (read the last line: SETUP_OK / PYTHON_MISSING / SETUP_FAILED).
2. Run `./start.sh --background` and read the `READY <url>` line. It opens the dashboard in their browser.
3. Tell them in three short lines: it's open, click **Choose folder**, pick their photos, press **Start sorting**.
4. If they named a folder in their message, you may start it for them instead: POST to `<url>api/sort` with
   `{"source": "<folder>", "dest": "<folder> (sorted)", "labeler": "claude"}` and tell them to watch the dashboard.

Never move, rename or delete their original photos.
