from pathlib import Path


def test_readme_contains_core_open_source_sections():
    readme = Path("README.md").read_text(encoding="utf-8")

    required = [
        "OpenAPI to MCP, safely.",
        "safe-oas2mcp inspect",
        "safe-oas2mcp serve",
        "Security Defaults",
        "Configuration",
        "MCP Client Setup",
        "Roadmap",
    ]

    for text in required:
        assert text in readme


def test_example_documentation_exists():
    for path in [
        Path("examples/todo/README.md"),
        Path("examples/todo/mock_server.py"),
        Path("examples/petstore/README.md"),
        Path("examples/github-readonly/README.md"),
        Path("examples/github-readonly/openapi.yaml"),
        Path("examples/github-readonly/safe-oas2mcp.config.example.yaml"),
    ]:
        assert path.exists(), f"Missing {path}"


def test_project_metadata_and_ci_files_exist():
    for path in [
        Path(".github/workflows/ci.yml"),
        Path("Dockerfile"),
        Path("SECURITY.md"),
        Path("CONTRIBUTING.md"),
        Path("CHANGELOG.md"),
        Path("docs/clients/claude-desktop.md"),
        Path("docs/clients/cursor.md"),
        Path("docs/clients/windsurf.md"),
        Path("docs/clients/troubleshooting.md"),
        Path("docs/release.md"),
        Path(".github/ISSUE_TEMPLATE/bug_report.yml"),
        Path(".github/ISSUE_TEMPLATE/feature_request.yml"),
        Path(".github/pull_request_template.md"),
    ]:
        assert path.exists(), f"Missing {path}"
