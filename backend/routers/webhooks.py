from __future__ import annotations

import ipaddress
import logging
import os
import socket
import threading
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend import case_store
from backend.api_context import _require_case

router = APIRouter()
log = logging.getLogger("pramaan.api")

class WebhookSubscribeRequest(BaseModel):
    url: str


# Process-local, case-scoped integrations. Every mutation requires the owning
# case secret; public analysis cannot subscribe a receiver for another case.
SUBSCRIBED_WEBHOOKS: dict[str, list[dict]] = {}
MAX_WEBHOOKS = 10


def _resolved_webhook_addresses(url: str) -> tuple[str, ...]:
    parsed = urlparse(url)
    if not parsed.hostname:
        return ()
    infos = socket.getaddrinfo(
        parsed.hostname,
        parsed.port or (443 if parsed.scheme == "https" else 80),
        proto=socket.IPPROTO_TCP,
    )
    return tuple(sorted({str(ipaddress.ip_address(info[4][0])) for info in infos}))


def _webhook_host_error(host: str) -> str | None:
    if host == "localhost" or host.endswith((".local", ".internal")):
        return "Private/internal hosts are not allowed"
    return None


def _webhook_address_error(url: str) -> str | None:
    try:
        addresses = [ipaddress.ip_address(value) for value in _resolved_webhook_addresses(url)]
    except (OSError, ValueError):
        return "Hostname does not resolve"
    blocked = any(
        address.is_private or address.is_loopback or address.is_link_local or address.is_unspecified
        for address in addresses
    )
    return "Private/internal addresses are not allowed" if blocked else None


def _webhook_url_error(url: str) -> str | None:
    """Validate a subscriber URL; return an error message or None if OK.

    Blocks non-HTTP schemes and hosts that resolve to private/loopback/
    link-local addresses so the public demo can't be driven as an SSRF proxy
    into the backend's network (cloud metadata endpoints, localhost services).
    Set PRAMAAN_WEBHOOK_ALLOW_PRIVATE=1 to demo against a local receiver.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return "URL must be http(s) with a hostname"
    if os.getenv("PRAMAAN_WEBHOOK_ALLOW_PRIVATE", "0") == "1":
        return None
    return _webhook_host_error(parsed.hostname) or _webhook_address_error(url)


def _redact_webhook(url: str) -> str:
    """Subscriber URLs can embed secrets (Slack webhook tokens): show enough
    to recognize the subscription, never enough to replay it."""
    return url if len(url) <= 40 else url[:40] + "…"


def _deliver_webhooks(subscriptions: list[dict], payload: dict, slack_payload: dict) -> None:
    """POST to every subscriber (runs on a worker thread). One dead subscriber
    must never block delivery to the rest."""
    import httpx
    for subscription in subscriptions:
        url = str(subscription.get("url", ""))
        body = slack_payload if "hooks.slack.com" in url else payload
        try:
            if _webhook_url_error(url):
                continue
            # Rebinding guard, not an exact pin: CDN-backed receivers (Slack)
            # legitimately rotate part of their record set between subscribe
            # and delivery, so require an overlap with the subscribe-time set
            # rather than equality. A rebind to a fully different set is still
            # dropped, and _webhook_url_error above re-blocks private/loopback
            # targets on every delivery regardless.
            pinned = set(subscription.get("resolved_ips", ()))
            if not pinned or pinned.isdisjoint(_resolved_webhook_addresses(url)):
                log.warning("Webhook destination DNS changed; delivery dropped")
                continue
            httpx.post(url, json=body, timeout=2.0, follow_redirects=False)
        except Exception as exc:
            log.warning(
                "Webhook delivery failed for %s: %s",
                _redact_webhook(url),
                exc,
            )


def trigger_webhooks(
    deviations: list[dict], system_id: str, case_id: str | None = None,
) -> None:
    """Fan out Critical/Major findings to one owned case. Fire-and-forget: the
    payload is built defensively (LLM-produced dicts may miss keys) and
    delivery happens on a daemon thread, so a malformed deviation or a slow
    subscriber can never fail or delay an analysis response."""
    if not case_id:
        return
    try:
        subscriptions = SUBSCRIBED_WEBHOOKS.get(case_id, [])
        critical_or_major = [d for d in deviations if d.get("severity") in ("Critical", "Major")]
        if not critical_or_major or not subscriptions:
            return

        payload = {
            "event": "deviation_detected",
            "case_id": case_id,
            "system": system_id,
            "count": len(critical_or_major),
            "deviations": critical_or_major,
            "rfi_drafts": [
                f"DEVIATION RFI: Component {d.get('component', '?')} fails {d.get('parameter', '?')}. "
                f"Required: {d.get('required_value', '?')} {d.get('unit', '')}, "
                f"Provided: {d.get('provided_value', '?')} {d.get('unit', '')}. "
                f"Please clarify non-compliance."
                for d in critical_or_major
            ],
        }

        slack_text = (
            f"🚨 *Pramaan Alert*: {len(critical_or_major)} Critical/Major deviations "
            f"found in system {system_id}!\n"
            + "\n".join([
                f"• *{d.get('component', '?')}* ({d.get('parameter', '?')}): "
                f"Required {d.get('required_value', '?')} {d.get('unit', '')}, "
                f"got {d.get('provided_value', '?')} {d.get('unit', '')}."
                for d in critical_or_major
            ])
        )
        slack_payload = {"text": slack_text}

        threading.Thread(
            target=_deliver_webhooks,
            args=(list(subscriptions), payload, slack_payload),
            daemon=True,
        ).start()
    except Exception as exc:
        log.warning("Case webhook dispatch could not start for %s: %s", case_id, exc)


@router.post("/webhooks/subscribe")
def subscribe_webhook(req: WebhookSubscribeRequest):
    del req
    raise HTTPException(
        status_code=410,
        detail="Global webhooks were retired. Configure integrations inside an owned case.",
    )


@router.get("/webhooks")
def get_webhooks():
    raise HTTPException(
        status_code=410,
        detail="Global webhooks were retired. Use /cases/{case_id}/webhooks.",
    )


@router.delete("/webhooks")
def clear_webhooks():
    """Retired global mutation endpoint retained as an explicit 410."""
    raise HTTPException(
        status_code=410,
        detail="Global webhooks were retired. Use /cases/{case_id}/webhooks.",
    )


@router.post("/cases/{case_id}/webhooks")
def subscribe_case_webhook(
    case_id: str, req: WebhookSubscribeRequest, request: Request,
):
    secret = _require_case(case_id, request)
    url = req.url.strip()
    err = _webhook_url_error(url)
    if err:
        raise HTTPException(status_code=400, detail=err)
    try:
        resolved_ips = _resolved_webhook_addresses(url)
    except (OSError, ValueError):
        raise HTTPException(status_code=400, detail="Hostname does not resolve") from None

    subscriptions = SUBSCRIBED_WEBHOOKS.setdefault(case_id, [])
    if not any(item["url"] == url for item in subscriptions):
        if len(subscriptions) >= MAX_WEBHOOKS:
            raise HTTPException(
                status_code=429,
                detail=f"Integration limit ({MAX_WEBHOOKS}) reached for this case",
            )
        subscriptions.append({"url": url, "resolved_ips": resolved_ips})
        case_store.append_audit(
            case_id,
            case_store.actor_key_for(secret),
            "webhook_subscribed",
            detail=urlparse(url).hostname or "",
        )
    return {"status": "subscribed", "url": _redact_webhook(url)}


@router.get("/cases/{case_id}/webhooks")
def get_case_webhooks(case_id: str, request: Request):
    _require_case(case_id, request)
    subscriptions = SUBSCRIBED_WEBHOOKS.get(case_id, [])
    return {
        "count": len(subscriptions),
        "urls": [_redact_webhook(str(item["url"])) for item in subscriptions],
    }


@router.delete("/cases/{case_id}/webhooks")
def clear_case_webhooks(case_id: str, request: Request):
    secret = _require_case(case_id, request)
    cleared = len(SUBSCRIBED_WEBHOOKS.pop(case_id, []))
    case_store.append_audit(
        case_id,
        case_store.actor_key_for(secret),
        "webhooks_cleared",
        detail=str(cleared),
    )
    return {"cleared": cleared}
