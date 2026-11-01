"""Microstock+ agent API HTTP proxy workflow.

The token is supplied per execution input and is never stored or logged.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from pydantic import BaseModel

import mistralai.workflows as workflows

BASE_URL = "https://microstock.plus/api/agent/v1"
MAX_BYTES = 8 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


class ProxyInput(BaseModel):
    token: str
    method: str = "GET"
    path: str = "/me"
    query: dict = {}
    body: Optional[dict] = None


@workflows.activity()
async def call_api(token: str, method: str, path: str, query: dict, body: Any) -> dict:
    url = BASE_URL + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with _opener.open(req, timeout=15) as resp:
            status = resp.status
            raw = resp.read(MAX_BYTES).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            raw = e.read(MAX_BYTES).decode("utf-8", "replace")
        except Exception:
            raw = ""
    except Exception as e:
        return {"status": 0, "body": {"error": type(e).__name__, "message": str(e)[:500]}}
    try:
        parsed = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        parsed = raw[:2000]
    return {"status": status, "body": parsed}


@workflows.workflow.define(
    name="mplus-api",
    workflow_display_name="Microstock+ API proxy",
    workflow_description="Authenticated HTTP client for the Microstock+ agent API. Token supplied per execution.",
)
class MplusApiWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: ProxyInput) -> dict:
        return await call_api(input.token, input.method, input.path, input.query, input.body)
