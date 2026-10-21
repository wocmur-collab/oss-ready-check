"""Check a local project for common open-source release-readiness files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CHECKS: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    (
        "README / project overview",
        ("README.md", "README.rst", "README.txt", "README.markdown", "README.adoc", "README"),
        "Essential",
        "Explain what the project does, who it is for, and how to install or use it.",
    ),
    (
        "License",
        ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"),
        "Essential",
        "Choose a license you are authorized to apply and add its complete text.",
    ),
    (
        "Contribution guide",
        ("CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING"),
        "Recommended",
        "Describe how to report issues, propose changes, and run project checks.",
    ),
    (
        "Code of conduct",
        ("CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.rst"),
        "Recommended",
        "Set expectations for respectful participation and explain how concerns are handled.",
    ),
    (
        "Security reporting guide",
        ("SECURITY.md", "SECURITY.rst"),
        "Recommended",
        "Explain how to report vulnerabilities privately and what versions are supported.",
    ),
    (
        "Changelog / release notes",
        ("CHANGELOG.md", "CHANGES.md", "HISTORY.md", "RELEASES.md"),
        "Recommended",
        "Record user-visible changes for releases.",
    ),
    (
        "Citation metadata",
        ("CITATION.cff",),
        "Optional",
        "Add citation metadata if users may need to cite this project in research.",
    ),
    (
        "Git ignore rules",
        (".gitignore",),
        "Recommended",
        "Ignore generated files, local environments, and other files that should not be committed.",
    ),
)

PROJECT_METADATA = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "composer.json",
    "Gemfile",
)
CI_CONFIGS = (
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "Jenkinsfile",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
)


def find_first_file(root: Path, candidates: tuple[str, ...]) -> Path | None:
    by_lower_name = {path.name.lower(): path for path in root.iterdir() if path.is_file()}
    for candidate in candidates:
        found = by_lower_name.get(candidate.lower())
        if found:
            return found
    return None


def scan(root: Path) -> list[tuple[str, str, str, str, str]]:
    """Return (priority, status, check, detail, suggestion) rows read-only."""
    rows: list[tuple[str, str, str, str, str]] = []

    for label, candidates, priority, suggestion in CHECKS:
        found = find_first_file(root, candidates)
        if found:
            rows.append((priority, "Found", label, f"`{found.relative_to(root).as_posix()}`", ""))
        else:
            rows.append((priority, "Missing", label, "No common filename found", suggestion))

    ci_files: list[Path] = []
    github_workflows = root / ".github" / "workflows"
    if github_workflows.is_dir():
        ci_files.extend(
            path for path in github_workflows.glob("*")
            if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
        )
    for config in CI_CONFIGS:
        candidate = root / config
        if candidate.is_file():
            ci_files.append(candidate)
    if ci_files:
        names = ", ".join(f"`{path.relative_to(root).as_posix()}`" for path in sorted(set(ci_files)))
        rows.append(("Recommended", "Found", "CI workflow", names, ""))
    else:
        rows.append((
            "Recommended",
            "Missing",
            "CI workflow",
            "No YAML workflow found under `.github/workflows/`",
            "Add a workflow for the checks contributors should run before changes are merged.",
        ))

    metadata = find_first_file(root, PROJECT_METADATA)
    if metadata:
        rows.append(("Recommended", "Found", "Project/package metadata", f"`{metadata.name}`", ""))
    else:
        rows.append((
            "Recommended",
            "Missing",
            "Project/package metadata",
            "No common package manifest found",
            "Add package metadata if the project needs to be built, installed, or published as a package.",
        ))

    test_dirs = [
        path.name for path in root.iterdir()
        if path.is_dir() and path.name.lower() in {"tests", "test", "spec"}
    ]
    if test_dirs:
        rows.append(("Recommended", "Found", "Test directory", ", ".join(f"`{name}/`" for name in test_dirs), ""))
    else:
        rows.append((
            "Recommended",
            "Missing",
            "Test directory",
            "No `tests/` or `test/` directory found",
            "Add tests for the behavior that matters most to users.",
        ))

    return rows


def render_markdown(project_label: str, rows: list[tuple[str, str, str, str, str]]) -> str:
    found = sum(status == "Found" for _, status, _, _, _ in rows)
    missing_essential = [check for priority, status, check, _, _ in rows if priority == "Essential" and status == "Missing"]
    missing_recommended = [
        check for priority, status, check, _, _ in rows if priority == "Recommended" and status == "Missing"
    ]
    lines = [
        f"# OSS readiness checklist: `{project_label}`",
        "",
        "> Presence checks only; review the contents and project-specific requirements yourself.",
        "",
        "| Priority | Status | Check | Details |",
        "|---|---|---|---|",
    ]
    for priority, status, check, detail, _ in rows:
        escaped_detail = detail.replace("|", "\\|")
        lines.append(f"| {priority} | {status} | {check} | {escaped_detail} |")
    lines.extend([
        "",
        f"**Summary:** {found}/{len(rows)} common signals found. This is not a readiness score or certification.",
    ])

    for title, expected_priority, missing in (
        ("Essential next steps", "Essential", missing_essential),
        ("Other suggested improvements", "Recommended", missing_recommended),
    ):
        if missing:
            lines.extend(["", f"## {title}"])
            for priority, status, check, _, suggestion in rows:
                if priority == expected_priority and status == "Missing":
                    lines.append(f"- **{check}:** {suggestion}")
    return "\n".join(lines) + "\n"


def render_json(project_label: str, rows: list[tuple[str, str, str, str, str]]) -> str:
    found = sum(status == "Found" for _, status, _, _, _ in rows)
    report = {
        "project": project_label,
        "summary": {
            "found": found,
            "total": len(rows),
            "missing_essential": [
                check for priority, status, check, _, _ in rows if priority == "Essential" and status == "Missing"
            ],
            "missing_recommended": [
                check for priority, status, check, _, _ in rows if priority == "Recommended" and status == "Missing"
            ],
            "is_certification": False,
        },
        "checks": [
            {
                "priority": priority.lower(),
                "status": status.lower(),
                "check": check,
                "details": detail,
                "suggestion": suggestion or None,
            }
            for priority, status, check, detail, suggestion in rows
        ],
    }
    return json.dumps(report, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a read-only checklist of common open-source release-readiness files."
    )
    parser.add_argument("path", nargs="?", default=".", help="Project directory to scan (default: current directory)")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="report format (default: markdown)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit with status 1 if a README or license file is missing",
    )
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"not a directory: {root}")

    rows = scan(root)
    missing_essential = [check for priority, status, check, _, _ in rows if priority == "Essential" and status == "Missing"]
    # Avoid placing machine-specific paths (which can contain usernames) in a
    # report that users may paste into a public issue.
    project_label = root.name or root.drive or "project"
    report = render_markdown(project_label, rows) if args.format == "markdown" else render_json(project_label, rows)
    print(report, end="")
    return 1 if args.strict and missing_essential else 0


if __name__ == "__main__":
    raise SystemExit(main())
