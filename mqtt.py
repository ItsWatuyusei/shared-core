

import asyncio
import os
import json
import logging
import ssl
from typing import Any, Dict, Optional
from gmqtt import Client as MQTTClient

logger = logging.getLogger(__name__)

class BaseMQTTClient:

    def __init__(self, broker: str, port: int, user: Optional[str] = None, password: Optional[str] = None, client_id_prefix: str = "Client"):
        self.broker = broker
        self.port = port
        self.user = user
        self.password = password
        self.client_id = f"{client_id_prefix}_{os.urandom(4).hex()}"
        self._client: Optional[MQTTClient] = None
        self._lock = asyncio.Lock()

    async def get_client(self, on_message_handler: Any) -> Optional[MQTTClient]:

        if self._client and self._client.is_connected:
            return self._client

        async with self._lock:
            if self._client and self._client.is_connected:
                return self._client

            if not self.broker:
                logger.debug("[MQTT] No broker configured.")
                return None

            if self._client:
                try: await self._client.disconnect()
                except: pass

            self._client = MQTTClient(self.client_id)
            self._client.on_message = on_message_handler

            if self.user and self.password:
                self._client.set_auth_credentials(self.user, self.password)

            if self.port == 8883:
                self._client.set_config({'ssl': ssl.create_default_context()})

            try:
                logging.getLogger('gmqtt').setLevel(logging.WARNING)
                await self._client.connect(self.broker, self.port, ssl=(self.port == 8883))
                logger.info(f"MQTT Connected to {self.broker}")
                return self._client
            except Exception as e:
                logger.error(f"MQTT Connection failed: {e}")
                self._client = None
                return None

    async def broadcast(self, topic: str, payload: str) -> None:

        try:

            pass
        except Exception as e:
            logger.error(f"MQTT Broadcast error: {e}")

    async def publish(self, client: MQTTClient, topic: str, payload: str, qos: int = 1) -> None:
        try:
            client.publish(topic, payload, qos=qos)
        except Exception as e:
            logger.error(f"MQTT Publish error: {e}")
