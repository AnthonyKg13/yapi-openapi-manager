# Endpoint Reference

All requests use the documented YApi OpenAPI surface and the project `token`.

## Project

### `project get`

- Path: `/api/project/get`
- Method: `GET`
- Required params: `token`
- Use to verify config and retrieve project metadata before writes

## Category

### `category add`

- Path: `/api/interface/add_cat`
- Method: `POST`
- Content type: `application/x-www-form-urlencoded`
- Required fields: `project_id`, `name`, `token`
- Optional fields: `desc`

### `category list`

- Path: `/api/interface/getCatMenu`
- Method: `GET`
- Required params: `project_id`, `token`

## Interface Read

### `interface get`

- Path: `/api/interface/get`
- Method: `GET`
- Required params: `id`, `token`
- Returns full interface detail, including request and response schema fields

### `interface list-cat`

- Path: `/api/interface/list_cat`
- Method: `GET`
- Required params: `catid`, `token`
- Optional params: `page`, `limit`

### `interface list`

- Path: `/api/interface/list`
- Method: `GET`
- Required params: `project_id`, `token`
- Optional params: `page`, `limit`

### `interface list-menu`

- Path: `/api/interface/list_menu`
- Method: `GET`
- Required params: `project_id`, `token`
- Useful when the agent needs category plus interface IDs in one response

## Interface Write

### `interface add`

- Path: `/api/interface/add`
- Method: `POST`
- Content type: `application/json`
- Use for create-only flows
- The payload is a JSON object mirroring YApi interface fields such as `title`, `path`, `method`, `catid`, `req_*`, `res_body`, and `desc`

### `interface save`

- Path: `/api/interface/save`
- Method: `POST`
- Content type: `application/json`
- Use as the default upsert-style command
- Accepts the same payload shape as `interface add`, and can include `id` when updating an existing interface

### `interface update`

- Path: `/api/interface/up`
- Method: `POST`
- Content type: `application/json`
- Use when the target interface `id` is known and update-only semantics are desired

## Import

### `import-data`

- Path: `/api/open/import_data`
- Method: `POST`
- Content type: `application/x-www-form-urlencoded`
- Required fields: `type`, `merge`, `token`
- Optional fields: `json`, `url`
- `merge` values documented by YApi: `normal`, `good`, `merge`
- `json` must be a serialized string, not a raw nested object

## Response Handling

- Successful responses typically return `errcode: 0`
- Treat non-zero `errcode` as failure even if HTTP status is `200`
- Preserve YApi `errmsg` in surfaced errors
