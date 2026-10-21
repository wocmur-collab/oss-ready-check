# OSS Ready Check

A small, dependency-free Python CLI that scans a local project and prints a practical open-source release-readiness checklist. It only reads the target directory and never uploads or changes project files.

## Requirements

- Python 3.9 or newer
- No third-party runtime packages

## Run from source

From PowerShell:

```powershell
python .\oss_ready_check.py path\to\your-project
```

Scan the current directory:

```powershell
python .\oss_ready_check.py
```

Use `--strict` in automation to exit with status 1 when a README or license file is missing:

```powershell
python .\oss_ready_check.py path\to\your-project --strict
```

Get JSON for another script to consume:

```powershell
python .\oss_ready_check.py path\to\your-project --format json
```

## Install as a command

```powershell
python -m pip install .
oss-ready-check path\to\your-project
```

Installation uses the standard Python packaging build backend; the installed CLI has no third-party runtime dependencies.

The default report is Markdown and can be copied into an issue or release plan. Reports show the project directory's name rather than its full local path, so they are safer to share. Missing README and license files are marked essential; other checks are recommendations or optional signals. The tool prints suggestions for missing items.

## Checks

- README / project overview and license (essential)
- Contribution guide, code of conduct, security reporting guide, changelog, Git ignore rules, CI, package metadata, and test directory (recommended)
- Citation metadata (optional)

CI detection includes GitHub Actions, GitLab CI, CircleCI, Jenkins, Azure Pipelines, and Bitbucket Pipelines. This repository runs its test suite and strict CLI check on pushes and pull requests for Python 3.9 and the latest stable Python. Common project metadata includes Python, JavaScript, Rust, Go, Java, PHP, and Ruby manifests.

## Development

Run the standard-library test suite:

```powershell
python -m unittest discover -s tests -v
```

## Scope and limitations

This tool checks for common filenames and directories only. It does not inspect file contents, validate license compatibility, run a target project's tests, inspect Git history, or decide whether code is safe to publish. A file's presence is not proof that its contents are correct or that a project is ready to publish. `--strict` checks only for a README and license filename; it is not a general readiness score. Review secrets, personal information, dependencies, and commit history separately before making a repository public.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and pull requests are welcome. Please include a short explanation of the use case for new checks, and keep the default scan read-only and dependency-free.

## Security

Please do not report vulnerabilities in a public issue. See [SECURITY.md](SECURITY.md) for reporting guidance.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

