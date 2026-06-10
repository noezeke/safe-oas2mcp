from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import anyio
import typer
from rich.console import Console
from rich.table import Table

from safe_oas2mcp.config import ConfigError, load_config
from safe_oas2mcp.gateway import SafeGateway
from safe_oas2mcp.mcp.server import create_mcp_server, run_stdio_server
from safe_oas2mcp.openapi.loader import OpenAPILoadError, load_openapi
from safe_oas2mcp.openapi.parser import OpenAPIParseError, parse_openapi
from safe_oas2mcp.openapi.tools import build_tool_metadata
from safe_oas2mcp.policy.engine import evaluate_operation_risk


app = typer.Typer(help="OpenAPI to MCP, safely.")


@app.callback()
def main() -> None:
    """Safe OpenAPI to MCP gateway."""


@app.command("inspect")
def inspect_command(
    spec_file: Annotated[Path, typer.Argument(help="Path to openapi.yaml or openapi.json")],
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: table or json"),
    ] = "table",
    config_path: Annotated[
        Path | None,
        typer.Option("--config", help="Path to safe-oas2mcp.config.yaml"),
    ] = None,
) -> None:
    """Inspect which MCP tools would be generated."""
    try:
        payload = inspect_openapi(spec_file, config_path=config_path)
    except (OpenAPILoadError, OpenAPIParseError, ConfigError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if output_format == "json":
        typer.echo(json.dumps(payload, indent=2))
        return

    if output_format != "table":
        typer.echo("Error: --format must be either 'table' or 'json'", err=True)
        raise typer.Exit(code=1)

    _render_table(payload)


def inspect_openapi(
    spec_file: Path,
    config_path: Path | None = None,
) -> dict[str, Any]:
    document = load_openapi(spec_file)
    operations = parse_openapi(document)
    config = load_config(config_path)
    used_names: set[str] = set()
    tools: list[dict[str, Any]] = []

    for operation in operations:
        metadata = build_tool_metadata(operation, used_names)
        risk = evaluate_operation_risk(operation, config.policy)
        tools.append(
            {
                "name": metadata.name,
                "description": metadata.description,
                "method": operation.method,
                "path": operation.path,
                "risk": risk.risk,
                "status": risk.status,
                "reasons": risk.reasons,
                "inputSchema": metadata.input_schema,
            }
        )

    return {
        "tools": tools,
        "summary": {
            "total": len(tools),
            "enabled": _count_status(tools, "enabled"),
            "confirm": _count_status(tools, "confirm"),
            "disabled": _count_status(tools, "disabled"),
        },
    }


@app.command("serve")
def serve_command(
    spec_file: Annotated[Path, typer.Argument(help="Path to openapi.yaml or openapi.json")],
    config_path: Annotated[
        Path | None,
        typer.Option("--config", help="Path to safe-oas2mcp.config.yaml"),
    ] = None,
) -> None:
    """Start an MCP stdio server for the OpenAPI document."""
    try:
        gateway = build_gateway_from_files(spec_file, config_path)
    except (OpenAPILoadError, OpenAPIParseError, ConfigError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    server = create_mcp_server(gateway)
    anyio.run(run_stdio_server, server)


def build_gateway_from_files(
    spec_file: Path,
    config_path: Path | None,
) -> SafeGateway:
    document = load_openapi(spec_file)
    operations = parse_openapi(document)
    config = load_config(config_path)
    return SafeGateway(operations=operations, config=config)


def _render_table(payload: dict[str, Any]) -> None:
    table = Table(title="safe-oas2mcp inspect")
    table.add_column("Tool", no_wrap=True)
    table.add_column("Method", no_wrap=True)
    table.add_column("Path", no_wrap=True)
    table.add_column("Risk", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Reasons", no_wrap=True)

    for tool in payload["tools"]:
        table.add_row(
            tool["name"],
            tool["method"],
            tool["path"],
            tool["risk"],
            tool["status"],
            "; ".join(tool["reasons"]),
        )

    console = Console(width=300)
    console.print(table)
    summary = payload["summary"]
    console.print(
        "Summary: "
        f"total={summary['total']} "
        f"enabled={summary['enabled']} "
        f"confirm={summary['confirm']} "
        f"disabled={summary['disabled']}"
    )


def _count_status(tools: list[dict[str, Any]], status: str) -> int:
    return sum(1 for tool in tools if tool["status"] == status)
