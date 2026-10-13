#!/usr/bin/env python3
"""Helper CLI for the github-pages-publish skill. Standard library only.

Subcommands (each prints one JSON object on stdout; errors go to stderr):
  log-init   create the run log and print its path
  log        append one step entry to the run log
  preflight  read-only checks: tools, git identity, gh auth scopes, target repo, Pages config, workflows
  check-site validate a content folder (index.html, sizes, local links); optionally fix root links
  sync-site  copy content into the repo's site folder with replace semantics and a manifest
  workflow   create or update the Pages deploy workflow; report conflicting workflows
  configure  make sure Pages exists and deploys from GitHub Actions (build_type=workflow)
  verify     wait for the deploy run, then prove the live site serves the committed bytes

Exit codes: 0 ok, 1 check failed, 2 bad input or missing prerequisite, 3 conflict needing the user.
"""
import argparse
import base64
import datetime as dt
import hashlib
import html.parser
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(SKILL_DIR, "assets", "pages-workflow.yml")
MANIFEST_REL = ".github/pages-publish.json"
MANAGED_MARK = "Managed by the github-pages-publish skill"
# Known-good majors (2026-10); `workflow` resolves the latest release at run time.
FALLBACK_ACTIONS = {"checkout": "v7", "configure-pages": "v6",
                    "upload-pages-artifact": "v5", "deploy-pages": "v5"}
STATIC_ACTIONS = {"actions/" + k for k in FALLBACK_ACTIONS}
MAX_FILE = 100 * 1024 * 1024        # git hosting hard limit per file
MAX_SITE = 1024 * 1024 * 1024       # GitHub Pages published-site limit
KEEP_IN_SITE_DIR = {"CNAME"}


def die(code, msg, fix=None):
    sys.stderr.write("error: %s\n" % msg)
    if fix:
        sys.stderr.write("fix: %s\n" % fix)
    sys.exit(code)


def emit(obj, code=0):
    print(json.dumps(obj, indent=2, sort_keys=True))
    sys.exit(code)


def run(cmd, check=False, cwd=None, binary=False):
    try:
        p = subprocess.run(cmd, capture_output=True, text=not binary, cwd=cwd)
    except FileNotFoundError:
        die(2, "command not found: %s" % cmd[0], "install %s and re-run" % cmd[0])
    if check and p.returncode != 0:
        err = p.stderr if not binary else p.stderr.decode("utf-8", "replace")
        die(2, "`%s` failed (exit %d): %s" % (" ".join(cmd), p.returncode, err.strip()[:400]))
    return p


def gh_json(args):
    """Run a gh command expected to print JSON. Returns (data or None, stderr)."""
    p = run(["gh"] + args)
    if p.returncode != 0:
        return None, p.stderr.strip()
    try:
        return json.loads(p.stdout or "null"), ""
    except ValueError:
        return None, "unparseable gh output"


def parse_repo(spec, default_owner):
    s = spec.strip()
    s = re.sub(r"^(https?://|git@)github\.com[/:]", "", s)
    s = re.sub(r"\.git$", "", s).strip("/")
    parts = s.split("/")
    if len(parts) == 1 and parts[0]:
        if not default_owner:
            die(2, "repo '%s' has no owner and the gh user is unknown" % spec,
                "pass owner/name, or log in with `gh auth login`")
        parts = [default_owner, parts[0]]
    if len(parts) != 2 or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) for p in parts):
        die(2, "cannot parse repo '%s'" % spec, "use owner/name or https://github.com/owner/name")
    return parts[0], parts[1]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def list_files(root, skip_hidden=True):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        if skip_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fn in filenames:
            if skip_hidden and fn.startswith("."):
                continue
            out.append(os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/"))
    return sorted(out)


def tracked_files(repo, site_dir):
    """Files git tracks under site_dir, relative to site_dir (hidden ones skipped, as Pages skips them)."""
    spec = "." if site_dir == "." else site_dir
    p = run(["git", "-C", repo, "ls-files", "-z", "--", spec], check=True)
    out = []
    for f in p.stdout.split("\0"):
        if not f:
            continue
        rel = f if site_dir == "." else posixpath.relpath(f, site_dir)
        if not any(part.startswith(".") for part in rel.split("/")):
            out.append(rel)
    return sorted(out)


def safe_site_dir(repo, site_dir):
    """Normalize a site folder and refuse anything outside the repo or inside .git/.github."""
    norm = posixpath.normpath((site_dir or ".").strip().strip("/") or ".")
    dest = os.path.realpath(os.path.join(repo, norm))
    if os.path.commonpath([os.path.realpath(repo), dest]) != os.path.realpath(repo) \
            or norm.startswith("..") or norm.split("/")[0] in (".git", ".github"):
        die(2, "site dir '%s' is not allowed" % site_dir, "use '.', 'docs', or another plain folder inside the repo")
    return norm, os.path.join(repo, norm)


def append_paths(out, paths):
    """Append repo-relative paths for `git add/commit --pathspec-from-file` (use GIT_LITERAL_PATHSPECS=1)."""
    if out and paths:
        with open(out, "a") as f:
            f.write("".join(p + "\n" for p in paths))


# ---------------------------------------------------------------- log

def cmd_log_init(a):
    os.makedirs(a.dir, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.abspath(os.path.join(a.dir, "run-%s.md" % stamp))
    with open(path, "w") as f:
        f.write("# github-pages-publish run %s\n\n" % stamp)
        f.write("Request: %s\n\n| time (UTC) | step | status | detail | command |\n|---|---|---|---|---|\n"
                % (a.request or "(not recorded)"))
    excluded = False
    top = run(["git", "rev-parse", "--show-toplevel"], cwd=a.dir)
    already = top.returncode == 0 and run(["git", "check-ignore", "-q", path], cwd=a.dir).returncode == 0
    if already:
        excluded = True
    elif top.returncode == 0:
        excl = os.path.join(top.stdout.strip(), ".git", "info", "exclude")
        rel = os.path.relpath(os.path.abspath(a.dir), top.stdout.strip()).replace(os.sep, "/") + "/"
        try:
            existing = open(excl).read() if os.path.exists(excl) else ""
            if rel not in existing.split("\n"):
                with open(excl, "a") as f:
                    f.write("\n" + rel + "\n")
            excluded = True
        except OSError:
            pass
    emit({"log": path, "git_excluded": excluded})


def cmd_log(a):
    if not os.path.exists(a.file):
        die(2, "log file %s does not exist" % a.file, "run `log-init` first and pass its path")
    cell = lambda s: (s or "").replace("|", "\\|").replace("\n", " ")
    now = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    with open(a.file, "a") as f:
        f.write("| %s | %s | %s | %s | %s |\n" % (now, cell(a.step), a.status.upper(), cell(a.msg),
                                                  ("`%s`" % cell(a.cmd)) if a.cmd else ""))
    emit({"logged": True, "file": a.file})


# ---------------------------------------------------------------- preflight

def gh_scopes():
    p = run(["gh", "api", "-i", "user"])
    if p.returncode != 0:
        return None, None
    login, scopes = None, None
    head, _, body = p.stdout.partition("\r\n\r\n")
    if not body:
        head, _, body = p.stdout.partition("\n\n")
    for line in head.splitlines():
        if line.lower().startswith("x-oauth-scopes:"):
            scopes = [s.strip() for s in line.split(":", 1)[1].split(",") if s.strip()]
    try:
        login = json.loads(body).get("login")
    except ValueError:
        pass
    return login, scopes


def classify_workflow(text):
    """A Pages workflow is static only when it uses nothing but the four standard actions and runs no commands."""
    t = text or ""
    uses = set(re.findall(r"uses:\s*['\"]?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", t))
    return {
        "managed": MANAGED_MARK in t,
        "deploys_pages": "actions/deploy-pages" in uses,
        "pushes_branch": bool(re.search(r"peaceiris/actions-gh-pages|JamesIves/github-pages-deploy-action", t)),
        "builds": bool(re.search(r"^\s*-?\s*run:", t, re.M)) or bool(uses - STATIC_ACTIONS),
    }


def prefer_https(url):
    """Pages reports http:// when HTTPS is not enforced; use https:// when the host serves it."""
    if url.startswith("http://") and fetch("https://%s/" % urllib.parse.urlsplit(url).netloc)[0] is not None:
        return "https://" + url[len("http://"):]
    return url


def expected_url(owner, name, user_site, pages):
    """Where the site will be served. A project site inherits the custom domain of the owner's user site."""
    if pages.get("html_url"):
        return prefer_https(pages["html_url"])
    if user_site:
        return "https://%s.github.io/" % owner.lower()
    home, _ = gh_json(["api", "repos/%s/%s.github.io/pages" % (owner, owner)])
    if home and home.get("cname"):
        return prefer_https("http://%s/%s/" % (home["cname"], name))
    return "https://%s.github.io/%s/" % (owner.lower(), name)


def cmd_preflight(a):
    res = {"blockers": [], "gates": [], "warnings": []}
    for tool in ("gh", "git"):
        if not shutil.which(tool):
            die(2, "%s is not installed" % tool,
                "install it (https://cli.github.com for gh) and re-run preflight")
    for key in ("user.name", "user.email"):
        if not run(["git", "config", key]).stdout.strip():
            res["blockers"].append({"id": "git-identity", "why": "git %s is not set, so the commit would fail" % key,
                                    "fix": "git config --global %s '<value>'" % key})
    login, scopes = gh_scopes()
    if not login:
        die(2, "gh is not authenticated", "run `gh auth login`, then re-run preflight")
    res["auth"] = {"user": login, "scopes": scopes,
                   "git_protocol": (run(["gh", "config", "get", "git_protocol", "-h", "github.com"]).stdout.strip()
                                    or run(["gh", "config", "get", "git_protocol"]).stdout.strip() or "https")}
    res["scope_gaps"] = []
    if scopes is not None:
        if "repo" not in scopes:
            res["blockers"].append({"id": "scope-repo", "fix": "gh auth refresh -h github.com -s repo",
                                    "why": "pushing and configuring Pages need the 'repo' token scope"})
        if "workflow" not in scopes:
            # Only blocks a run that creates or changes a workflow file; the skill decides after `workflow`.
            res["scope_gaps"].append({"id": "scope-workflow", "fix": "gh auth refresh -h github.com -s workflow",
                                      "why": "GitHub rejects a push that adds or edits .github/workflows/* without it"})
    else:
        res["warnings"].append("token scopes not reported (fine-grained token or GITHUB_TOKEN); "
                               "it needs Contents, Pages, Workflows and Administration write")
    owner, name = parse_repo(a.repo, login)
    full = "%s/%s" % (owner, name)
    res["target"] = {"owner": owner, "name": name, "full": full,
                     "user_site": name.lower() == "%s.github.io" % owner.lower()}
    info, err = gh_json(["repo", "view", full, "--json",
                         "visibility,isArchived,isEmpty,isFork,viewerPermission,defaultBranchRef,url"])
    if info is None:
        if "Could not resolve" not in err and "not found" not in err.lower():
            die(2, "cannot read repo %s: %s" % (full, err[:300]), "check network and gh auth, then retry")
        res["target"].update({"exists": False, "default_branch": "main", "empty": True})
        res["pages"] = {"exists": False}
        res["workflows"] = []
        res["gates"].append({"id": "create-repo", "ask": "Create public repo %s?" % full})
        if owner.lower() != login.lower():
            org, _ = gh_json(["api", "orgs/%s" % owner])
            if org is None:
                res["blockers"].append({"id": "owner-unknown",
                                        "why": "'%s' is neither you (%s) nor an org you can see" % (owner, login),
                                        "fix": "check the owner name"})
    else:
        branch = (info.get("defaultBranchRef") or {}).get("name") or "main"
        perm = info.get("viewerPermission") or "NONE"
        res["target"].update({"exists": True, "visibility": info.get("visibility"),
                              "archived": info.get("isArchived"), "empty": info.get("isEmpty"),
                              "fork": info.get("isFork"), "permission": perm, "default_branch": branch,
                              "url": info.get("url")})
        if info.get("isFork"):
            res["warnings"].append("forks keep Actions workflows off until enabled once in the repo's Actions tab")
        if info.get("isArchived"):
            res["blockers"].append({"id": "archived", "why": "%s is archived (read-only)" % full,
                                    "fix": "unarchive it in Settings, or pick another repo"})
        if perm not in ("ADMIN", "MAINTAIN", "WRITE"):
            res["blockers"].append({"id": "no-push", "why": "your permission on %s is %s" % (full, perm),
                                    "fix": "ask an admin for write access, or pick another repo"})
        if info.get("visibility") in ("PRIVATE", "INTERNAL"):
            res["gates"].append({"id": "private-repo",
                                 "ask": "%s is %s. Make it public?" % (full, info["visibility"].lower())})
        pages, _ = gh_json(["api", "repos/%s/pages" % full])
        res["pages"] = ({"exists": True, "build_type": pages.get("build_type"), "html_url": pages.get("html_url"),
                         "cname": pages.get("cname"), "source": pages.get("source")}
                        if pages else {"exists": False})
        src = (pages or {}).get("source") or {}
        res["pages"]["source_on_default_branch"] = bool(src) and src.get("branch") == branch
        if perm == "WRITE" and not (pages and pages.get("build_type") == "workflow"):
            res["blockers"].append({"id": "pages-admin",
                                    "why": "configuring Pages needs admin or maintain; you have write",
                                    "fix": "ask an admin to set Settings > Pages > Source to GitHub Actions"})
        actions, _ = gh_json(["api", "repos/%s/actions/permissions" % full])
        res["actions_enabled"] = actions.get("enabled") if actions else None
        if actions is not None and not actions.get("enabled"):
            res["gates"].append({"id": "enable-actions", "ask": "GitHub Actions is disabled on %s. Enable it?" % full})
        res["workflows"] = []
        listing, _ = gh_json(["api", "repos/%s/contents/.github/workflows?ref=%s" % (full, branch)])
        for item in listing if isinstance(listing, list) else []:
            if not re.search(r"\.ya?ml$", item.get("name", "")):
                continue
            blob, _ = gh_json(["api", item["url"].replace("https://api.github.com/", "")])
            text = base64.b64decode(blob["content"]).decode("utf-8", "replace") if blob and blob.get("content") else ""
            res["workflows"].append(dict(path=item["path"], **classify_workflow(text)))
    res["target"]["project_site"] = not res["target"]["user_site"] and not (res.get("pages") or {}).get("cname")
    res["target"]["expected_url"] = expected_url(owner, name, res["target"]["user_site"], res.get("pages") or {})
    top = run(["git", "rev-parse", "--show-toplevel"])
    local = {"in_git_repo": top.returncode == 0, "in_place": False}
    if top.returncode == 0:
        remote = run(["git", "remote", "get-url", "origin"]).stdout.strip()
        cur = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        m = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(\.git)?$", remote)
        same = bool(m) and (m.group(1).lower(), m.group(2).lower()) == (owner.lower(), name.lower())
        ahead = run(["git", "rev-list", "--count", "@{u}..HEAD"])
        unpushed = None if ahead.returncode != 0 else int(ahead.stdout.strip() or 0)
        local.update({"toplevel": top.stdout.strip(), "branch": cur, "origin_matches_target": same,
                      "unpushed_commits": unpushed, "ssh_remote": remote.startswith("git@")})
        # In-place only when nothing local could ride along with the push.
        local["in_place"] = same and cur == res["target"].get("default_branch") and unpushed == 0
    res["local"] = local
    res["ok"] = not res["blockers"]
    emit(res)


# ---------------------------------------------------------------- check-site

class LinkParser(html.parser.HTMLParser):
    ATTRS = {"href", "src", "poster", "data", "action"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if v is None:
                continue
            if k in self.ATTRS:
                self.links.append(v.strip())
            elif k == "srcset":
                self.links += [c.strip().split()[0] for c in v.split(",") if c.strip()]
            elif k == "style":
                self.links += css_urls(v)


CSS_URL_RE = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""", re.I)


def css_urls(text):
    return [m.group(2).strip() for m in CSS_URL_RE.finditer(text)]


def is_external(link):
    return (not link or link.startswith(("#", "//", "data:", "mailto:", "tel:", "javascript:", "{{", "{%"))
            or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", link) is not None)


def resolve_local(root, page_rel, link):
    path = urllib.parse.unquote(link.split("#", 1)[0].split("?", 1)[0])
    if not path:
        return None
    base = posixpath.dirname(page_rel)
    target = posixpath.normpath(path.lstrip("/") if path.startswith("/") else posixpath.join(base, path))
    if target.startswith(".."):
        return target  # escapes the site: reported missing
    full = os.path.join(root, target)
    candidates = [full, os.path.join(full, "index.html"), full + ".html"]
    return None if any(os.path.isfile(c) for c in candidates) else target


ATTR_LINK_RE = re.compile(r"""((?:href|src|poster|action|data)\s*=\s*)(["'])/(?!/)([^"']*)\2""", re.I)
SRCSET_RE = re.compile(r"""(srcset\s*=\s*)(["'])([^"']*)\2""", re.I)
CSS_ROOT_RE = re.compile(r"""(url\(\s*)(['"]?)/(?!/)([^'")]*)\2(\s*\))""", re.I)


def fix_root_links(root, rel):
    """Rewrite root-absolute links (/x) to paths relative to the file. Returns the original links rewritten."""
    path = os.path.join(root, rel)
    text = open(path, encoding="utf-8", errors="surrogateescape").read()
    prefix = "../" * rel.count("/")
    changed = []

    def attr(m):
        changed.append("/" + m.group(3))
        return "%s%s%s%s" % (m.group(1), m.group(2), (prefix + m.group(3)) or "./", m.group(2))

    def srcset(m):
        parts = []
        for cand in m.group(3).split(","):
            c = cand.strip()
            if c.startswith("/") and not c.startswith("//"):
                changed.append(c.split()[0])
                c = prefix + c[1:]
            parts.append(c)
        return "%s%s%s%s" % (m.group(1), m.group(2), ", ".join(parts), m.group(2))

    def css(m):
        changed.append("/" + m.group(3))
        return "%s%s%s%s%s" % (m.group(1), m.group(2), (prefix + m.group(3)) or "./", m.group(2), m.group(4))

    new = text
    if rel.lower().endswith((".html", ".htm")):
        new = ATTR_LINK_RE.sub(attr, new)
        new = SRCSET_RE.sub(srcset, new)
    new = CSS_ROOT_RE.sub(css, new)
    if new != text:
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(new)
    return changed


SSG_MARKERS = ("_config.yml", "config.toml", "hugo.toml", "mkdocs.yml", "astro.config.mjs", "astro.config.ts",
               "next.config.js", "vite.config.js", "vite.config.ts", "svelte.config.js", "eleventy.config.js",
               ".eleventy.js", "docusaurus.config.js", "gatsby-config.js")


def cmd_check_site(a):
    root = os.path.abspath(a.dir)
    if not os.path.isdir(root):
        die(2, "content folder %s does not exist" % root, "pass the folder that holds index.html")
    errors, warnings, fixed = [], [], []
    files = list_files(root)
    all_files = list_files(root, skip_hidden=False)
    hidden = sorted(set(all_files) - set(files))
    if hidden:
        warnings.append("hidden files are not deployed by upload-pages-artifact: %s" % ", ".join(hidden[:10]))
    ssg = [m for m in SSG_MARKERS if m in all_files or m in files]
    if ssg:
        errors.append({"id": "needs-build", "detail": "site-generator source (%s); publish its built output folder"
                       % ", ".join(ssg)})
    if "index.html" not in files:
        errors.append({"id": "no-index", "detail": "no index.html at the content root"})
    total = 0
    for rel in files:
        full = os.path.join(root, rel)
        if os.path.islink(full):
            warnings.append("symlink %s is deployed as its target's bytes" % rel)
        size = os.path.getsize(full)
        total += size
        if size > MAX_FILE:
            errors.append({"id": "file-too-large", "detail": "%s is %d MB (limit 100 MB)" % (rel, size >> 20)})
        with open(full, "rb") as f:
            if f.read(64).startswith(b"version https://git-lfs"):
                warnings.append("%s is a Git LFS pointer, not the real file" % rel)
    if total > MAX_SITE:
        errors.append({"id": "site-too-large", "detail": "site is %d MB (Pages limit 1 GB)" % (total >> 20)})
    for rel in [f for f in files if f.lower().endswith((".html", ".htm", ".css"))]:
        if a.project_site and a.fix_root_links:
            links = fix_root_links(root, rel)
            if links:
                fixed.append({"file": rel, "root_links_rewritten": len(links), "links": links[:20]})
        text = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
        if rel.lower().endswith(".css"):
            links = css_urls(text)
        else:
            p = LinkParser()
            try:
                p.feed(text)
            except Exception as e:  # malformed HTML must not stop the whole check
                warnings.append("could not parse %s: %s" % (rel, e))
                continue
            links = p.links + [u for block in re.findall(r"<style[^>]*>(.*?)</style>", text, re.S | re.I)
                               for u in css_urls(block)]
        for link in links:
            if is_external(link):
                continue
            if link.startswith("/") and a.project_site:
                errors.append({"id": "root-absolute-link", "file": rel, "link": link,
                               "detail": "breaks on a project site served under /<repo>/; re-run with --fix-root-links"})
                continue
            missing = resolve_local(root, rel, link)
            if missing:
                errors.append({"id": "broken-link", "file": rel, "link": link, "detail": "target %s not found" % missing})
    emit({"ok": not errors, "dir": root, "files": len(files), "bytes": total,
          "errors": errors, "warnings": warnings, "fixed": fixed}, 0 if not errors else 1)


# ---------------------------------------------------------------- sync-site

def cmd_sync_site(a):
    src = os.path.abspath(a.src)
    repo = os.path.abspath(a.repo_dir)
    if not os.path.isdir(src):
        die(2, "content folder %s does not exist" % src, "run check-site on the prepared content first")
    if not os.path.isdir(os.path.join(repo, ".git")):
        die(2, "%s is not a git checkout" % repo, "pass the cloned target repo with --repo-dir")
    site_dir, dest = safe_site_dir(repo, a.site_dir)
    mpath = os.path.join(repo, MANIFEST_REL)
    prev = json.load(open(mpath)) if os.path.exists(mpath) else None
    moved_from = None
    if prev and (prev.get("site_dir") or ".") != site_dir:
        if a.move_from != (prev.get("site_dir") or "."):
            emit({"ok": False, "conflict": "site-dir-changed", "previous": prev.get("site_dir"),
                  "requested": site_dir, "detail": "the last publish used another folder; ask which to keep. "
                  "To move, re-run with --move-from %s" % prev.get("site_dir")}, 3)
        moved_from = prev.get("site_dir") or "."
    new_files = list_files(src)
    same_dir = os.path.realpath(src) == os.path.realpath(dest)
    tracked = tracked_files(repo, site_dir) if os.path.isdir(dest) else []
    on_disk = list_files(dest) if os.path.isdir(dest) else []
    added, changed = [], []
    for rel in new_files:
        d = os.path.join(dest, rel)
        if not os.path.exists(d):
            added.append(rel)
        elif not same_dir and sha256(d) != sha256(os.path.join(src, rel)):
            changed.append(rel)
    # Deletion candidates are tracked files only, so an untracked file is never lost.
    if moved_from is not None:
        old_prefix = "" if moved_from == "." else moved_from + "/"
        old_tracked = set(tracked_files(repo, moved_from))
        old_deleted = [old_prefix + f for f in prev.get("files", []) if f in old_tracked
                       and posixpath.basename(f) not in KEEP_IN_SITE_DIR]
        candidates = []
    else:
        old_deleted = []
        if prev:
            candidates = [f for f in prev.get("files", []) if f not in new_files and f in tracked]
        elif site_dir == ".":
            candidates = []  # never sweep a repo root without a record of what we published
        else:
            candidates = [f for f in tracked if f not in new_files]
    deleted = [f for f in candidates if posixpath.basename(f) not in KEEP_IN_SITE_DIR]
    untracked = [f for f in on_disk if f not in tracked and f not in new_files]
    stale = untracked + ([] if prev or site_dir != "." else
                         [f for f in tracked if f.lower().endswith((".html", ".htm"))
                          and f not in new_files and "/" not in f])
    prefix = "" if site_dir == "." else site_dir + "/"
    new_paths = [prefix + r for r in added + changed]
    ignored = []
    if new_paths:
        chk = subprocess.run(["git", "-C", repo, "check-ignore", "--no-index", "--stdin"],
                             input="\n".join(new_paths) + "\n", capture_output=True, text=True)
        ignored = [l for l in chk.stdout.splitlines() if l]
    manifest_changed = (prev is None or moved_from is not None or sorted(prev.get("files", [])) != new_files
                        or bool(added or changed or deleted))
    if not a.dry_run:
        if not same_dir:
            for rel in added + changed:
                os.makedirs(os.path.dirname(os.path.join(dest, rel)) or dest, exist_ok=True)
                shutil.copy2(os.path.join(src, rel), os.path.join(dest, rel))
        removals = [os.path.join(dest, rel) for rel in deleted] + [os.path.join(repo, p) for p in old_deleted]
        for full in removals:
            if os.path.exists(full):
                os.remove(full)
            parent = os.path.dirname(full)
            while parent not in (dest, repo) and os.path.isdir(parent) and not os.listdir(parent):
                os.rmdir(parent)
                parent = os.path.dirname(parent)
        if manifest_changed:
            append_paths(a.paths_out, new_paths + [prefix + r for r in deleted] + old_deleted + [MANIFEST_REL])
            os.makedirs(os.path.dirname(mpath), exist_ok=True)
            with open(mpath, "w") as f:
                json.dump({"site_dir": site_dir, "files": new_files, "tool": "github-pages-publish",
                           "published_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")},
                          f, indent=2)
                f.write("\n")
    emit({"ok": True, "dry_run": a.dry_run, "site_dir": site_dir, "added": added, "changed": changed,
          "deleted": deleted, "moved_from": moved_from, "deleted_from_old_dir": old_deleted,
          "first_publish_sweep": bool(deleted) and not prev,
          "unchanged": len(new_files) - len(added) - len(changed), "stale_not_deleted": stale[:50],
          "gitignored": ignored, "manifest": MANIFEST_REL, "manifest_changed": manifest_changed})


# ---------------------------------------------------------------- workflow

def latest_major(action):
    data, _ = gh_json(["api", "repos/actions/%s/releases/latest" % action])
    tag = (data or {}).get("tag_name", "")
    m = re.match(r"^(v\d+)", tag)
    return (m.group(1), "latest") if m else (FALLBACK_ACTIONS[action], "fallback")


def cmd_workflow(a):
    repo = os.path.abspath(a.repo_dir)
    wf_dir = os.path.join(repo, ".github", "workflows")
    site_dir, _ = safe_site_dir(repo, a.site_dir)
    found = []
    for fn in sorted(os.listdir(wf_dir)) if os.path.isdir(wf_dir) else []:
        if re.search(r"\.ya?ml$", fn):
            text = open(os.path.join(wf_dir, fn), encoding="utf-8", errors="replace").read()
            found.append(dict(path=".github/workflows/" + fn, **classify_workflow(text)))
    pages_wfs = [w for w in found if w["deploys_pages"] or w["pushes_branch"]]
    conflicts = [w for w in pages_wfs if not w["managed"] and (w["builds"] or w["pushes_branch"])]
    if conflicts:
        emit({"ok": False, "conflict": "existing-pages-workflow", "workflows": conflicts,
              "detail": "another workflow builds or pushes the site; ask before replacing it"}, 3)
    if len(pages_wfs) > 1:
        emit({"ok": False, "conflict": "several-pages-workflows", "workflows": pages_wfs,
              "detail": "more than one workflow deploys Pages; ask which one to keep"}, 3)
    if pages_wfs:
        rel = pages_wfs[0]["path"]
    else:
        rel = ".github/workflows/pages.yml"
        if os.path.exists(os.path.join(repo, rel)):
            rel = ".github/workflows/pages-publish.yml"
    full = os.path.join(repo, rel)
    old = open(full).read() if os.path.exists(full) else None
    versions, sources = {}, {}
    for act in FALLBACK_ACTIONS:
        pinned = re.search(r"actions/%s@(v\d+)" % re.escape(act), old or "")
        if a.keep_versions and pinned:
            versions[act], sources[act] = pinned.group(1), "kept"
        elif a.offline:
            versions[act], sources[act] = FALLBACK_ACTIONS[act], "fallback"
        else:
            versions[act], sources[act] = latest_major(act)
    paths_block = "" if site_dir == "." else (
        "    paths:\n      - '%s/**'\n      - '%s'\n" % (site_dir, rel))
    try:
        text = open(TEMPLATE).read()
    except OSError as e:
        die(2, "workflow template missing: %s" % e, "reinstall the skill; assets/pages-workflow.yml is required")
    for k, v in {"{{SITE_LABEL}}": "the repo root" if site_dir == "." else site_dir + "/",
                 "{{BRANCH}}": a.branch, "{{PATHS_BLOCK}}": paths_block,
                 "{{SITE_PATH}}": "." if site_dir == "." else site_dir,
                 "{{CHECKOUT}}": versions["checkout"], "{{CONFIGURE}}": versions["configure-pages"],
                 "{{UPLOAD}}": versions["upload-pages-artifact"], "{{DEPLOY}}": versions["deploy-pages"]}.items():
        text = text.replace(k, v)
    action = "unchanged" if old == text else ("updated" if old is not None else "created")
    if not a.dry_run and action != "unchanged":
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(text)
        append_paths(a.paths_out, [rel])
    emit({"ok": True, "dry_run": a.dry_run, "path": rel, "file": os.path.basename(rel), "action": action,
          "versions": versions, "version_source": sources,
          "other_workflows": [w["path"] for w in found if w["path"] != rel]})


# ---------------------------------------------------------------- configure

def cmd_configure(a):
    full = a.repo
    pages, err = gh_json(["api", "repos/%s/pages" % full])
    before = pages.get("build_type") if pages else None
    action = "unchanged"
    if a.dry_run:
        action = "would-create" if not pages else ("would-switch" if before != "workflow" else "unchanged")
        emit({"ok": True, "dry_run": True, "action": action, "build_type_before": before,
              "html_url": (pages or {}).get("html_url")})
    if not pages:
        p = run(["gh", "api", "-X", "POST", "repos/%s/pages" % full, "-f", "build_type=workflow"])
        if p.returncode != 0:
            die(1, "could not enable Pages on %s: %s" % (full, p.stderr.strip()[:400]),
                "private repos need a paid plan; an empty repo needs its first push first")
        action = "created"
    elif before != "workflow":
        p = run(["gh", "api", "-X", "PUT", "repos/%s/pages" % full, "-f", "build_type=workflow"])
        if p.returncode != 0:
            die(1, "could not switch Pages on %s to GitHub Actions: %s" % (full, p.stderr.strip()[:400]),
                "set Settings > Pages > Source to 'GitHub Actions' by hand, then re-run")
        action = "switched"
    after, _ = gh_json(["api", "repos/%s/pages" % full])
    if not after or after.get("build_type") != "workflow":
        die(1, "Pages on %s does not report build_type=workflow after the change" % full,
            "open Settings > Pages and check the Source setting")
    emit({"ok": True, "action": action, "build_type_before": before, "build_type": after["build_type"],
          "html_url": after.get("html_url"), "cname": after.get("cname")})


# ---------------------------------------------------------------- verify

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "github-pages-publish-verify",
                                               "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, b"", url
    except (urllib.error.URLError, OSError) as e:
        return None, str(e).encode(), url


def pick_files(files, limit):
    order = (["index.html"] if "index.html" in files else []) + \
            [f for f in files if f.endswith((".html", ".htm")) and f != "index.html"] + \
            [f for f in files if not f.endswith((".html", ".htm"))]
    return order[:limit]


def wait_for_run(a):
    deadline = time.time() + a.run_timeout
    run_info = None
    while time.time() < deadline:
        runs, _ = gh_json(["run", "list", "-R", a.repo, "--workflow", os.path.basename(a.workflow),
                           "--commit", a.sha] + (["--event", a.event] if a.event else []) +
                          ["--json", "databaseId,status,conclusion,url,event,createdAt", "--limit", "5"])
        if runs:
            run_info = runs[0]
            if run_info["status"] == "completed":
                return run_info
        time.sleep(10)
    if not run_info:
        die(1, "no run of %s appeared for commit %s within %ds" % (a.workflow, a.sha[:7], a.run_timeout),
            "check the workflow's branch/paths filter, or start it: gh workflow run %s -R %s, then verify "
            "with --event workflow_dispatch" % (os.path.basename(a.workflow), a.repo))
    die(1, "deploy run %s still %s after %ds" % (run_info["url"], run_info["status"], a.run_timeout),
        "watch it with `gh run watch %s -R %s` and re-run verify" % (run_info["databaseId"], a.repo))


def cmd_verify(a):
    started = time.time()
    repo = os.path.abspath(a.repo_dir)
    site_dir, _ = safe_site_dir(repo, a.site_dir)
    prefix = "" if site_dir == "." else site_dir + "/"
    sha = a.sha or run(["git", "-C", repo, "rev-parse", "HEAD"], check=True).stdout.strip()
    a.sha = sha
    run_info = wait_for_run(a)
    if run_info["conclusion"] != "success":
        die(1, "deploy run %s ended '%s'" % (run_info["url"], run_info["conclusion"]),
            "read the failure: gh run view %s -R %s --log-failed" % (run_info["databaseId"], a.repo))
    url = a.url
    if not url:
        pages, err = gh_json(["api", "repos/%s/pages" % a.repo])
        if not pages or not pages.get("html_url"):
            die(1, "Pages reports no URL for %s: %s" % (a.repo, err[:200]), "run the configure subcommand first")
        url = pages["html_url"]
    if not url.endswith("/"):
        url += "/"
    upgraded = prefer_https(url)
    https_upgraded, url = upgraded != url, upgraded
    mpath = os.path.join(repo, MANIFEST_REL)
    try:
        listed = json.load(open(mpath)).get("files", [])
    except (OSError, ValueError) as e:
        die(2, "cannot read %s: %s" % (mpath, e), "run sync-site first; it writes the manifest")
    files = pick_files(listed, a.max_files)
    expected = {}
    for f in files:  # hash the committed blob, not the working tree (CRLF/LFS filters differ)
        blob = run(["git", "-C", repo, "show", "%s:%s%s" % (sha, prefix, f)], binary=True)
        if blob.returncode != 0:
            die(2, "%s%s is not in commit %s" % (prefix, f, sha[:7]), "commit and push before verify")
        expected[f] = hashlib.sha256(blob.stdout).hexdigest()
    deadline = time.time() + a.live_timeout
    attempt = 0
    while True:
        attempt += 1
        nonce = "%d-%d" % (int(time.time()), attempt)
        bad = []
        for f in files:
            status, body, _ = fetch("%s%s?ppv=%s" % (url, urllib.parse.quote(f), nonce))
            if status != 200:
                bad.append({"path": f, "status": status,
                            "detail": body[:120].decode("utf-8", "replace") if status is None else ""})
            elif hashlib.sha256(body).hexdigest() != expected[f]:
                bad.append({"path": f, "status": status, "detail": "content differs from commit"})
        root_ok = None
        if "index.html" in expected:
            status, body, _ = fetch("%s?ppv=%s" % (url, nonce))
            root_ok = status == 200 and hashlib.sha256(body).hexdigest() == expected["index.html"]
        if (not bad and root_ok is not False) or time.time() >= deadline:
            break
        time.sleep(10)
    ok = not bad and root_ok is not False
    emit({"ok": ok, "url": url, "sha": sha, "run": run_info, "files_total": len(listed),
          "checked": len(files), "matched": len(files) - len(bad), "capped": len(listed) > len(files),
          "root_url_ok": root_ok, "https_upgraded": https_upgraded, "mismatched": bad[:20], "attempts": attempt,
          "elapsed_s": int(time.time() - started)}, 0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("log-init"); p.add_argument("--dir", default=".pages-publish"); p.add_argument("--request")
    p.set_defaults(fn=cmd_log_init)
    p = sp.add_parser("log"); p.add_argument("--file", required=True); p.add_argument("--step", required=True)
    p.add_argument("--status", required=True, choices=["pass", "fail", "skip", "info", "ask"])
    p.add_argument("--msg", required=True); p.add_argument("--cmd"); p.set_defaults(fn=cmd_log)
    p = sp.add_parser("preflight"); p.add_argument("--repo", required=True); p.set_defaults(fn=cmd_preflight)
    p = sp.add_parser("check-site"); p.add_argument("--dir", required=True)
    p.add_argument("--project-site", action="store_true", help="site is served under /<repo>/")
    p.add_argument("--fix-root-links", action="store_true"); p.set_defaults(fn=cmd_check_site)
    p = sp.add_parser("sync-site"); p.add_argument("--src", required=True); p.add_argument("--repo-dir", required=True)
    p.add_argument("--site-dir", required=True); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--move-from", help="previous site folder to move away from (deletes its published files)")
    p.add_argument("--paths-out", help="append changed repo paths to this file"); p.set_defaults(fn=cmd_sync_site)
    p = sp.add_parser("workflow"); p.add_argument("--repo-dir", required=True); p.add_argument("--site-dir", required=True)
    p.add_argument("--branch", required=True); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--offline", action="store_true", help="use pinned fallback action versions")
    p.add_argument("--keep-versions", action="store_true", help="keep action majors already in the workflow")
    p.add_argument("--paths-out", help="append the workflow path to this file when it changes")
    p.set_defaults(fn=cmd_workflow)
    p = sp.add_parser("configure"); p.add_argument("--repo", required=True); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_configure)
    p = sp.add_parser("verify"); p.add_argument("--repo", required=True); p.add_argument("--repo-dir", required=True)
    p.add_argument("--site-dir", required=True); p.add_argument("--workflow", default="pages.yml")
    p.add_argument("--sha", help="commit to verify (default: HEAD of --repo-dir)"); p.add_argument("--url")
    p.add_argument("--event", help="only runs from this event, e.g. workflow_dispatch")
    p.add_argument("--run-timeout", type=int, default=900); p.add_argument("--live-timeout", type=int, default=600)
    p.add_argument("--max-files", type=int, default=100); p.set_defaults(fn=cmd_verify)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
