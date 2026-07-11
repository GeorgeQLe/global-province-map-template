"""M14.5 public landing page validation, git publish, and Vercel deploy."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

from gpm.paths import PROJECT_ROOT
from gpm.release.alpha import ReleaseError

LANDING_DIR_NAME = "landing"
REQUIRED_LANDING_FILES: tuple[str, ...] = (
    "index.html",
    "styles.css",
    "app.js",
    "vercel.json",
)

# Interactive demo (static MapLibre page + beta sample data).
REQUIRED_DEMO_FILES: tuple[str, ...] = (
    "demo/index.html",
    "demo/demo.js",
    "demo/demo.css",
    "demo/data/demo-manifest.json",
    "demo/data/adjacency.json",
    "demo/data/official-1444.geojson",
    "demo/data/official-1836.geojson",
    "demo/data/official-1936.geojson",
    "demo/data/modern-baseline.geojson",
    "demo/data/official-1444.legend.json",
    "demo/data/official-1836.legend.json",
    "demo/data/official-1936.legend.json",
    "demo/data/modern-baseline.legend.json",
    # M18 culture / religion identity legends
    "demo/data/official-1444.culture.legend.json",
    "demo/data/official-1444.religion.legend.json",
    "demo/data/official-1836.culture.legend.json",
    "demo/data/official-1836.religion.legend.json",
    "demo/data/official-1936.culture.legend.json",
    "demo/data/official-1936.religion.legend.json",
    "demo/data/modern-baseline.culture.legend.json",
    "demo/data/modern-baseline.religion.legend.json",
    # Multi-era period geometry demo assets (M15–M16)
    "demo/data/official-1444-period.geojson",
    "demo/data/official-1444-period.legend.json",
    "demo/data/official-1444-period.culture.legend.json",
    "demo/data/official-1444-period.religion.legend.json",
    "demo/data/boundary-hints-1444.geojson",
    "demo/data/lineage-1444.json",
    "demo/data/official-1836-period.geojson",
    "demo/data/official-1836-period.legend.json",
    "demo/data/official-1836-period.culture.legend.json",
    "demo/data/official-1836-period.religion.legend.json",
    "demo/data/boundary-hints-1836.geojson",
    "demo/data/lineage-1836.json",
    "demo/data/official-1936-period.geojson",
    "demo/data/official-1936-period.legend.json",
    "demo/data/official-1936-period.culture.legend.json",
    "demo/data/official-1936-period.religion.legend.json",
    "demo/data/boundary-hints-1936.geojson",
    "demo/data/lineage-1936.json",
    # M19 PMTiles / vector tiles (ownership layer per scenario)
    "demo/data/official-1444.pmtiles",
    "demo/data/official-1444.tileset.json",
    "demo/data/official-1836.pmtiles",
    "demo/data/official-1836.tileset.json",
    "demo/data/official-1936.pmtiles",
    "demo/data/official-1936.tileset.json",
    "demo/data/modern-baseline.pmtiles",
    "demo/data/modern-baseline.tileset.json",
)

# Content anchors that prove the page still describes the project honestly.
REQUIRED_HTML_SNIPPETS: tuple[str, ...] = (
    "Global Province Map",
    "scaffold-baseline",
    "curated-politics",
    "gpm export pack",
    "gpm export atlas",
    "official-1836",
    "official-1444",
    "official-1936",
    "license-audited",
    "Natural Earth",
    "geoBoundaries",
    "M14.5",
    "/demo",
)

REQUIRED_DEMO_HTML_SNIPPETS: tuple[str, ...] = (
    "Interactive demo",
    "official-1444",
    "official-1836",
    "official-1936",
    "modern-baseline",
    "period-geometry",
    "boundary hints",
    "layer-period-geometry",
    "layer-boundary-hints",
    "layer-culture",
    "layer-religion",
    "layer-pmtiles",
    "pmtiles",
    "gpm export pack",
    "gpm export atlas",
    "scaffold-baseline",
    "curated-politics",
    "Reserved for later",
    # Root-absolute assets: required under Vercel cleanUrls + trailingSlash:false
    # where the page is served as /demo (no trailing slash).
    'href="/demo/demo.css"',
    'src="/demo/demo.js"',
)


@dataclass(frozen=True)
class LandingValidationResult:
    landing_dir: str
    files_present: tuple[str, ...]
    missing_files: tuple[str, ...]
    missing_snippets: tuple[str, ...]
    html_bytes: int
    valid: bool
    demo_files_present: tuple[str, ...] = ()
    missing_demo_files: tuple[str, ...] = ()
    missing_demo_snippets: tuple[str, ...] = ()
    demo_html_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SiteReleaseResult:
    landing_dir: str
    validation: LandingValidationResult
    repo_url: str | None = None
    repo_created: bool = False
    pushed: bool = False
    commit_sha: str | None = None
    deployed: bool = False
    deployment_url: str | None = None
    inspect_url: str | None = None
    dry_run: bool = False
    messages: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def default_landing_dir(project_root: Path | None = None) -> Path:
    root = project_root or PROJECT_ROOT
    return root / LANDING_DIR_NAME


def validate_landing_site(landing_dir: Path | None = None) -> LandingValidationResult:
    """Validate the static landing site is complete and on-message."""
    path = (landing_dir or default_landing_dir()).resolve()
    if not path.is_dir():
        raise ReleaseError(f"Landing directory does not exist: {path}")

    present: list[str] = []
    missing: list[str] = []
    for name in REQUIRED_LANDING_FILES:
        if (path / name).is_file():
            present.append(name)
        else:
            missing.append(name)

    demo_present: list[str] = []
    demo_missing: list[str] = []
    for name in REQUIRED_DEMO_FILES:
        if (path / name).is_file():
            demo_present.append(name)
        else:
            demo_missing.append(name)

    html_path = path / "index.html"
    html_bytes = 0
    missing_snippets: list[str] = []
    if html_path.is_file():
        raw = html_path.read_bytes()
        html_bytes = len(raw)
        html_text = raw.decode("utf-8", errors="replace")
        for snippet in REQUIRED_HTML_SNIPPETS:
            if snippet not in html_text:
                missing_snippets.append(snippet)
    else:
        missing_snippets = list(REQUIRED_HTML_SNIPPETS)

    demo_html_path = path / "demo" / "index.html"
    demo_html_bytes = 0
    missing_demo_snippets: list[str] = []
    if demo_html_path.is_file():
        demo_raw = demo_html_path.read_bytes()
        demo_html_bytes = len(demo_raw)
        demo_html_text = demo_raw.decode("utf-8", errors="replace")
        for snippet in REQUIRED_DEMO_HTML_SNIPPETS:
            if snippet not in demo_html_text:
                missing_demo_snippets.append(snippet)
    else:
        missing_demo_snippets = list(REQUIRED_DEMO_HTML_SNIPPETS)

    valid = (
        not missing
        and not missing_snippets
        and html_bytes > 0
        and not demo_missing
        and not missing_demo_snippets
        and demo_html_bytes > 0
    )
    return LandingValidationResult(
        landing_dir=str(path),
        files_present=tuple(present),
        missing_files=tuple(missing),
        missing_snippets=tuple(missing_snippets),
        html_bytes=html_bytes,
        valid=valid,
        demo_files_present=tuple(demo_present),
        missing_demo_files=tuple(demo_missing),
        missing_demo_snippets=tuple(missing_demo_snippets),
        demo_html_bytes=demo_html_bytes,
    )


def release_landing_site(
    *,
    landing_dir: Path | None = None,
    project_root: Path | None = None,
    ensure_repo: bool = False,
    repo_name: str | None = None,
    repo_owner: str | None = None,
    repo_visibility: str = "public",
    remote_name: str = "origin",
    push: bool = False,
    commit_message: str | None = None,
    branch: str | None = None,
    deploy: bool = False,
    production: bool = True,
    dry_run: bool = False,
    vercel_token: str | None = None,
) -> SiteReleaseResult:
    """Validate the landing page; optionally ensure GitHub remote, push, and deploy.

    Network side effects (``gh``, ``git push``, ``vercel``) are skipped when
    *dry_run* is true. Validation always runs.
    """
    root = (project_root or PROJECT_ROOT).resolve()
    path = (landing_dir or default_landing_dir(root)).resolve()
    validation = validate_landing_site(path)
    messages: list[str] = []

    if not validation.valid:
        detail_parts: list[str] = []
        if validation.missing_files:
            detail_parts.append(f"missing files: {', '.join(validation.missing_files)}")
        if validation.missing_snippets:
            detail_parts.append(
                "missing content snippets: " + ", ".join(validation.missing_snippets)
            )
        if validation.missing_demo_files:
            detail_parts.append(
                "missing demo files: " + ", ".join(validation.missing_demo_files)
            )
        if validation.missing_demo_snippets:
            detail_parts.append(
                "missing demo content snippets: "
                + ", ".join(validation.missing_demo_snippets)
            )
        raise ReleaseError(
            "Landing site validation failed (" + "; ".join(detail_parts) + ")"
        )

    messages.append(f"Validated landing site at {path}")

    if dry_run:
        messages.append("Dry run: skipped git remote ensure, push, and Vercel deploy")
        return SiteReleaseResult(
            landing_dir=str(path),
            validation=validation,
            dry_run=True,
            messages=tuple(messages),
        )

    repo_url: str | None = None
    repo_created = False
    pushed = False
    commit_sha: str | None = None
    deployed = False
    deployment_url: str | None = None
    inspect_url: str | None = None

    if ensure_repo or push:
        _require_tool("git")
        if not (root / ".git").is_dir():
            raise ReleaseError(f"Not a git repository: {root}")

    if ensure_repo:
        _require_tool("gh")
        ensure = _ensure_github_remote(
            root=root,
            remote_name=remote_name,
            repo_name=repo_name or root.name,
            repo_owner=repo_owner,
            visibility=repo_visibility,
        )
        repo_url = ensure["repo_url"]
        repo_created = bool(ensure["created"])
        messages.extend(ensure["messages"])

    if push:
        push_result = _commit_and_push_landing(
            root=root,
            landing_dir=path,
            remote_name=remote_name,
            branch=branch,
            commit_message=commit_message
            or "Publish M14.5 public landing page",
        )
        pushed = bool(push_result["pushed"])
        commit_sha = push_result.get("commit_sha")
        messages.extend(push_result["messages"])
        if repo_url is None:
            repo_url = push_result.get("repo_url")

    if deploy:
        _require_tool("vercel")
        deploy_result = _deploy_vercel(
            landing_dir=path,
            production=production,
            token=vercel_token or os.environ.get("VERCEL_TOKEN"),
        )
        deployed = True
        deployment_url = deploy_result.get("deployment_url")
        inspect_url = deploy_result.get("inspect_url")
        messages.extend(deploy_result["messages"])

    return SiteReleaseResult(
        landing_dir=str(path),
        validation=validation,
        repo_url=repo_url,
        repo_created=repo_created,
        pushed=pushed,
        commit_sha=commit_sha,
        deployed=deployed,
        deployment_url=deployment_url,
        inspect_url=inspect_url,
        dry_run=False,
        messages=tuple(messages),
    )


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise ReleaseError(
            f"Required tool '{name}' not found on PATH. "
            f"Install it, then re-run gpm release site."
        )
    return path


def _run(
    args: Sequence[str],
    *,
    cwd: Path,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    result = subprocess.run(
        list(args),
        cwd=str(cwd),
        text=True,
        capture_output=True,
        env=merged,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise ReleaseError(
            f"Command failed ({result.returncode}): {' '.join(args)}\n{stderr}"
        )
    return result


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=root, check=check)


def _remote_url(root: Path, remote_name: str) -> str | None:
    result = _git(root, "remote", "get-url", remote_name, check=False)
    if result.returncode != 0:
        return None
    return (result.stdout or "").strip() or None


def _parse_github_slug(remote_url: str) -> tuple[str, str] | None:
    patterns = (
        r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+?)(?:\.git)?$",
        r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/.]+?)(?:\.git)?$",
    )
    for pattern in patterns:
        match = re.search(pattern, remote_url.strip())
        if match:
            return match.group("owner"), match.group("repo")
    return None


def _gh_repo_view(slug: str) -> dict[str, Any] | None:
    result = _run(
        ["gh", "repo", "view", slug, "--json", "url,nameWithOwner,isPrivate"],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ReleaseError(f"Could not parse gh repo view JSON for {slug}") from exc


def _ensure_github_remote(
    *,
    root: Path,
    remote_name: str,
    repo_name: str,
    repo_owner: str | None,
    visibility: str,
) -> dict[str, Any]:
    messages: list[str] = []
    existing = _remote_url(root, remote_name)
    if existing:
        messages.append(f"Using existing git remote '{remote_name}': {existing}")
        slug = _parse_github_slug(existing)
        if slug:
            owner, name = slug
            view = _gh_repo_view(f"{owner}/{name}")
            if view:
                return {
                    "repo_url": view.get("url") or f"https://github.com/{owner}/{name}",
                    "created": False,
                    "messages": messages,
                }
        return {
            "repo_url": existing,
            "created": False,
            "messages": messages,
        }

    if visibility not in {"public", "private"}:
        raise ReleaseError("repo_visibility must be 'public' or 'private'")

    if repo_owner:
        slug = f"{repo_owner}/{repo_name}"
        create_args = ["gh", "repo", "create", slug, f"--{visibility}", "--source=.", f"--remote={remote_name}"]
    else:
        slug = repo_name
        create_args = ["gh", "repo", "create", repo_name, f"--{visibility}", "--source=.", f"--remote={remote_name}"]

    # Prefer create when missing; if the remote name is free but repo exists, just add remote.
    view = None
    probe_slug = f"{repo_owner}/{repo_name}" if repo_owner else None
    if probe_slug:
        view = _gh_repo_view(probe_slug)
    if view is None and repo_owner is None:
        # Resolve authenticated user and probe owner/name.
        who = _run(["gh", "api", "user", "--jq", ".login"], cwd=root, check=False)
        login = (who.stdout or "").strip()
        if login:
            view = _gh_repo_view(f"{login}/{repo_name}")
            if view:
                probe_slug = f"{login}/{repo_name}"

    if view:
        url = view.get("url") or f"https://github.com/{probe_slug}"
        _git(root, "remote", "add", remote_name, f"{url}.git")
        messages.append(f"Added git remote '{remote_name}' → {url} (repo already existed)")
        return {"repo_url": url, "created": False, "messages": messages}

    result = _run(create_args, cwd=root, check=True)
    messages.append((result.stdout or result.stderr or f"Created GitHub repo {slug}").strip())
    url = _remote_url(root, remote_name)
    if not url:
        # gh usually prints the HTTPS URL
        created_url = (result.stdout or "").strip().splitlines()
        url = created_url[-1] if created_url else f"https://github.com/{slug}"
    messages.append(f"Created GitHub repository and set remote '{remote_name}'")
    return {"repo_url": url, "created": True, "messages": messages}


def _commit_and_push_landing(
    *,
    root: Path,
    landing_dir: Path,
    remote_name: str,
    branch: str | None,
    commit_message: str,
) -> dict[str, Any]:
    messages: list[str] = []
    if _remote_url(root, remote_name) is None:
        raise ReleaseError(
            f"No git remote named '{remote_name}'. "
            "Pass --ensure-repo to create or attach a GitHub repository first."
        )

    rel = os.path.relpath(landing_dir, root)
    if rel.startswith(".."):
        raise ReleaseError(
            f"Landing dir {landing_dir} is outside project root {root}; "
            "refusing to commit"
        )

    # Stage landing assets (and vercel config if present at root later).
    _git(root, "add", "--", rel)

    status = _git(root, "status", "--porcelain", "--", rel)
    staged_or_dirty = bool((status.stdout or "").strip())

    commit_sha: str | None = None
    if staged_or_dirty:
        # Only commit if the index has changes for these paths after add.
        diff_cached = _git(root, "diff", "--cached", "--name-only", "--", rel)
        if (diff_cached.stdout or "").strip():
            _git(root, "commit", "-m", commit_message, "--", rel)
            messages.append(f"Committed landing page changes: {commit_message}")
        else:
            messages.append("Landing page already staged/committed; nothing new to commit")
    else:
        messages.append("No landing page changes to commit")

    sha_result = _git(root, "rev-parse", "HEAD")
    commit_sha = (sha_result.stdout or "").strip() or None

    if branch is None:
        branch_result = _git(root, "branch", "--show-current")
        branch = (branch_result.stdout or "").strip() or "main"

    _git(root, "push", "-u", remote_name, branch)
    messages.append(f"Pushed branch '{branch}' to remote '{remote_name}'")

    repo_url = _remote_url(root, remote_name)
    return {
        "pushed": True,
        "commit_sha": commit_sha,
        "repo_url": repo_url,
        "messages": messages,
    }


def _deploy_vercel(
    *,
    landing_dir: Path,
    production: bool,
    token: str | None,
) -> dict[str, Any]:
    messages: list[str] = []
    args = ["vercel", "deploy", "--yes"]
    if production:
        args.append("--prod")
    env: dict[str, str] = {}
    if token:
        # Prefer flag so non-interactive CI works; also export for nested tools.
        args.extend(["--token", token])
        env["VERCEL_TOKEN"] = token

    result = _run(args, cwd=landing_dir, check=True, env=env or None)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    combined = "\n".join(part for part in (stdout, stderr) if part)
    messages.append("Vercel deploy completed")

    deployment_url = _extract_vercel_url(combined, production=production)
    inspect_url = _extract_inspect_url(combined)
    if deployment_url:
        messages.append(f"Deployment URL: {deployment_url}")
    if inspect_url:
        messages.append(f"Inspect URL: {inspect_url}")
    if not deployment_url and stdout:
        # Last non-empty line is often the URL in modern vercel CLI.
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        if lines:
            deployment_url = lines[-1]
            messages.append(f"Deployment URL: {deployment_url}")

    return {
        "deployment_url": deployment_url,
        "inspect_url": inspect_url,
        "messages": messages,
        "raw_output": combined,
    }


def _extract_vercel_url(text: str, *, production: bool) -> str | None:
    # Prefer production aliases when present.
    patterns = [
        r"https://[a-zA-Z0-9.-]+\.vercel\.app",
        r"Production:\s+(https://\S+)",
        r"Aliased:\s+(https://\S+)",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text))
    # re.findall may return tuples for groups — normalize.
    urls: list[str] = []
    for item in found:
        if isinstance(item, tuple):
            urls.extend(part for part in item if part.startswith("http"))
        elif item.startswith("http"):
            urls.append(item)
    if not urls:
        return None
    if production:
        # Prefer non-hash deployment aliases when possible.
        stable = [u for u in urls if re.search(r"https://[a-z0-9-]+\.vercel\.app/?$", u) and "--" not in u]
        if stable:
            return stable[-1]
    return urls[-1]


def _extract_inspect_url(text: str) -> str | None:
    match = re.search(r"Inspect:\s+(https://\S+)", text)
    if match:
        return match.group(1)
    match = re.search(r"https://vercel\.com/\S+/[a-zA-Z0-9-]+", text)
    return match.group(0) if match else None
