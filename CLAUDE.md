# Photo sorter: instructions for the agent

This repo sorts a folder of photos and videos into folders (Selfies, Food, Travel, Screenshots...), finds duplicates, and shows it all on a live dashboard at http://127.0.0.1:8765. The person you're helping has probably never used a terminal. Do every technical step yourself, keep messages short and friendly, and use plain words ("folder", not "directory"). Never paste long logs at them.

## Ground rules (never break these)

1. **Never move, rename or delete the user's original photos.** The tool only reads them and makes sorted copies. If they want duplicates removed, point them to `_Review/duplicates` and `duplicates.csv` and let them do it.
2. **Ask before anything that costs money.** Jev (TypeSafe) is billed per file: run `label_jev.py --estimate`, show the numbers, wait for a yes.
3. **Keep their photos private.** Never commit or upload anything in `dashboard/data/`, `dashboard/peek/`, `dashboard/demo/`, `work/` or `.env`.
4. **Their Claude sign-in is theirs.** Never type passwords or codes for them. If sign-in is needed, open the steps for them and wait.
5. One question at a time, with short numbered options.

## When someone gives you this repo's link (the usual case)

They pasted something like "install and run https://github.com/sukralia/claude-photo-sorter" (or "set up", "open", "sort my photos with ..."). Do all of this without asking:

1. **Download it.** If you're not already inside this repo:
   `git clone https://github.com/sukralia/claude-photo-sorter.git ~/claude-photo-sorter` (if that folder already exists: `git -C ~/claude-photo-sorter pull --ff-only`), then work from `~/claude-photo-sorter`.
   On a brand-new Mac, `git` may open a window asking to install Apple's developer tools: tell them to click **Install**, wait until it finishes, then run the clone again.
2. **Set up.** Run `./setup.sh` (about a minute the first time, instant after). Read the last line:
   - `SETUP_OK`: continue.
   - `PYTHON_MISSING`: a window asking to install developer tools has opened. Tell them to click **Install**, wait, then run `./setup.sh` again.
   - `SETUP_FAILED`: usually no internet. Say so in one line and retry once.
   Notes about ffmpeg or HEIC are fine to ignore. Offer `brew install ffmpeg` only if `brew` exists and they have videos.
3. **Open the dashboard.** Run `./start.sh --background`. It prints `READY http://127.0.0.1:<port>/` and opens their browser; the server keeps running after this chat ends. (If you're in the Claude desktop app you can also show it in the preview pane, using `.claude/launch.json`.)
4. **Tell them, in about three lines:**
   - The photo sorter is open in their browser.
   - Click **Choose folder**, pick the folder with their photos, then press **Start sorting**. Sorted copies go next to the photos in "<folder> (sorted)".
   - To open it again later, double-click **Open Photo Sorter** in the `claude-photo-sorter` folder in their home folder, or ask you to "open my photo sorter".
   If they only want to **see the demo**, run `./start.sh --background --demo` instead (it opens the demo camera roll and plays the sorting animation when they press **Sort with Claude**).
5. Stay available. Answer questions from what you see in `dashboard/data/` and `http://127.0.0.1:8765/api/state`.

If they don't have their photos on the computer yet:
- **iPhone / Apple Photos (Mac):** in Photos, select the photos, then File > Export > Export Unmodified Originals, into a new folder.
- **Google Photos:** takeout.google.com, select only Google Photos, download, unzip everything into one folder.
- **Android phone:** connect it by USB and copy the `DCIM/Camera` folder to the computer.
Never read `Photos Library.photoslibrary` directly.

## If something goes wrong

The dashboard explains most problems itself. What you may need to do:

| What they see | What to do |
|---|---|
| "Claude needs you to sign in again" | Claude Code's login on this Mac expired. Run `claude` in a new Terminal tab for them (or tell them to open Terminal and type `claude`), then they type `/login` and finish in the browser. Check with `.venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); from common import claude_check; print(claude_check())"`, then they press **Try again**. |
| "Claude needs a short break" | Their plan's usage limit. Finished batches are kept; they press **Continue sorting** later. |
| "macOS didn't let the photo sorter read this folder" | System Settings > Privacy & Security > Files and Folders (or Full Disk Access): allow Terminal or the Claude app. |
| Page won't load | Run `./start.sh --background` again. It reuses a running copy or starts a new one, and moves to the next port if 8765 is taken. Log: `work/server.log`. |
| Photos look blank / HEIC fails | `.venv/bin/pip install -U pillow-heif`, then sort again. |
| Want to start completely fresh | `rm -rf .venv && ./setup.sh` (their photos and sorted copies are not touched). |

## Running steps from the chat instead

| Step | Command |
|---|---|
| Scan | `.venv/bin/python scripts/scan.py "<photos folder>" [--limit 200]` |
| Duplicates | `.venv/bin/python scripts/dupes.py` (see `work/duplicates.jpg`) |
| Sample sheets | `.venv/bin/python scripts/sheets.py --sample` (look at `work/sample/` to suggest folders) |
| Labels (Claude) | `.venv/bin/python scripts/label_claude.py` |
| Labels (Jev, paid) | `.venv/bin/python scripts/label_jev.py --estimate`, then without `--estimate` |
| Build folders | `.venv/bin/python scripts/apply.py "<output folder>"` |

The open dashboard refreshes itself when these run. Scanning a new folder clears the old labels automatically.

**Choosing folders.** Folders live in `categories.json` (`key`, `kind` photo or video, `label`, `emoji`, `rule`). The `rule` is what the model reads. Offer: 1) the standard folders, 2) folders you suggest after looking at `work/sample/` (a traveller gets "Beaches" and "Landmarks", a parent gets "Kids" and "School"), or 3) their own list. Keep at least one photo and one video folder, and make the last folder of each kind a catch-all. They can also do this in the dashboard under **Edit folders**.
