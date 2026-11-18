"""Shared paths and helpers. Everything the tool writes lives inside this repo:
  dashboard/data/   inventory, thumbnails, labels (what the dashboard reads)
  work/             contact sheets and raw labels (scratch)
Your original photos are only ever read, never changed.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "dashboard", "data")
THUMBS = os.path.join(DATA, "thumbs")
WORK = os.path.join(ROOT, "work")
LABELS = os.path.join(WORK, "labels")      # Claude writes one JSON per batch here
JEV_OUT = os.path.join(WORK, "jev.json")   # Jev labels (optional)
CATEGORIES = os.path.join(ROOT, "categories.json")

IMG = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
VID = {".mov", ".mp4", ".m4v", ".3gp", ".avi", ".mkv", ".webm"}


def list_media(src):
    """Every photo/video under src, the same way everywhere (folder preview and scan).
    Skips hidden files and folders (phone .thumbnails, .trashed-*, macOS ._ files, .Trashes) and
    earlier '<name> (sorted)' output. Returns (files, blocked) where blocked lists folders macOS refused."""
    files, blocked = [], []
    def err(e):
        if isinstance(e, PermissionError):
            blocked.append(getattr(e, "filename", "") or "")
    for dp, dirs, fs in os.walk(src, onerror=err):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and not d.endswith(" (sorted)"))
        for f in fs:
            if not f.startswith(".") and os.path.splitext(f)[1].lower() in IMG | VID:
                files.append(os.path.join(dp, f))
    return sorted(files), blocked


BLOCKED_HELP = ("macOS didn't let the photo sorter read this folder. Open System Settings > Privacy & Security > "
                "Files and Folders (or Full Disk Access) and allow Terminal (or the Claude app), then try again.")


def clear_library(keep_scan=False):
    """A new folder (or sample size) means the old previews, labels and duplicates no longer match."""
    import shutil
    names = ["labels.json", "dupes.json"] + ([] if keep_scan else ["inventory.json", "source.json"])
    for f in [os.path.join(DATA, n) for n in names] + [JEV_OUT, os.path.join(WORK, "overrides.json")]:
        if os.path.exists(f):
            os.remove(f)
    for d in (LABELS, os.path.join(WORK, "sheets")):
        shutil.rmtree(d, ignore_errors=True)


def load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


def categories():
    cats = load(CATEGORIES)
    keys = [c["key"] for c in cats]
    assert len(keys) == len(set(keys)), "categories.json has duplicate keys"
    for kind in ("photo", "video"):
        assert any(c["kind"] == kind for c in cats), f"categories.json needs at least one {kind} folder"
    return cats


# ---------- running the `claude` command in the background ----------
import re as _re
import shutil as _shutil
import subprocess as _subprocess

# Settings a parent Claude session passes down to its own tools. If the dashboard was started from inside
# Claude Code (or the desktop app), a background `claude -p` would pick these up and try to sign in through
# that parent session, which fails. Dropping them makes it use your normal Claude Code login.
_HOST_ONLY = ("CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT", "ANTHROPIC_BASE_URL", "USE_STAGING_OAUTH", "USE_LOCAL_OAUTH")
_HOST_PREFIXES = ("CLAUDE_CODE_", "CLAUDE_AGENT_SDK")

AUTH_ERROR = _re.compile(r"authenticat|oauth|not logged in|please run /login|/login|invalid api key|credit balance", _re.I)
USAGE_LIMIT = _re.compile(r"usage limit|rate limit|limit reached|out of (extra )?usage|too many requests|overloaded|529", _re.I)
LIMIT_HELP = ("Claude's usage limit was reached for now. Photos that were already sorted are kept: "
              "press Start sorting again when your limit resets, and it carries on where it stopped.")
LOGIN_HELP = ("Claude Code needs you to sign in again. Open the Terminal app, type  claude  and press Enter, "
              "then type  /login  and follow the steps. Then press Start sorting again.")


def find_claude():
    """`claude` on PATH, or in the places the installers put it (a server started by double-click has a short PATH)."""
    found = _shutil.which("claude")
    if found:
        return found
    home = os.path.expanduser("~")
    for p in (f"{home}/.local/bin/claude", f"{home}/.claude/local/claude", "/opt/homebrew/bin/claude",
              "/usr/local/bin/claude", f"{home}/.npm-global/bin/claude", f"{home}/.bun/bin/claude"):
        if os.access(p, os.X_OK):
            return p
    return None


def claude_env():
    env = {k: v for k, v in os.environ.items() if k not in _HOST_ONLY and not k.startswith(_HOST_PREFIXES)}
    env["PATH"] = env.get("PATH", "/usr/bin:/bin") + ":/opt/homebrew/bin:/usr/local/bin:" + os.path.expanduser("~/.local/bin")
    return env


def claude_check(model="haiku", timeout=90):
    """Quick test that `claude -p` can answer. Returns (ok, message)."""
    exe = find_claude()
    if not exe:
        return False, "Claude Code is not installed. Install it from claude.com/claude-code, or use Jev under Advanced."
    try:
        r = _subprocess.run([exe, "-p", "Reply with only the word: ok", "--model", model, "--strict-mcp-config",
                             "--setting-sources", "project", "--no-session-persistence"],
                            capture_output=True, text=True, timeout=timeout, env=claude_env(), cwd=ROOT)
    except _subprocess.TimeoutExpired:
        return False, "Claude Code didn't answer within a minute and a half. Check your internet, then try again."
    out = ((r.stdout or "") + " " + (r.stderr or "")).strip()
    if r.returncode == 0 and "ok" in out.lower():
        return True, "ok"
    if AUTH_ERROR.search(out):
        return False, LOGIN_HELP
    if USAGE_LIMIT.search(out):
        return False, LIMIT_HELP
    return False, "Claude Code couldn't answer: " + " ".join(out.split())[:200]
