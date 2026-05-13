---
name: yapi-openapi-manager
description: Manage YApi projects, categories, interfaces, and OpenAPI imports through the documented YApi OpenAPI endpoints. Use when Codex needs to inspect YApi project metadata, list categories or interfaces, create categories, add or update interfaces, or import Swagger/OpenAPI data for a YApi project from a local project directory.
---

# YApi OpenAPI Manager

Use the bundled script to manage YApi through its documented OpenAPI surface. Prefer the script over handwritten `curl` so requests, config loading, and error handling stay consistent.

## Quick Start

1. Check whether `.yapi-openapi.json` exists in the current project.
2. If it does not exist, run `python scripts/yapi_openapi.py init-config` from the skill directory, then tell the user to fill in the generated config in their project root.
3. After config exists, use `python scripts/yapi_openapi.py ...` subcommands for all reads and writes.

The default config contract is:

```json
{
  "baseUrl": "https://your-yapi.example.com",
  "token": "project-token",
  "timeoutMs": 15000
}
```

## Workflow

### Bootstrap

- Treat missing config as a setup task, not an API failure.
- Point the user to `assets/.yapi-openapi.example.json` and the generated project-local `.yapi-openapi.json`.
- Require `baseUrl` and `token` before any API call.

### Preferred Operations

- Use `project get` to verify access before any write flow.
- Use `category list` or `interface list-menu` to discover IDs before creating or updating interfaces.
- Prefer `interface save` when the user wants upsert-style behavior.
- Use `interface add` only for create-only flows.
- Use `interface update` only when the interface `id` is already known and update-only semantics matter.
- Use `import-data` for Swagger/OpenAPI imports.

## Command Patterns

```bash
python scripts/yapi_openapi.py init-config
python scripts/yapi_openapi.py project get
python scripts/yapi_openapi.py category list --project-id 123
python scripts/yapi_openapi.py category add --project-id 123 --name "User APIs"
python scripts/yapi_openapi.py interface get --id 1001
python scripts/yapi_openapi.py interface save --file payload.json
python scripts/yapi_openapi.py import-data --type swagger --merge good --url https://example.com/openapi.json
```

## References

- Read `references/config.md` when handling first-use setup, config errors, or path assumptions.
- Read `references/endpoints.md` when you need endpoint-specific fields, payload shapes, or response caveats.
- Read `references/workflows.md` when the task spans multiple API calls, especially category discovery plus interface changes.
