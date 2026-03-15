

import httpx
import asyncio
import logging
import random
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BaseNotificationService:

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
            resp = await self._client.post(webhook_url, json={"embeds": [embed]}, timeout=15.0)
            if resp.status_code >= 400:
                logger.error(f"[BaseNotification] Discord error {resp.status_code}: {resp.text}")
            return resp.status_code < 400
        except Exception as e:
            logger.error(f"[BaseNotification] Discord critical failure: {str(e)}")
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

        fallback_ips = ["149.154.167.220", "149.154.167.99"]

        endpoints = ["https://api.telegram.org"] + [f"https://{ip}" for ip in fallback_ips]

        for base_url in endpoints:
            is_ip = any(ip in base_url for ip in fallback_ips)
            url = f"{base_url}/bot{token}/sendMessage"
            headers = {"Host": "api.telegram.org", "User-Agent": "ItsWatuyusei-Suite/3.0"} if is_ip else {"User-Agent": "ItsWatuyusei-Suite/3.0"}

            try:
                
                verify_ssl = not is_ip 
                resp = await self._client.post(url, json=payload, headers=headers, timeout=12.0, follow_redirects=True, verify=verify_ssl)
                
                if resp.status_code == 200:
                    return True
                logger.warning(f"[BaseNotification] Telegram {base_url} returned {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.debug(f"[BaseNotification] Telegram attempt {base_url} failed: {str(e)}")
                if not is_ip: 
                    continue
                break

        logger.error(f"[BaseNotification] Telegram all attempts failed.")
        return False
