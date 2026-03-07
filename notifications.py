import httpx
import asyncio
import logging
import random
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BaseNotificationService:
    """
    Common notification logic for Discord and Telegram.
    Can be used by composition in ApiLicense and Core.
    """
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        self._client = http_client or httpx.AsyncClient(timeout=30)

    async def _send_to_discord(
        self, 
        webhook_url: str, 
        event_type: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        footer: str = "Monitoring"
    ) -> bool:
        colors = {"error": 0xe74c3c, "critical": 0xe74c3c, "success": 0x2ecc71, "warning": 0xf1c40f}
        embed = {
            "title": f"🔔 {event_type.upper()}", 
            "description": message, 
            "color": colors.get(event_type.lower(), 0x3498db), 
            "fields": [], 
            "footer": {"text": footer}
        }
        if details:
            for k, v in details.items():
                embed["fields"].append({"name": k, "value": str(v), "inline": True})
        
        try:
            resp = await self._client.post(webhook_url, json={"embeds": [embed]})
            return resp.status_code < 400
        except Exception as e:
            logger.error(f"[BaseNotification] Discord failed: {e}")
            return False

    async def _send_to_telegram(
        self, 
        token: str, 
        chat_id: str, 
        event_type: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        prefix: str = "Suite"
    ) -> bool:
        emojis = {"error": "🚨", "critical": "🚨", "success": "✅", "warning": "⚠️", "info": "ℹ️"}
        text = f"{emojis.get(event_type.lower(), '🔔')} <b>{prefix}: {event_type.upper()}</b>\n\n{message}\n"
        if details:
            text += "\n<b>Details:</b>\n" + "\n".join([f"• <b>{k}:</b> {v}" for k, v in details.items()])
        
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        
        # Hardcoded fallback IPs for api.telegram.org
        fallback_ips = ["149.154.167.220", "149.154.167.99"]
        
        # Try hostname first, then fallback IPs if resolution fails
        endpoints = ["https://api.telegram.org"] + [f"https://{ip}" for ip in fallback_ips]
        
        for base_url in endpoints:
            url = f"{base_url}/bot{token}/sendMessage"
            headers = {"Host": "api.telegram.org"} if "telegram.org" not in base_url else {}
            
            try:
                # We use verify=False only for IP-based fallbacks if needed, 
                # but better to keep it True and rely on Host header if httpx supports it
                # Actually httpx doesn't easily support SNI with IP out of the box without custom transport
                # So we just try to be resilient with retries first
                resp = await self._client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    return True
                logger.warning(f"[BaseNotification] Telegram {base_url} returned {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.debug(f"[BaseNotification] Telegram attempt {base_url} failed: {e}")
                if base_url == endpoints[0]: # If the hostname failed, we continue to IPs
                    continue
                break # If IPs also fail or we finished, stop
        
        logger.error(f"[BaseNotification] Telegram failed after trying all endpoints.")
        return False
