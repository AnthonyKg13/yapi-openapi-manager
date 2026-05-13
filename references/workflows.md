# Workflow Reference

## Verify Config and Access

1. Run `project get`
2. If it fails because config is missing, bootstrap config instead of retrying
3. If it fails with YApi error data, stop and surface `errmsg`

## Create a Category Then Add an Interface

1. Run `project get` to validate access
2. Run `category add --project-id ... --name ...`
3. Use the returned category ID, or confirm through `category list`
4. Build the interface payload in a JSON file
5. Run `interface add --file payload.json`

## Update an Existing Interface Safely

1. Find the interface through `interface list`, `interface list-menu`, or `interface get`
2. Prefer `interface save --file payload.json` when create-vs-update is not important
3. Use `interface update --file payload.json` only when `id` is definitely known and update-only behavior matters

## Import OpenAPI Data

1. Validate config with `project get`
2. Choose `merge` mode deliberately:
3. Use `normal` for ordinary imports
4. Use `good` for smarter merge behavior
5. Use `merge` for full overwrite semantics
6. Provide either `--url` or `--json-file`

## Discovery Patterns

- Use `category list` when only category metadata is needed
- Use `interface list-menu` when category and interface IDs are both needed
- Use `interface list-cat` for a focused view within one category
