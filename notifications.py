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
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

        try:
            resp = await self._client.post(url, json=payload)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"[BaseNotification] Telegram failed: {e}")
            return False
