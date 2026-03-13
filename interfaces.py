

from typing import Protocol, Dict, Any, Optional

class INotificationService(Protocol):

    async def send_notification(
        self,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        ...

class IMQTTService(Protocol):

    def broadcast_notification(self, event_type: str, data: Dict[str, Any]) -> None:
        ...

    async def _async_broadcast(self, topic: str, payload: str) -> None:
        ...
