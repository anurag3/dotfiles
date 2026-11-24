#!/usr/bin/env python3
"""Track freshness of a repo's local .docs/ notes against git history.

Usage: docs_state.py status|diff|stamp|init-manifest <repo> [args]
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DOCS = ".docs"
MANIFEST = f"{DOCS}/manifest.json"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
HEADER_RE = re.compile(r"^Checked \d{4}-\d{2}-\d{2} (?:against |\(not a git repo\))")
CITATION_RE = re.compile(r"`([^`\s:]+):(\d+)(?:-(\d+))?`")
AS_OF_RE = re.compile(r"as of (\d{4}-\d{2}-\d{2})", re.I)
TLDS = {"com", "net", "org", "io", "ai"}


class DocsError(Exception):
    def __init__(self, msg, code=1):  # noqa: B042
        super().__init__(msg)
        self.code = code


def today():
    env = os.environ.get("DOCS_STATE_TODAY")
    return datetime.date.fromisoformat(env) if env else datetime.date.today()


def git(repo, *args, check=True):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise DocsError(f"git {args[0]} failed: {r.stderr.strip()}")
    return r


def is_git(repo):
    r = git(repo, "rev-parse", "--show-toplevel", check=False)
    return r.returncode == 0 and os.path.realpath(r.stdout.strip()) == os.path.realpath(repo)


def head_sha(repo):
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def branch_name(repo):
    return git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def glob_to_regex(pattern):
    pattern = pattern.rstrip("/")
    if "*" not in pattern:
        return re.compile(re.escape(pattern) + r"(?:/.*)?$")
    parts = pattern.split("/")
    out = ""
    for i, seg in enumerate(parts):
        last = i == len(parts) - 1
        if seg == "**":
            out += ".*" if last else "(?:[^/]+/)*"
            continue
        out += "".join("[^/]*" if c == "*" else re.escape(c) for c in seg)
        out += "" if last else "/"
    return re.compile(out + "$")


def covers_match(covers, path):
    return any(glob_to_regex(c).match(path) for c in covers)


def load_manifest(repo):
    p = Path(repo) / MANIFEST
    if not p.exists():
        raise DocsError(f"no {MANIFEST} in {repo}; run: docs_state.py init-manifest {repo}", 2)
    try:
        m = json.loads(p.read_text())
        if not isinstance(m, dict) or not isinstance(m.get("files"), dict):
            raise ValueError("top level must be an object with a 'files' object")
        datetime.date.fromisoformat(m["generated"])
    except KeyError:
        raise DocsError(f"invalid {MANIFEST}: missing 'generated'")
    except (ValueError, TypeError) as e:
        raise DocsError(f"invalid {MANIFEST}: {e}")
    return m


def validate_covers(m, only=None):
    for note, info in m["files"].items():
        if info.get("frozen") or (only and note != only):
            continue
        for c in info.get("covers", []):
            if re.search(r"[?\[]", c):
                raise DocsError(f"glob pattern not supported in {note}: {c} (use only *, ** or bare paths)")


def save_manifest(repo, m):
    m = dict(m)
    m["files"] = {k: m["files"][k] for k in sorted(m["files"])}
    (Path(repo) / MANIFEST).write_text(json.dumps(m, indent=2) + "\n")


def split_z(text):
    return [t for t in text.split("\0") if t]


def entries_from(pairs):
    """Turn (old, new) pairs into {display: paths}, dropping anything under .docs/."""
    result = {}
    for old, new in pairs:
        if old.startswith(f"{DOCS}/") or new.startswith(f"{DOCS}/"):
            continue
        result[old if old == new else f"{old} -> {new}"] = [old] if old == new else [old, new]
    return result


def committed_changes(repo, base):
    toks = split_z(git(repo, "diff", "--name-status", "-z", "-M", f"{base}..HEAD").stdout)
    pairs, i = [], 0
    while i < len(toks):
        if toks[i][0] in "RC":
            pairs.append((toks[i + 1], toks[i + 2]))
            i += 3
        else:
            pairs.append((toks[i + 1], toks[i + 1]))
            i += 2
    return entries_from(pairs)


def worktree_changes(repo):
    # Untracked dirs stay collapsed in the display; their files are expanded only for matching.
    toks = split_z(git(repo, "status", "--porcelain", "-z").stdout)
    pairs, i = [], 0
    while i < len(toks):
        xy, path = toks[i][:2], toks[i][3:]
        if "R" in xy or "C" in xy:
            pairs.append((toks[i + 1], path))
            i += 2
        else:
            pairs.append((path, path))
            i += 1
    result = entries_from(pairs)
    for disp in list(result):
        if disp.endswith("/"):
            result[disp] = split_z(git(repo, "ls-files", "--others", "--exclude-standard", "-z", "--", disp).stdout)
    return result


def resolve_base(repo, sha, date):
    """Return (base, warning). Falls back to the last commit before `date` when sha is unusable."""
    if sha and git(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode == 0:
        return sha, None
    # T00:00:00 errs toward reporting more changes, not fewer.
    found = git(repo, "rev-list", "-1", f"--before={date}T00:00:00", "HEAD").stdout.strip()
    what = sha or "null"
    if found and not sha:
        return found, f"No recorded sha; fallback: last commit before {date}T00:00:00 ({found[:8]})."
    if found:
        return found, f"Recorded sha {what} is missing; fallback: last commit before {date}T00:00:00 ({found[:8]})."
    return EMPTY_TREE, f"Recorded sha {what} is missing; fallback: no commit before {date}, using the empty tree."


def list_notes(repo):
    root = Path(repo) / DOCS
    return sorted(str(p.relative_to(root)) for p in root.rglob("*.md"))


def known_files(repo, git_mode):
    if git_mode:
        return set(git(repo, "ls-files").stdout.splitlines())
    found = set()
    for dirpath, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in (DOCS, ".git")]
        found.update(os.path.relpath(os.path.join(dirpath, f), repo) for f in files)
    return found


def expand_braces(path):
    m = re.search(r"\{([^{}]*)\}", path)
    if not m:
        return [path]
    return [path[: m.start()] + alt + path[m.end() :] for alt in m.group(1).split(",")]  # noqa: E203


def line_count(path):
    return len(path.read_text(errors="replace").splitlines())


def check_one(repo, known, path, end):
    """Return None when the cited path is fine, else a reason string."""
    on_disk = Path(repo) / path
    cands = [path] if on_disk.exists() else [k for k in known if k == path or k.endswith("/" + path)]
    if not cands:
        return ""
    counts = [line_count(Path(repo) / c) for c in cands if (Path(repo) / c).is_file()]
    if counts and all(end > n for n in counts):
        return f"line {end} > {max(counts)} lines"
    return None


def broken_citations(repo, known):
    out = []
    sibling_parent = Path(repo).resolve().parent
    for note in list_notes(repo):
        text = (Path(repo) / DOCS / note).read_text(errors="replace")
        for m in CITATION_RE.finditer(text):
            path = m.group(1)
            while path.startswith("./"):
                path = path[2:]
            ext = re.search(r"\.(\w+)$", path)
            if "://" in path or not ("/" in path or ext):
                continue
            if "/" not in path and ext.group(1).lower() in TLDS:
                continue
            seg = path.split("/")[0]
            if "/" in path and "{" not in seg and (sibling_parent / seg).is_dir() and not (Path(repo) / seg).is_dir():
                continue
            end = int(m.group(3) or m.group(2))
            for exp in expand_braces(path):
                reason = check_one(repo, known, exp, end)
                if reason is not None:
                    suffix = f" ({reason})" if reason else ""
                    out.append(f"{note}: {m.group(0).strip('`')}{suffix}")
                    break
    return out


def stale_statements(repo, days):
    stale, bad = [], []
    for note in list_notes(repo):
        for n, line in enumerate((Path(repo) / DOCS / note).read_text(errors="replace").splitlines(), 1):
            m = AS_OF_RE.search(line)
            if not m:
                continue
            try:
                age = (today() - datetime.date.fromisoformat(m.group(1))).days
            except ValueError:
                bad.append(f"{note}:{n}: {line.strip()}")
                continue
            if age > days:
                stale.append(f"{note}:{n}: {line.strip()}")
    return stale, bad


def group(title, lines, out):
    if lines:
        out.append(title)
        out.extend(f"  {line}" for line in lines)
        out.append("")


def hidden(rel):
    return any(part.startswith(".") or part == "__pycache__" for part in Path(rel).parts)


def matching_notes(m, paths):
    return [n for n, i in sorted(m["files"].items()) if not i.get("frozen") and any(covers_match(i.get("covers", []), p) for p in paths)]


def cmd_status(args):
    repo = args.repo
    m = load_manifest(repo)
    validate_covers(m)
    out = []
    if not is_git(repo):
        gen = datetime.date.fromisoformat(m["generated"])
        out.append(f"{repo} is not a git repo; using file modification times since {m['generated']}.")
        out.append("")
        newer = [r for r in sorted(known_files(repo, False)) if not hidden(r) and datetime.date.fromtimestamp((Path(repo) / r).stat().st_mtime) >= gen]
        group(f"Files modified after {m['generated']}:", newer, out)
        group("Broken citations:", broken_citations(repo, known_files(repo, False)), out)
        stale, bad = stale_statements(repo, args.stale_days)
        group("Stale time-bound statements:", stale, out)
        group("Bad dates:", bad, out)
        print("\n".join(out).rstrip())
        return 0

    head = head_sha(repo)
    top_base, top_warn = resolve_base(repo, m.get("sha"), m["generated"])
    how = "manifest sha" if top_warn is None else "fallback by manifest date"
    out.append(f"Base: {top_base[:8]} (from {how}), HEAD: {head[:8]}")
    if top_warn:
        out.append(top_warn)

    cache = {}
    affected = []
    for note, info in sorted(m["files"].items()):
        if info.get("frozen"):
            continue
        base, warn = resolve_base(repo, info.get("sha") or m.get("sha"), info.get("checked") or m["generated"])
        if warn:
            out.append(f"Note {note}: {warn}")
        if base not in cache:
            cache[base] = committed_changes(repo, base)
        hits = [d for d, paths in cache[base].items() if any(covers_match(info.get("covers", []), p) for p in paths)]
        if hits:
            affected.append(note)
            affected.extend(f"  {h}" for h in hits)
    out.append("")

    top_changes = cache.get(top_base) or committed_changes(repo, top_base)
    out.append(f"Changed files since base: {len(top_changes)}")
    out.append("")
    group("Affected notes:", affected, out)
    group("Uncovered changes:", [d for d, paths in top_changes.items() if not matching_notes(m, paths)], out)
    if not args.committed:
        unc = [f"{d}: {', '.join(matching_notes(m, paths)) or 'no note'}" for d, paths in worktree_changes(repo).items()]
        group("Uncommitted changes (not stamped):", unc, out)
    group("Broken citations:", broken_citations(repo, known_files(repo, True)), out)
    stale, bad = stale_statements(repo, args.stale_days)
    group("Stale time-bound statements:", stale, out)
    group("Bad dates:", bad, out)
    print("\n".join(out).rstrip())
    return 0


def get_note(m, note):
    info = m["files"].get(note)
    if info is None:
        raise DocsError(f"note not in manifest: {note}")
    if info.get("frozen"):
        raise DocsError(f"note is frozen: {note}")
    return info


def cmd_diff(args):
    repo = args.repo
    m = load_manifest(repo)
    info = get_note(m, args.note)
    if not info.get("covers"):
        raise DocsError(f"note has no covers: {args.note}")
    validate_covers(m, args.note)
    if not is_git(repo):
        raise DocsError("not a git repo; cannot diff")
    base, warn = resolve_base(repo, info.get("sha") or m.get("sha"), info.get("checked") or m["generated"])
    if warn:
        print(warn, file=sys.stderr)
    specs = [f":(glob){c}" for c in info["covers"]]
    print(git(repo, "diff", base, "--", *specs).stdout, end="")
    untracked = [p for p in split_z(git(repo, "ls-files", "--others", "--exclude-standard", "-z").stdout) if covers_match(info["covers"], p)]
    if untracked:
        print("Untracked files matching covers:")
        print("\n".join(f"  {p}" for p in untracked))
    return 0


def set_header(path, header):
    lines = path.read_text().split("\n")
    trailing = lines[-1] == ""
    if trailing:
        lines.pop()
    for i, line in enumerate(lines):
        if HEADER_RE.match(line):
            lines[i] = header
            break
    else:
        h1 = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
        if h1 is None:
            lines[0:0] = [header, ""]
        else:
            at = h1 + 1
            tail = lines[at:]
            lines[at:] = ["", header] + ([] if tail and tail[0] == "" else [""]) + tail
    path.write_text("\n".join(lines) + ("\n" if trailing else ""))


def cmd_stamp(args):
    repo = args.repo
    m = load_manifest(repo)
    git_mode = is_git(repo)
    stamp_all = not args.notes
    names = [n for n, i in m["files"].items() if not i.get("frozen")] if stamp_all else args.notes
    for n in names:
        get_note(m, n)
    date = today().isoformat()
    sha, branch = (head_sha(repo), branch_name(repo)) if git_mode else (None, None)
    header = f"Checked {date} against `{branch}` (`{sha[:8]}`)." if git_mode else f"Checked {date} (not a git repo)."
    targets = list(names)
    for n in names:
        if git_mode:
            m["files"][n]["sha"] = sha
        m["files"][n]["checked"] = date
    if stamp_all:
        m["generated"] = date
        if git_mode:
            m.update({"sha": sha, "branch": branch})
        targets.append("README.md")
    for n in targets:
        p = Path(repo) / DOCS / n
        if p.exists():
            set_header(p, header)
        elif not stamp_all:
            raise DocsError(f"note file missing: {n}")
    save_manifest(repo, m)
    print(f"Stamped {len(names)} note(s)" + (f" at {sha[:8]}." if git_mode else "."))
    return 0


def cmd_init(args):
    repo = args.repo
    if (Path(repo) / MANIFEST).exists() and not args.force:
        raise DocsError(f"{MANIFEST} already exists; use --force to overwrite")
    if not (Path(repo) / DOCS).is_dir():
        raise DocsError(f"no {DOCS}/ folder in {repo}")
    files = {}
    for n in list_notes(repo):
        if n.startswith("investigations/"):
            files[n] = {"covers": [], "frozen": True}
        else:
            # No sha: status falls back to the last commit before the note's own file date.
            files[n] = {"covers": [], "checked": datetime.date.fromtimestamp((Path(repo) / DOCS / n).stat().st_mtime).isoformat()}
    git_mode = is_git(repo)
    save_manifest(
        repo,
        {
            "branch": branch_name(repo) if git_mode else None,
            "sha": None,
            "generated": min((i["checked"] for i in files.values() if "checked" in i), default=today().isoformat()),
            "files": files,
        },
    )
    print(f"Wrote {MANIFEST} with {len(files)} note(s).")
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="docs_state.py",
        description=__doc__,
        epilog="covers patterns support only '*' (one path segment), '**' (zero or more segments) and bare paths (a file or a directory prefix).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("repo")
    s.add_argument("--stale-days", type=int, default=30)
    s.add_argument("--committed", action="store_true", help="omit the uncommitted changes group")
    s.set_defaults(fn=cmd_status)
    d = sub.add_parser("diff")
    d.add_argument("repo")
    d.add_argument("note")
    d.set_defaults(fn=cmd_diff)
    st = sub.add_parser("stamp")
    st.add_argument("repo")
    st.add_argument("notes", nargs="*")
    st.set_defaults(fn=cmd_stamp)
    i = sub.add_parser("init-manifest")
    i.add_argument("repo")
    i.add_argument("--force", action="store_true")
    i.set_defaults(fn=cmd_init)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except DocsError as e:
        print(f"error: {e}", file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
