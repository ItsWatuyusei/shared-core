from typing import Protocol, Dict, Any, Optional

class INotificationService(Protocol):
    """
    Interface for sending notifications (Discord, Telegram, etc.).
    Ensures both systems follow the same contract.
    """
    async def send_notification(
        self, 
        event_type: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        ...

class IMQTTService(Protocol):
    """
    Interface for MQTT communication.
    Standardizes how we broadcast and broadcast notifications via MQTT.
    """
    def broadcast_notification(self, event_type: str, data: Dict[str, Any]) -> None:
        ...
        
    async def _async_broadcast(self, topic: str, payload: str) -> None:
        ...
