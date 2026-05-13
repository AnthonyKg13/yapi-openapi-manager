#!/usr/bin/env python3
"""CLI wrapper around the documented YApi OpenAPI endpoints."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_NAME = ".yapi-openapi.json"
DEFAULT_TIMEOUT_MS = 15000
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ASSET_CONFIG_TEMPLATE = SKILL_DIR / "assets" / ".yapi-openapi.example.json"

JSON_FILE_COMMANDS = {
    ("interface", "add"),
    ("interface", "save"),
    ("interface", "update"),
}

ENDPOINTS = {
    ("project", "get"): ("GET", "/api/project/get"),
    ("category", "add"): ("POST_FORM", "/api/interface/add_cat"),
    ("category", "list"): ("GET", "/api/interface/getCatMenu"),
    ("interface", "get"): ("GET", "/api/interface/get"),
    ("interface", "list-cat"): ("GET", "/api/interface/list_cat"),
    ("interface", "list"): ("GET", "/api/interface/list"),
    ("interface", "list-menu"): ("GET", "/api/interface/list_menu"),
    ("interface", "add"): ("POST_JSON", "/api/interface/add"),
    ("interface", "save"): ("POST_JSON", "/api/interface/save"),
    ("interface", "update"): ("POST_JSON", "/api/interface/up"),
    ("import-data", None): ("POST_FORM", "/api/open/import_data"),
}


class CliError(Exception):
    """Raised for expected CLI failures."""


def json_dump(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, separators=(",", ":")))


def fail(message: str, *, exit_code: int = 1, **extra: Any) -> int:
    payload: dict[str, Any] = {"ok": False, "error": message}
    payload.update(extra)
    json_dump(payload)
    return exit_code


def resolve_config_path(config_arg: str | None) -> Path:
    if config_arg:
        return Path(config_arg).expanduser().resolve()
    return (Path.cwd() / DEFAULT_CONFIG_NAME).resolve()


def validate_config(raw: Any, path: Path) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise CliError(f"Config at {path} must be a JSON object.")

    base_url = raw.get("baseUrl")
    token = raw.get("token")
    timeout_ms = raw.get("timeoutMs", DEFAULT_TIMEOUT_MS)

    if not isinstance(base_url, str) or not base_url.strip():
        raise CliError("Config field 'baseUrl' is required and must be a non-empty string.")
    if "openapi-doc.html" in base_url:
        raise CliError("Config field 'baseUrl' must be the YApi host root, not the docs page URL.")
    if not isinstance(token, str) or not token.strip():
        raise CliError("Config field 'token' is required and must be a non-empty string.")
    if not isinstance(timeout_ms, int) or timeout_ms <= 0:
        raise CliError("Config field 'timeoutMs' must be a positive integer when provided.")

    return {
        "baseUrl": base_url.rstrip("/"),
        "token": token.strip(),
        "timeoutMs": timeout_ms,
        "configPath": str(path),
    }


def load_config(config_arg: str | None) -> dict[str, Any]:
    path = resolve_config_path(config_arg)
    if not path.exists():
        raise CliError(
            "YApi config not found. Run 'python scripts/yapi_openapi.py init-config' from your project root, then fill in .yapi-openapi.json.",
        )
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise CliError(
            f"Config at {path} is not valid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}.",
        ) from exc
    return validate_config(raw, path)


def load_json_file(path_str: str) -> Any:
    path = Path(path_str).expanduser().resolve()
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise CliError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CliError(
            f"JSON file at {path} is not valid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}.",
        ) from exc


def init_config() -> int:
    destination = Path.cwd() / DEFAULT_CONFIG_NAME
    if destination.exists():
        return fail(
            "Project config already exists.",
            path=str(destination),
            template=str(ASSET_CONFIG_TEMPLATE),
        )
    shutil.copyfile(ASSET_CONFIG_TEMPLATE, destination)
    json_dump(
        {
            "ok": True,
            "message": "Created project config template. Fill in baseUrl and token before retrying API commands.",
            "path": str(destination.resolve()),
            "template": str(ASSET_CONFIG_TEMPLATE),
        }
    )
    return 0


def build_payload(args: argparse.Namespace, config: dict[str, Any]) -> tuple[str, str, dict[str, Any] | str]:
    key = (args.resource, args.action)
    method, endpoint = ENDPOINTS[key]
    token = config["token"]

    if key == ("project", "get"):
        return method, endpoint, {"token": token}
    if key == ("category", "add"):
        payload = {
            "token": token,
            "project_id": args.project_id,
            "name": args.name,
        }
        if args.desc is not None:
            payload["desc"] = args.desc
        return method, endpoint, payload
    if key == ("category", "list"):
        return method, endpoint, {"token": token, "project_id": args.project_id}
    if key == ("interface", "get"):
        return method, endpoint, {"token": token, "id": args.id}
    if key == ("interface", "list-cat"):
        payload = {"token": token, "catid": args.catid}
        if args.page is not None:
            payload["page"] = args.page
        if args.limit is not None:
            payload["limit"] = args.limit
        return method, endpoint, payload
    if key == ("interface", "list"):
        payload = {"token": token, "project_id": args.project_id}
        if args.page is not None:
            payload["page"] = args.page
        if args.limit is not None:
            payload["limit"] = args.limit
        return method, endpoint, payload
    if key == ("interface", "list-menu"):
        return method, endpoint, {"token": token, "project_id": args.project_id}
    if key in JSON_FILE_COMMANDS:
        payload = load_json_file(args.file)
        if not isinstance(payload, dict):
            raise CliError("Interface payload file must contain a JSON object.")
        payload = dict(payload)
        payload["token"] = token
        return method, endpoint, payload
    if key == ("import-data", None):
        payload: dict[str, Any] = {
            "token": token,
            "type": args.type,
            "merge": args.merge,
        }
        if args.url:
            payload["url"] = args.url
        if args.json_file:
            json_value = load_json_file(args.json_file)
            payload["json"] = json.dumps(json_value, ensure_ascii=False, separators=(",", ":"))
        if "url" not in payload and "json" not in payload:
            raise CliError("import-data requires either --url or --json-file.")
        return method, endpoint, payload
    raise CliError(f"Unsupported command: {args.resource} {args.action}")


def send_request(config: dict[str, Any], method: str, endpoint: str, payload: dict[str, Any] | str) -> dict[str, Any]:
    base_url = config["baseUrl"]
    timeout_seconds = config["timeoutMs"] / 1000

    if method == "GET":
        query = urllib.parse.urlencode(payload)
        url = f"{base_url}{endpoint}?{query}"
        request = urllib.request.Request(url, method="GET")
    elif method == "POST_FORM":
        body = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{base_url}{endpoint}",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
    elif method == "POST_JSON":
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{base_url}{endpoint}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
    else:
        raise CliError(f"Unsupported HTTP method wrapper: {method}")

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise CliError(f"HTTP {exc.code} calling {endpoint}: {body}") from exc
    except urllib.error.URLError as exc:
        raise CliError(f"Network error calling {endpoint}: {exc.reason}") from exc

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise CliError(f"YApi response from {endpoint} was not valid JSON: {exc.msg}") from exc

    if isinstance(data, dict) and data.get("errcode") not in (None, 0):
        raise CliError(
            f"YApi returned errcode {data.get('errcode')}: {data.get('errmsg', 'unknown error')}",
        )
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage YApi through its documented OpenAPI endpoints.")
    parser.add_argument("--config", help="Path to config JSON. Defaults to ./.yapi-openapi.json")

    subparsers = parser.add_subparsers(dest="resource", required=True)

    init_parser = subparsers.add_parser("init-config", help="Copy the example config into the current project.")
    init_parser.set_defaults(action=None)

    project_parser = subparsers.add_parser("project", help="Project-level operations")
    project_sub = project_parser.add_subparsers(dest="action", required=True)
    project_sub.add_parser("get", help="Fetch project metadata")

    category_parser = subparsers.add_parser("category", help="Category operations")
    category_sub = category_parser.add_subparsers(dest="action", required=True)
    category_add = category_sub.add_parser("add", help="Create a category")
    category_add.add_argument("--project-id", required=True, type=int)
    category_add.add_argument("--name", required=True)
    category_add.add_argument("--desc")
    category_list = category_sub.add_parser("list", help="List category menu data")
    category_list.add_argument("--project-id", required=True, type=int)

    interface_parser = subparsers.add_parser("interface", help="Interface operations")
    interface_sub = interface_parser.add_subparsers(dest="action", required=True)
    interface_get = interface_sub.add_parser("get", help="Fetch one interface")
    interface_get.add_argument("--id", required=True, type=int)
    interface_list_cat = interface_sub.add_parser("list-cat", help="List interfaces in a category")
    interface_list_cat.add_argument("--catid", required=True, type=int)
    interface_list_cat.add_argument("--page", type=int)
    interface_list_cat.add_argument("--limit", type=int)
    interface_list = interface_sub.add_parser("list", help="List interfaces in a project")
    interface_list.add_argument("--project-id", required=True, type=int)
    interface_list.add_argument("--page", type=int)
    interface_list.add_argument("--limit", type=int)
    interface_list_menu = interface_sub.add_parser("list-menu", help="List category and interface menu data")
    interface_list_menu.add_argument("--project-id", required=True, type=int)
    for action_name in ("add", "save", "update"):
        action_parser = interface_sub.add_parser(action_name, help=f"{action_name} an interface using a JSON payload file")
        action_parser.add_argument("--file", required=True, help="Path to a JSON payload file")

    import_parser = subparsers.add_parser("import-data", help="Import Swagger/OpenAPI data")
    import_parser.set_defaults(action=None)
    import_parser.add_argument("--type", required=True, choices=["swagger"])
    import_parser.add_argument("--merge", required=True, choices=["normal", "good", "merge"])
    import_parser.add_argument("--url")
    import_parser.add_argument("--json-file")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.resource == "init-config":
            return init_config()
        config = load_config(args.config)
        method, endpoint, payload = build_payload(args, config)
        response = send_request(config, method, endpoint, payload)
    except CliError as exc:
        return fail(str(exc))

    json_dump({"ok": True, "endpoint": endpoint, "method": method, "data": response})
    return 0


if __name__ == "__main__":
    sys.exit(main())
