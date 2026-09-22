"""MenuBelt - Krita custom-shortcut file layer (``kritashortcutsrc``).

Krita keeps user shortcut overrides in a KConfig INI file named
``kritashortcutsrc``, sitting next to ``kritarc`` (Windows: ``%LOCALAPPDATA%``,
Linux: ``~/.config``).  Krita re-reads that file on every start, so merely
clearing a QAction at runtime only *looks* permanent: on the next start the
action gets its shortcut back and steals the key from MenuBelt again.  Writing
an entry here is what makes an override survive a restart.

File format (KDE KConfig, CRLF on Windows)::

    [Shortcuts]
    file_export_file=Ctrl+E
    file_quit=none

Krita's loader (KisActionRegistry::loadCustomShortcuts) has two "null" states:

* key absent            -> the action keeps its built-in default shortcut
* key present, ``none`` -> the action is explicitly unbound

So unbinding = write ``none``; *restoring the default* = delete the entry again.

Pure stdlib on purpose (no Qt / krita import) so it can be tested outside Krita.
"""

import os

GROUP = "[Shortcuts]"
UNBOUND = "none"


# ---------- text layer ----------
def _split_eol(text):
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    if lines and lines[-1] == "":
        lines.pop()          # text ended with a line break: don't re-add a blank line
    return lines, eol


def _is_header(line):
    s = line.strip()
    return s.startswith("[") and s.endswith("]")


def _in_shortcuts_group(lines):
    """Yield (index, key, value) for entries inside the [Shortcuts] group."""
    inside = False
    for i, line in enumerate(lines):
        s = line.strip()
        if _is_header(s):
            inside = (s == GROUP)
            continue
        if not inside:
            continue
        if not s or s.startswith((";", "#")) or "=" not in s:
            continue
        key, value = s.split("=", 1)
        yield i, key.strip(), value.strip()


def parse_entries(text):
    """Return ``{action_id: value}`` for the [Shortcuts] group only."""
    lines, _ = _split_eol(text)
    return {key: value for _i, key, value in _in_shortcuts_group(lines)}


def is_unbound(value):
    """True when `value` means "this action has no shortcut"."""
    return (value or "").strip().lower() in ("", UNBOUND)


def set_entries(text, updates):
    """Return `text` with `updates` ({action_id: value}) merged into [Shortcuts].

    Existing keys are rewritten in place, new keys are appended to the group,
    the group is created when missing, and the file's line endings are kept.
    """
    lines, eol = _split_eol(text)
    pending = dict(updates)

    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == GROUP:
            start = i
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if _is_header(lines[j]):
                    end = j
                    break
            break

    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(GROUP)
        start = len(lines) - 1
        end = len(lines)

    body = []
    for line in lines[start + 1:end]:
        s = line.strip()
        if "=" in s and not s.startswith((";", "#")):
            key = s.split("=", 1)[0].strip()
            if key in pending:
                body.append("%s=%s" % (key, pending.pop(key)))
                continue
        body.append(line)
    for key, value in pending.items():
        body.append("%s=%s" % (key, value))
    lines[start + 1:end] = body
    return eol.join(lines) + eol


def remove_entries(text, keys):
    """Delete `keys` from [Shortcuts] (their built-in defaults come back)."""
    keys = set(keys)
    lines, eol = _split_eol(text)
    out = []
    inside = False
    for line in lines:
        s = line.strip()
        if _is_header(s):
            inside = (s == GROUP)
            out.append(line)
            continue
        if inside and "=" in s and not s.startswith((";", "#")):
            if s.split("=", 1)[0].strip() in keys:
                continue
        out.append(line)
    joined = eol.join(out)
    return joined + eol if joined else ""


# ---------- file layer ----------
def config_dir_candidates(qt_dirs=(), env=None):
    """Ordered list of directories that may hold ``kritarc``/``kritashortcutsrc``."""
    env = os.environ if env is None else env
    out = [d for d in qt_dirs if d]
    if env.get("XDG_CONFIG_HOME"):
        out.append(env["XDG_CONFIG_HOME"])
    home = env.get("HOME") or env.get("USERPROFILE")
    if home:
        out.append(os.path.join(home, ".config"))
        out.append(os.path.join(home, "Library", "Preferences"))
    for var in ("LOCALAPPDATA", "APPDATA"):
        if env.get(var):
            out.append(env[var])
    uniq, seen = [], set()
    for d in out:
        d = os.path.normpath(d)
        if d not in seen:
            seen.add(d)
            uniq.append(d)
    return uniq


def find_shortcut_file(qt_dirs=(), env=None):
    """Path of Krita's ``kritashortcutsrc``, or None when no Krita config dir exists.

    Anchored on ``kritarc``, which always lives next to the shortcut file.
    """
    cands = config_dir_candidates(qt_dirs, env)
    for d in cands:
        candidate = os.path.join(d, "kritashortcutsrc")
        if os.path.isfile(candidate):
            return candidate
    for d in cands:
        if os.path.isfile(os.path.join(d, "kritarc")):
            return os.path.join(d, "kritashortcutsrc")
    return None


def read_text(path):
    """Return the file's text ('' when missing/unreadable). Line endings kept as-is."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
            return f.read()
    except OSError:
        return ""


def write_text(path, text):
    """Write `text` back (no-op if nothing would change). Line endings kept as-is."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
            if f.read() == text:
                return False
    except OSError:
        pass
    try:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        return True
    except OSError as e:
        print("menubelt: cannot write %s: %s" % (path, e))
        return False


def unbind(path, action_id):
    """Persist "this action has no shortcut". Returns its previous entry (or None)."""
    text = read_text(path)
    previous = parse_entries(text).get(action_id)
    write_text(path, set_entries(text, {action_id: UNBOUND}))
    return previous


def restore(path, previous):
    """Undo `unbind`: `previous` maps action_id -> old value, None = delete the key."""
    text = read_text(path)
    to_delete = [k for k, v in previous.items() if v is None]
    updates = {k: v for k, v in previous.items() if v is not None}
    if to_delete:
        text = remove_entries(text, to_delete)
    if updates:
        text = set_entries(text, updates)
    write_text(path, text)
