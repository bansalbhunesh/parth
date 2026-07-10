"""Build a reproducible public-repository census for ET AI Hackathon 2.0.

This is a discovery and triage tool, not a substitute for a technical review.
It searches the event name and the eight official problem-title fragments,
then records repository-level evidence that can be verified through GitHub.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

API_ROOT = "https://api.github.com"
EVENT_QUERY = '"ET AI Hackathon" created:>=2026-06-15'
TRACK_QUERIES = {
    "PS1 Industrial Safety": '"Zero-Harm Operations" created:>=2026-06-15',
    "PS2 Energy Resilience": '"Energy Supply Chain Resilience" created:>=2026-06-15',
    "PS3 EV Supply Chain": '"EV Supply Chain" created:>=2026-06-15',
    "PS4 Data Centre EPC": '"Data Centre EPC" created:>=2026-06-15',
    "PS5 Urban Air Quality": '"Urban Air Quality Intelligence" created:>=2026-06-15',
    "PS6 Digital Public Safety": '"Digital Public Safety" created:>=2026-06-15',
    "PS7 Cyber Resilience": '"Critical National Infrastructure" created:>=2026-06-15',
    "PS8 Industrial Knowledge": '"Industrial Knowledge Intelligence" created:>=2026-06-15',
}
TRACK_BY_NUMBER = {int(label[2]): label for label in TRACK_QUERIES}

CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".py",
    ".rs",
    ".ts",
    ".tsx",
    ".vue",
}
JUNK_SEGMENTS = {
    ".next",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
    ".venv",
}


@dataclass
class Candidate:
    repo: str
    html_url: str
    default_branch: str
    description: str = ""
    homepage: str = ""
    language: str = ""
    size_kb: int = 0
    created_at: str = ""
    pushed_at: str = ""
    event_match: bool = False
    tracks: set[str] = field(default_factory=set)
    files: int = 0
    code_files: int = 0
    test_files: int = 0
    ci_files: int = 0
    eval_files: int = 0
    data_files: int = 0
    architecture_files: int = 0
    impact_files: int = 0
    pitch_files: int = 0
    video_files: int = 0
    docker_files: int = 0
    lockfiles: int = 0
    junk_files: int = 0
    commits_visible: int = 0
    tree_truncated: bool = False
    readme_chars: int = 0
    readme_event: bool = False
    readme_video: bool = False
    readme_run: bool = False
    confidence: str = "Low"
    evidence_index: int = 0
    error: str = ""

    @property
    def track_label(self) -> str:
        return ", ".join(sorted(self.tracks)) if self.tracks else "Unclassified event match"


def api_get(path: str, token: str, retries: int = 3) -> Any:
    url = path if path.startswith("http") else f"{API_ROOT}/{path.lstrip('/')}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "pramaan-independent-field-audit",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    for attempt in range(retries):
        request = urllib.request.Request(url, headers=headers)
        try:
            # API URLs are always derived from the fixed HTTPS API_ROOT above.
            with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code not in {403, 429, 502, 503, 504} or attempt == retries - 1:
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == retries - 1:
                raise
        time.sleep(2**attempt)
    raise RuntimeError(f"unreachable retry state for {url}")


def search_repositories(query: str, token: str) -> list[dict[str, Any]]:
    encoded = urllib.parse.quote(query)
    first = api_get(f"search/repositories?q={encoded}&per_page=100&page=1", token)
    if not first:
        return []
    items = list(first.get("items", []))
    total = min(int(first.get("total_count", 0)), 1000)
    for page in range(2, math.ceil(total / 100) + 1):
        result = api_get(f"search/repositories?q={encoded}&per_page=100&page={page}", token)
        items.extend((result or {}).get("items", []))
    return items


def merge_candidate(candidates: dict[str, Candidate], item: dict[str, Any], source: str) -> None:
    repo = item["full_name"]
    candidate = candidates.get(repo)
    if candidate is None:
        candidate = Candidate(
            repo=repo,
            html_url=item.get("html_url") or f"https://github.com/{repo}",
            default_branch=item.get("default_branch") or "main",
            description=item.get("description") or "",
            homepage=item.get("homepage") or "",
            language=item.get("language") or "",
            size_kb=int(item.get("size") or 0),
            created_at=item.get("created_at") or "",
            pushed_at=item.get("pushed_at") or "",
        )
        candidates[repo] = candidate
    if source == "event":
        candidate.event_match = True
    else:
        candidate.tracks.add(source)


def is_junk(path: str) -> bool:
    return any(segment.lower() in JUNK_SEGMENTS for segment in path.split("/"))


def enrich_candidate(candidate: Candidate, token: str) -> Candidate:
    try:
        branch = urllib.parse.quote(candidate.default_branch, safe="")
        tree = api_get(f"repos/{candidate.repo}/git/trees/{branch}?recursive=1", token) or {"tree": []}
        entries = tree.get("tree", [])
        paths = [str(entry.get("path") or "") for entry in entries]
        candidate.files = len(paths)
        candidate.tree_truncated = bool(tree.get("truncated"))
        candidate.junk_files = sum(1 for path in paths if is_junk(path))

        useful_paths = [path for path in paths if not is_junk(path)]
        lower_paths = [path.lower() for path in useful_paths]
        candidate.code_files = sum(1 for path in useful_paths if Path(path).suffix.lower() in CODE_EXTENSIONS)
        candidate.test_files = sum(
            1 for path in lower_paths if re.search(r"(^|/)(test|tests|__tests__)(/|$)|\.(test|spec)\.", path)
        )
        candidate.ci_files = sum(1 for path in lower_paths if path.startswith(".github/workflows/"))
        candidate.eval_files = sum(
            1 for path in lower_paths if re.search(r"(^|/)(eval|evaluation|benchmark|benchmarks)(/|$)|metrics?", path)
        )
        candidate.data_files = sum(
            1 for path in lower_paths if re.search(r"(^|/)(data|dataset|datasets|fixtures|samples)(/|$)", path)
        )
        candidate.architecture_files = sum(1 for path in lower_paths if "architecture" in path)
        candidate.impact_files = sum(
            1 for path in lower_paths if re.search(r"(^|/)(impact|business|roi)([^/]*)(/|\.|$)", path)
        )
        candidate.pitch_files = sum(1 for path in lower_paths if "pitch" in path or path.endswith((".ppt", ".pptx")))
        candidate.video_files = sum(1 for path in lower_paths if path.endswith((".mp4", ".mov", ".m4v", ".webm")))
        candidate.docker_files = sum(
            1 for path in lower_paths if re.search(r"(^|/)(dockerfile|docker-compose[^/]*)$", path)
        )
        candidate.lockfiles = sum(
            1
            for path in lower_paths
            if re.search(
                r"(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|uv\.lock|pipfile\.lock|bun\.lockb?)$",
                path,
            )
        )

        readme = api_get(f"repos/{candidate.repo}/readme", token)
        readme_text = ""
        if readme and readme.get("content"):
            readme_text = base64.b64decode(re.sub(r"\s", "", readme["content"])).decode("utf-8", errors="replace")
        candidate.readme_chars = len(readme_text)
        track_context = f"{candidate.description}\n{readme_text}"
        for match in re.finditer(
            r"(?:problem\s+statement|problem|track|ps)\s*[-:#]?\s*([1-8])\b",
            track_context,
            re.IGNORECASE,
        ):
            candidate.tracks.add(TRACK_BY_NUMBER[int(match.group(1))])
        candidate.readme_event = bool(
            re.search(
                r"ET\s*(AI|GenAI)\s*Hackathon|Economic Times\s*(AI|GenAI)\s*Hackathon",
                readme_text,
                re.IGNORECASE,
            )
        )
        candidate.readme_video = bool(
            re.search(
                r"https?://[^\s)>]*(?:youtu\.be|youtube\.com|loom\.com|vimeo\.com|drive\.google\.com)[^\s)>]*",
                readme_text,
                re.IGNORECASE,
            )
        )
        candidate.readme_run = bool(
            re.search(
                r"getting started|quick\s*start|installation|npm\s+(run|start)|uvicorn|"
                r"streamlit\s+run|docker\s+compose|python\s+[^\n]+\.py",
                readme_text,
                re.IGNORECASE,
            )
        )

        commits = api_get(f"repos/{candidate.repo}/commits?per_page=100", token)
        candidate.commits_visible = len(commits or [])
    except Exception as exc:  # keep partial evidence and expose the failure
        candidate.error = f"{type(exc).__name__}: {exc}"

    candidate.confidence = classify_confidence(candidate)
    candidate.evidence_index = calculate_evidence_index(candidate)
    return candidate


def classify_confidence(candidate: Candidate) -> str:
    if candidate.event_match or candidate.readme_event:
        return "High"
    if candidate.tracks and (candidate.code_files > 0 or candidate.readme_chars > 200):
        return "Medium"
    return "Low"


def calculate_evidence_index(candidate: Candidate) -> int:
    if candidate.files == 0 and candidate.readme_chars == 0:
        return 0

    if candidate.code_files == 0:
        substance = 0
    elif candidate.code_files <= 5:
        substance = 5
    elif candidate.code_files <= 15:
        substance = 10
    elif candidate.code_files <= 40:
        substance = 15
    else:
        substance = 20

    engineering = 0
    engineering += min(8, 2 + int(math.log2(candidate.test_files + 1)) * 2) if candidate.test_files else 0
    engineering += 4 if candidate.ci_files else 0
    engineering += 3 if candidate.lockfiles else 0
    engineering += 3 if candidate.docker_files else 0
    engineering += 2 if candidate.commits_visible > 1 else 0

    evidence = 0
    evidence += min(8, 3 + int(math.log2(candidate.eval_files + 1)) * 2) if candidate.eval_files else 0
    evidence += 4 if candidate.data_files else 0
    evidence += 3 if candidate.architecture_files else 0
    evidence += 3 if candidate.impact_files else 0
    evidence += 2 if candidate.files >= 20 else 0

    deliverables = 0
    deliverables += 4 if candidate.readme_chars >= 1000 else (2 if candidate.readme_chars else 0)
    deliverables += 4 if candidate.architecture_files else 0
    deliverables += 4 if candidate.impact_files else 0
    deliverables += 3 if candidate.pitch_files else 0
    deliverables += 3 if candidate.readme_video or candidate.video_files else 0
    deliverables += 2 if candidate.homepage else 0

    runnable = 0
    runnable += 5 if candidate.readme_run else 0
    runnable += 2 if candidate.homepage else 0
    runnable += 2 if candidate.lockfiles else 0
    runnable += 1 if candidate.junk_files == 0 else 0

    provenance = {"High": 6, "Medium": 3, "Low": 0}[candidate.confidence]
    provenance += min(4, candidate.commits_visible - 1) if candidate.commits_visible > 1 else 0

    penalty = 0
    if candidate.junk_files >= 20:
        penalty += 5
    if candidate.tree_truncated:
        penalty += 2
    if candidate.error:
        penalty += 3

    return max(
        0,
        min(
            100,
            substance + engineering + evidence + deliverables + runnable + provenance - penalty,
        ),
    )


def one_line_evidence(candidate: Candidate) -> str:
    positives: list[str] = []
    gaps: list[str] = []
    if candidate.code_files:
        positives.append(f"{candidate.code_files} code files")
    if candidate.test_files:
        positives.append(f"{candidate.test_files} test files")
    if candidate.ci_files:
        positives.append("CI")
    if candidate.eval_files:
        positives.append("evaluation artifacts")
    if candidate.architecture_files:
        positives.append("architecture artifact")
    if candidate.impact_files:
        positives.append("impact artifact")
    if candidate.pitch_files:
        positives.append("pitch artifact")
    if candidate.readme_video or candidate.video_files:
        positives.append("video artifact")
    if candidate.homepage:
        positives.append("live URL")
    if candidate.commits_visible:
        positives.append(
            f"{candidate.commits_visible}{'+' if candidate.commits_visible == 100 else ''} visible commit(s)"
        )

    if not candidate.test_files:
        gaps.append("no tests found")
    if not candidate.eval_files:
        gaps.append("no evaluation artifact found")
    if not candidate.architecture_files:
        gaps.append("no architecture file found")
    if not candidate.impact_files:
        gaps.append("no impact file found")
    if candidate.junk_files >= 20:
        gaps.append(f"{candidate.junk_files} generated/environment files")
    if not candidate.code_files:
        gaps.append("no source code found")
    if candidate.error:
        gaps.append("API enrichment incomplete")

    left = ", ".join(positives) if positives else "No positive repository signal"
    right = "; ".join(gaps[:3])
    return f"{left}. {right}." if right else f"{left}."


def write_outputs(candidates: list[Candidate], markdown_path: Path, json_path: Path) -> None:
    ranked = sorted(
        candidates,
        key=lambda item: (
            -item.evidence_index,
            -item.code_files,
            -item.test_files,
            item.repo.lower(),
        ),
    )
    confidence_counts = Counter(candidate.confidence for candidate in ranked)
    track_counts = Counter(track for candidate in ranked for track in (candidate.tracks or {"Unclassified"}))
    explicit_count = sum(1 for candidate in ranked if candidate.event_match)
    problem_only_count = sum(1 for candidate in ranked if not candidate.event_match)

    lines = [
        "# ET AI Hackathon 2.0 Public Repository Census",
        "",
        f"Generated: {datetime.now(UTC).isoformat(timespec='seconds')}",
        "",
        "> This is a public-discovery and repository-evidence triage appendix, not a judge-score table. "
        "The evidence index measures visible repository substance and artifacts; it cannot establish "
        "model correctness, demo quality, originality, or submission validity without deeper review.",
        "",
        "## Coverage",
        "",
        f"- Unique plausible repositories found: **{len(ranked)}**",
        f"- Exact event-name matches: **{explicit_count}**",
        f"- Problem-title-only additions: **{problem_only_count}**",
        (
            f"- Confidence: **{confidence_counts['High']} high**, "
            f"**{confidence_counts['Medium']} medium**, **{confidence_counts['Low']} low**"
        ),
        (
            "- Discovery window: repositories created on or after 2026-06-15; "
            "snapshot is mid-sprint and will change before the 2026-07-22 deadline."
        ),
        "",
        "Track-query counts are non-exclusive:",
        "",
    ]
    for track, count in sorted(track_counts.items()):
        lines.append(f"- {track}: {count}")

    lines.extend(
        [
            "",
            "## Method",
            "",
            "Discovery used GitHub repository search for the exact event name and eight "
            "official problem-title fragments. "
            "Each repository was enriched through its recursive tree, README, and up to 100 visible commits. "
            "Generated environments and dependency trees are excluded from source/test counts "
            "and penalized when committed.",
            "",
            "Index components: source substance (20), engineering signals (20), evidence artifacts (20), "
            "required/presentation artifacts (20), run/deploy signals (10), and event/provenance confidence (10). "
            "This index is used only to order the census and choose repositories for human review.",
            "",
            "## Ranked Census",
            "",
            (
                "| Rank | Index | Confidence | Track | Repository | Declared purpose | "
                "Discovery source | One-line evidence |"
            ),
            "|---:|---:|---|---|---|---|---|---|",
        ]
    )
    for rank, candidate in enumerate(ranked, start=1):
        evidence = one_line_evidence(candidate).replace("|", "\\|")
        track = candidate.track_label.replace("|", "\\|")
        purpose = re.sub(r"\s+", " ", candidate.description).strip()
        purpose = purpose.replace("â€”", "-").replace("â€“", "-").replace("â€™", "'")
        purpose = (purpose or "Not declared in GitHub metadata").encode("ascii", errors="ignore").decode()
        if len(purpose) > 180:
            purpose = purpose[:177].rstrip() + "..."
        purpose = purpose.replace("|", "\\|")
        if candidate.event_match and candidate.tracks:
            discovery_source = "event-name + problem-title queries"
        elif candidate.event_match:
            discovery_source = "event-name query"
        else:
            discovery_source = "problem-title query"
        lines.append(
            f"| {rank} | {candidate.evidence_index} | {candidate.confidence} | {track} | "
            f"[{candidate.repo}]({candidate.html_url}) | {purpose} | {discovery_source} | {evidence} |"
        )

    lines.extend(
        [
            "",
            "## Coverage Limits",
            "",
            "GitHub search is not a submission registry. Repositories can be missed when they use generic names, "
            "omit event/problem wording, are not indexed, were created before the search window, or are linked only "
            "inside authenticated Unstop pages. Conversely, an exact title match does not prove that a repository "
            "was submitted. Confidence labels reflect this distinction.",
            "",
            "Repository contents may also change before the deadline. Re-run the script for a fresh snapshot.",
        ]
    )

    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps([candidate.__dict__ | {"tracks": sorted(candidate.tracks)} for candidate in ranked], indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--markdown",
        type=Path,
        default=Path("docs/ET_AI_HACKATHON_PUBLIC_REPO_CENSUS_2026-07-10.md"),
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("docs/ET_AI_HACKATHON_PUBLIC_REPO_CENSUS_2026-07-10.json"),
    )
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required")

    candidates: dict[str, Candidate] = {}
    for item in search_repositories(EVENT_QUERY, token):
        merge_candidate(candidates, item, "event")
    for track, query in TRACK_QUERIES.items():
        for item in search_repositories(query, token):
            merge_candidate(candidates, item, track)

    print(f"Discovered {len(candidates)} unique candidates; enriching...")
    completed: list[Candidate] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(enrich_candidate, candidate, token): candidate.repo for candidate in candidates.values()
        }
        for index, future in enumerate(concurrent.futures.as_completed(future_map), start=1):
            completed.append(future.result())
            if index % 25 == 0 or index == len(future_map):
                print(f"Enriched {index}/{len(future_map)}")

    write_outputs(completed, args.markdown, args.json)
    print(f"Wrote {args.markdown} and {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
