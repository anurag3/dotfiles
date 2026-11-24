import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import docs_state  # noqa: E402

TODAY = "2026-11-23"


def git(repo, *args, env=None):
    cmd = ["git", "-c", "user.name=t", "-c", "user.email=t@t.test", *args]
    return subprocess.run(cmd, cwd=repo, check=True, capture_output=True, text=True, env={**os.environ, **(env or {})}).stdout.strip()


def write(repo, rel, text):
    p = Path(repo) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def commit_all(repo, msg="c", date=None):
    git(repo, "add", "-A", "--", ".", ":(exclude).docs")
    env = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date} if date else None
    git(repo, "commit", "-q", "-m", msg, env=env)
    return git(repo, "rev-parse", "HEAD")


def read_manifest(repo):
    return json.loads((Path(repo) / ".docs/manifest.json").read_text())


def write_manifest(repo, data):
    write(repo, ".docs/manifest.json", json.dumps(data, indent=2) + "\n")


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setenv("DOCS_STATE_TODAY", TODAY)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    # The user's global ignore file lists .docs/. Disable it so the tests prove the code filters .docs/ itself.
    git(r, "config", "core.excludesFile", "/dev/null")
    write(r, "databricks_dbt.yml", "a: 1\n")
    write(r, "macros/operations/clone.sql", "x\n")
    write(r, "models/a.sql", "1\n2\n3\n")
    write(r, "models/sub/b.sql", "1\n2\n")
    write(r, "README.md", "hi\n")
    sha = commit_all(r, "init")
    write(r, ".docs/README.md", "# Notes\n\nindex\n")
    write(r, ".docs/containment-flow.md", "# Containment\n\nbody\n")
    write(r, ".docs/models.md", "# Models\n\nbody\n")
    write(r, ".docs/ops.md", "# Ops\n\nbody\n")
    write(r, ".docs/investigations/old.md", "# Old\n")
    write_manifest(
        r,
        {
            "branch": "main",
            "sha": sha,
            "generated": "2026-11-01",
            "files": {
                "containment-flow.md": {"covers": ["databricks_dbt.yml", "macros/operations/**"], "sha": sha, "checked": "2026-11-01"},
                "models.md": {"covers": ["models/*.sql"]},
                "ops.md": {"covers": ["macros/operations"]},
                "investigations/old.md": {"covers": ["models/**"], "frozen": True},
            },
        },
    )
    return r


def run(capsys, *args):
    code = docs_state.main([str(a) for a in args])
    cap = capsys.readouterr()
    return code, cap.out + cap.err


def section(out, heading):
    lines = out.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(heading):
            body = []
            rest = lines[i + 1 :]  # noqa: E203
            for nxt in rest:
                if not nxt.strip():
                    break
                body.append(nxt)
            return "\n".join(body)
    return None


def test_glob_patterns():
    rx = docs_state.glob_to_regex
    assert re.match(rx("**/x.sql"), "x.sql")
    assert re.match(rx("**/x.sql"), "a/b/x.sql")
    assert re.match(rx("models/*.sql"), "models/a.sql")
    assert not re.match(rx("models/*.sql"), "models/sub/b.sql")
    assert re.match(rx("models/**"), "models/sub/b.sql")
    assert re.match(rx("a/**/z.py"), "a/z.py")
    assert re.match(rx("a/**/z.py"), "a/b/c/z.py")
    assert re.match(rx("macros/operations"), "macros/operations/x/y.sql")
    assert re.match(rx("macros/operations"), "macros/operations")
    assert not re.match(rx("macros/operations"), "macros/operations2/x.sql")


def test_changed_covered_file_marks_note_affected(repo, capsys):
    write(repo, "databricks_dbt.yml", "a: 2\n")
    commit_all(repo)
    code, out = run(capsys, "status", repo)
    assert code == 0
    affected = section(out, "Affected notes")
    assert "containment-flow.md" in affected
    assert "databricks_dbt.yml" in affected
    assert "models.md" not in affected
    assert out.splitlines()[0].startswith("Base:")


def test_uncovered_change(repo, capsys):
    write(repo, "README.md", "changed\n")
    commit_all(repo)
    _, out = run(capsys, "status", repo)
    assert "README.md" in section(out, "Uncovered changes")
    assert section(out, "Affected notes") is None


def test_star_double_star_and_prefix(repo, capsys):
    write(repo, "macros/operations/sub/deep.sql", "d\n")
    write(repo, "models/sub/b.sql", "changed\n")
    commit_all(repo)
    _, out = run(capsys, "status", repo)
    affected = section(out, "Affected notes")
    assert "containment-flow.md" in affected
    assert "ops.md" in affected
    assert "models.md" not in affected
    assert "models/sub/b.sql" in section(out, "Uncovered changes")


def test_rename_old_arrow_new_and_old_path_match(repo, capsys):
    (repo / "deploy").mkdir()
    git(repo, "mv", "databricks_dbt.yml", "deploy/databricks_dbt.yml")
    commit_all(repo)
    _, out = run(capsys, "status", repo)
    assert "databricks_dbt.yml -> deploy/databricks_dbt.yml" in out
    assert "containment-flow.md" in section(out, "Affected notes")


def test_deleted_file_breaks_citation_and_suffix_is_lenient(repo, capsys):
    write(repo, ".docs/models.md", "# Models\n\nSee `models/a.sql:1-3` and `sub/b.sql:2` and `sub/gone.sql:1`.\n")
    _, out = run(capsys, "status", repo)
    broken = section(out, "Broken citations")
    assert "sub/gone.sql:1" in broken
    assert "models/a.sql" not in broken
    assert "sub/b.sql:2" not in broken
    git(repo, "rm", "-q", "models/a.sql")
    commit_all(repo)
    _, out = run(capsys, "status", repo)
    assert "models.md: models/a.sql:1-3" in section(out, "Broken citations")


def test_docs_changes_ignored(repo, capsys):
    write(repo, ".docs/models.md", "# Models\n\nedited\n")
    write(repo, ".docs/new.md", "# New\n")
    _, out = run(capsys, "status", repo)
    assert ".docs/" not in out
    assert section(out, "Uncovered changes") is None


def test_frozen_note_never_affected_or_stamped(repo, capsys):
    write(repo, "models/a.sql", "edited\n")
    _, out = run(capsys, "status", repo)
    assert "old.md" not in out
    code, out = run(capsys, "stamp", repo, "investigations/old.md")
    assert code == 1
    assert "frozen" in out
    run(capsys, "stamp", repo)
    assert "sha" not in read_manifest(repo)["files"]["investigations/old.md"]


def test_recorded_sha_missing_uses_fallback(repo, capsys):
    m = read_manifest(repo)
    m["sha"] = "f" * 40
    m["generated"] = TODAY
    write_manifest(repo, m)
    code, out = run(capsys, "status", repo)
    assert code == 0
    assert "missing" in out
    assert "fallback" in out


def test_missing_manifest_exits_2(repo, capsys):
    (repo / ".docs/manifest.json").unlink()
    code, out = run(capsys, "status", repo)
    assert code == 2
    assert "init-manifest" in out


def test_stale_as_of(repo, capsys):
    write(repo, ".docs/models.md", "# Models\n\nok as of 2026-11-20\nold as of 2026-01-01 here\n")
    _, out = run(capsys, "status", repo)
    stale = section(out, "Stale time-bound statements")
    assert "models.md:4:" in stale
    assert "2026-11-20" not in stale
    _, out = run(capsys, "status", repo, "--stale-days", "400")
    assert section(out, "Stale time-bound statements") is None


def test_stamp_inserts_and_replaces_header(repo, capsys):
    head = git(repo, "rev-parse", "HEAD")
    write(repo, ".docs/models.md", "# Models\n\nChecked 2026-01-01 against `old` (`abcdef12`).\n\nbody\n")
    code, _ = run(capsys, "stamp", repo, "containment-flow.md", "models.md")
    assert code == 0
    cf = (repo / ".docs/containment-flow.md").read_text().splitlines()
    assert cf[:4] == ["# Containment", "", f"Checked {TODAY} against `main` (`{head[:8]}`).", ""]
    md = (repo / ".docs/models.md").read_text()
    assert md.count("Checked ") == 1
    assert f"Checked {TODAY} against `main` (`{head[:8]}`)." in md
    m = read_manifest(repo)
    assert m["files"]["models.md"]["sha"] == head
    assert m["files"]["models.md"]["checked"] == TODAY
    assert m["generated"] == "2026-11-01"
    assert "Checked" not in (repo / ".docs/README.md").read_text()


def test_stamp_all_updates_top_level_and_readme(repo, capsys):
    write(repo, "README.md", "changed\n")
    head = commit_all(repo)
    code, _ = run(capsys, "stamp", repo)
    assert code == 0
    m = read_manifest(repo)
    assert (m["sha"], m["branch"], m["generated"]) == (head, "main", TODAY)
    assert m["files"]["ops.md"]["sha"] == head
    assert f"Checked {TODAY} against `main`" in (repo / ".docs/README.md").read_text()
    assert (repo / ".docs/manifest.json").read_text().endswith("}\n")


def test_stamp_header_without_h1_goes_on_top(repo, capsys):
    write(repo, ".docs/ops.md", "plain text\n")
    run(capsys, "stamp", repo, "ops.md")
    lines = (repo / ".docs/ops.md").read_text().splitlines()
    assert lines[0].startswith("Checked ")
    assert lines[1] == ""
    assert lines[2] == "plain text"


def test_init_manifest(repo, capsys):
    (repo / ".docs/manifest.json").unlink()
    before = (repo / ".docs/models.md").read_text()
    for n in repo.glob(".docs/**/*.md"):
        set_mtime(n, TODAY)
    code, _ = run(capsys, "init-manifest", repo)
    assert code == 0
    m = read_manifest(repo)
    assert m["files"]["investigations/old.md"] == {"covers": [], "frozen": True}
    assert m["files"]["models.md"] == {"covers": [], "checked": TODAY}
    assert m["sha"] is None
    assert m["generated"] == TODAY
    assert (repo / ".docs/models.md").read_text() == before
    code, out = run(capsys, "init-manifest", repo)
    assert code == 1
    assert "--force" in out
    code, _ = run(capsys, "init-manifest", repo, "--force")
    assert code == 0


def set_mtime(path, day):
    ts = datetime.datetime.fromisoformat(f"{day}T12:00:00").timestamp()
    os.utime(path, (ts, ts))


def old_notes_repo(repo):
    """models.md is dated 2026-10-01. The init commit is 2026-09-20. A later commit on 2026-10-15 changes models/a.sql."""
    (repo / ".docs/manifest.json").unlink()
    git(repo, "commit", "-q", "--amend", "--no-edit", "--date", "2026-09-20T12:00:00", env={"GIT_COMMITTER_DATE": "2026-09-20T12:00:00"})
    write(repo, "models/a.sql", "changed\n")
    commit_all(repo, "late", "2026-10-15T12:00:00")
    set_mtime(repo / ".docs/models.md", "2026-10-01")
    set_mtime(repo / ".docs/ops.md", "2026-10-05")


def test_init_manifest_sets_checked_from_mtime(repo, capsys):
    old_notes_repo(repo)
    run(capsys, "init-manifest", repo)
    m = read_manifest(repo)
    assert m["files"]["models.md"] == {"covers": [], "checked": "2026-10-01"}
    assert m["files"]["ops.md"]["checked"] == "2026-10-05"
    assert m["files"]["investigations/old.md"] == {"covers": [], "frozen": True}
    assert "sha" not in m["files"]["models.md"]
    assert m["sha"] is None
    assert m["generated"] == "2026-10-01"


def test_init_manifest_generated_is_today_without_live_notes(tmp_path, capsys):
    write(tmp_path, ".docs/investigations/x.md", "# X\n")
    run(capsys, "init-manifest", tmp_path)
    m = read_manifest(tmp_path)
    assert m["generated"] == TODAY
    assert m["sha"] is None
    assert m["branch"] is None


def test_init_manifest_then_status_shows_drift_since_note_date(repo, capsys):
    old_notes_repo(repo)
    run(capsys, "init-manifest", repo)
    m = read_manifest(repo)
    m["files"]["models.md"]["covers"] = ["models/*.sql"]
    write_manifest(repo, m)
    _, out = run(capsys, "status", repo, "--committed")
    assert "models/a.sql" in section(out, "Affected notes")
    assert "No recorded sha" in out


def test_init_manifest_then_stamp_clears_drift(repo, capsys):
    old_notes_repo(repo)
    run(capsys, "init-manifest", repo)
    m = read_manifest(repo)
    m["files"]["models.md"]["covers"] = ["models/*.sql"]
    write_manifest(repo, m)
    run(capsys, "stamp", repo, "models.md")
    _, out = run(capsys, "status", repo, "--committed")
    assert "models.md" not in (section(out, "Affected notes") or "")


def test_diff_prints_and_errors(repo, capsys):
    write(repo, "databricks_dbt.yml", "a: 99\n")
    commit_all(repo)
    code, out = run(capsys, "diff", repo, "containment-flow.md")
    assert code == 0
    assert "+a: 99" in out
    code, out = run(capsys, "diff", repo, "investigations/old.md")
    assert code == 1
    assert "frozen" in out
    write_manifest(repo, {**read_manifest(repo), "files": {"x.md": {"covers": []}}})
    code, out = run(capsys, "diff", repo, "x.md")
    assert code == 1
    assert "covers" in out


def test_non_git_folder(tmp_path, capsys):
    d = tmp_path / "plain"
    write(d, "old.txt", "o\n")
    write(d, "new.txt", "n\n")
    write(d, ".docs/a.md", "# A\n\nsee `old.txt:1` and `missing.txt:3`\n")
    write_manifest(d, {"branch": None, "sha": None, "generated": "2026-11-01", "files": {"a.md": {"covers": []}}})
    os.utime(d / "old.txt", (1_700_000_000, 1_700_000_000))
    os.utime(d / "new.txt", (1_800_000_000, 1_800_000_000))
    code, out = run(capsys, "status", d)
    assert code == 0
    assert "not a git repo" in out
    changed = section(out, "Files modified after")
    assert "new.txt" in changed
    assert "old.txt" not in changed
    broken = section(out, "Broken citations")
    assert "missing.txt:3" in broken
    assert "old.txt" not in broken


UNC = "Uncommitted changes (not stamped)"


def test_uncommitted_split_from_committed(repo, capsys):
    write(repo, "models/a.sql", "edited\n")
    write(repo, "macros/operations/newdir/x.sql", "n\n")
    write(repo, "README.md", "dirty\n")
    _, out = run(capsys, "status", repo)
    assert section(out, "Affected notes") is None
    assert section(out, "Uncovered changes") is None
    unc = section(out, UNC)
    assert "models/a.sql: models.md" in unc
    assert "macros/operations/newdir/: " in unc
    assert "containment-flow.md" in unc and "ops.md" in unc
    assert "README.md: no note" in unc
    _, out = run(capsys, "status", repo, "--committed")
    assert section(out, UNC) is None


def test_dirty_tree_after_stamp_has_no_affected(repo, capsys):
    run(capsys, "stamp", repo)
    write(repo, "models/a.sql", "edited\n")
    _, out = run(capsys, "status", repo)
    assert section(out, "Affected notes") is None
    assert "models/a.sql" in section(out, UNC)


def dated_repo(tmp_path):
    r = tmp_path / "dated"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "core.excludesFile", "/dev/null")
    write(r, "models/a.sql", "1\n")
    commit_all(r, "one", "2026-10-31T12:00:00")
    write(r, "models/a.sql", "2\n")
    commit_all(r, "two", "2026-11-01T10:00:00")
    write(r, ".docs/models.md", "# M\n")
    write_manifest(r, {"branch": "main", "sha": "f" * 40, "generated": "2026-11-01", "files": {"models.md": {"covers": ["models/*.sql"]}}})
    return r


def test_fallback_errs_toward_more_changes_and_warns_per_note(tmp_path, capsys):
    r = dated_repo(tmp_path)
    _, out = run(capsys, "status", r)
    assert "models/a.sql" in section(out, "Affected notes")
    assert any(line.startswith("Note models.md: ") and "missing" in line for line in out.splitlines())


def test_note_with_missing_own_sha_warns(repo, capsys):
    m = read_manifest(repo)
    m["files"]["containment-flow.md"]["sha"] = "e" * 40
    write_manifest(repo, m)
    _, out = run(capsys, "status", repo)
    assert any(line.startswith("Note containment-flow.md: ") for line in out.splitlines())
    assert not any(line.startswith("Note models.md: ") for line in out.splitlines())


def test_diff_includes_worktree_untracked_and_fallback_warning(repo, capsys):
    write(repo, "databricks_dbt.yml", "a: 5\n")
    write(repo, "macros/operations/untracked.sql", "u\n")
    code, out = run(capsys, "diff", repo, "containment-flow.md")
    assert code == 0
    assert "+a: 5" in out
    assert "macros/operations/untracked.sql" in out.split("Untracked")[1]
    m = read_manifest(repo)
    m["files"]["containment-flow.md"]["sha"] = "e" * 40
    write_manifest(repo, m)
    _, out = run(capsys, "diff", repo, "containment-flow.md")
    assert "missing" in out


def test_citation_ignored_but_present_ok(repo, capsys):
    (repo / ".git/info/exclude").write_text("local.cfg\n")
    write(repo, "local.cfg", "x\n")
    write(repo, ".docs/models.md", "# M\n\n`local.cfg:1`\n")
    _, out = run(capsys, "status", repo)
    assert section(out, "Broken citations") is None


def test_citation_false_positives_and_braces(repo, capsys):
    (repo.parent / "sibling").mkdir()
    write(
        repo,
        ".docs/models.md",
        "# M\n\n`./models/a.sql:1` `models/{a,sub/b}.sql:1` `models/{a,zzz}.sql:1` `sibling/foo.py:3` `host.com:443` `models/nope.sql:4`\n",
    )
    _, out = run(capsys, "status", repo)
    broken = section(out, "Broken citations")
    assert "models/{a,zzz}.sql:1" in broken
    assert "models/nope.sql:4" in broken
    for ok in ("./models/a.sql", "models/{a,sub/b}.sql:1", "sibling", "host.com"):
        assert ok not in broken


def test_citation_line_drift(repo, capsys):
    write(repo, ".docs/models.md", "# M\n\n`models/a.sql:2-9` `models/a.sql:3`\n")
    _, out = run(capsys, "status", repo)
    broken = section(out, "Broken citations")
    assert "models/a.sql:2-9" in broken and "line 9 > 3 lines" in broken
    assert "models/a.sql:3`" not in broken and broken.count("models/a.sql") == 1


def test_bad_dates_and_case_insensitive(repo, capsys):
    write(repo, ".docs/models.md", "# M\n\nx as of 2026-13-45\nAs Of 2026-01-01 old\n")
    code, out = run(capsys, "status", repo)
    assert code == 0
    assert "models.md:3:" in section(out, "Bad dates")
    assert "models.md:4:" in section(out, "Stale time-bound statements")


def test_corrupt_manifest_errors_cleanly(repo, capsys):
    (repo / ".docs/manifest.json").write_text("{not json")
    code, out = run(capsys, "status", repo)
    assert code == 1 and out.startswith("error:")
    write_manifest(repo, {"files": {}})
    code, out = run(capsys, "status", repo)
    assert code == 1 and "generated" in out


def test_non_git_boundary_dotfiles_and_stamp(tmp_path, capsys):
    import datetime

    d = tmp_path / "plain"
    write(d, "edge.txt", "e\n")
    write(d, ".hidden", "h\n")
    write(d, "__pycache__/x.pyc", "p\n")
    write(d, ".cache/y", "y\n")
    write(d, ".docs/a.md", "# A\n\nbody\n")
    write_manifest(d, {"branch": None, "sha": None, "generated": "2026-11-01", "files": {"a.md": {"covers": []}}})
    ts = datetime.datetime(2026, 11, 1, 12).timestamp()
    for rel in ("edge.txt", ".hidden", "__pycache__/x.pyc", ".cache/y"):
        os.utime(d / rel, (ts, ts))
    _, out = run(capsys, "status", d)
    changed = section(out, "Files modified after")
    assert "edge.txt" in changed
    assert ".hidden" not in changed and "pycache" not in changed and ".cache" not in changed
    for _ in range(2):
        code, _ = run(capsys, "stamp", d)
        assert code == 0
    text = (d / ".docs/a.md").read_text()
    assert text.count(f"Checked {TODAY} (not a git repo).") == 1
    m = read_manifest(d)
    assert m["sha"] is None and m["branch"] is None
    assert m["generated"] == TODAY and m["files"]["a.md"]["checked"] == TODAY
    assert "sha" not in m["files"]["a.md"]


def test_unsupported_glob_chars_rejected_and_help(repo, capsys):
    m = read_manifest(repo)
    m["files"]["models.md"]["covers"] = ["models/[ab].sql"]
    write_manifest(repo, m)
    code, out = run(capsys, "status", repo)
    assert code == 1 and "not supported" in out
    code, out = run(capsys, "diff", repo, "models.md")
    assert code == 1 and "not supported" in out
    assert "**" in docs_state.build_parser().format_help()


def test_error_message_is_plain(repo, capsys):
    code, out = run(capsys, "diff", repo, "nope.md")
    assert code == 1 and out.strip() == "error: note not in manifest: nope.md"
