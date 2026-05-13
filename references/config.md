# Config Reference

## Default Path

The skill reads `.yapi-openapi.json` from the current working directory unless `--config` is provided.

Use project-local config so each repository can target its own YApi instance and token.

## Required Fields

```json
{
  "baseUrl": "https://your-yapi.example.com",
  "token": "project-token",
  "timeoutMs": 15000
}
```

- `baseUrl`: YApi host root, without the docs suffix. Example: `https://yapi.company.internal`
- `token`: project token used by the documented OpenAPI endpoints
- `timeoutMs`: optional integer timeout in milliseconds; defaults to `15000`

## Bootstrap Rules

When config is missing:

1. Run `python scripts/yapi_openapi.py init-config`
2. This copies `assets/.yapi-openapi.example.json` into the current project as `.yapi-openapi.json`
3. Tell the user to replace placeholder values before retrying any API command

When config is invalid:

- Treat malformed JSON as a setup error
- Surface which required field is missing
- Remind the user that the file must live in the project root unless `--config` is passed

## Common Failures

- `baseUrl` points to the docs page instead of the host root
- `token` is blank or still contains the placeholder string
- The command was run from the wrong working directory
- `timeoutMs` is not a positive integer
