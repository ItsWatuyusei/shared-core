import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from shared_core.notifications import BaseNotificationService
from shared_core.mqtt import BaseMQTTClient

@pytest.mark.asyncio
async def test_base_notification_service_discord():
    
    mock_client = AsyncMock()
    mock_resp = AsyncMock()
    mock_resp.status_code = 204
    mock_client.post.return_value = mock_resp
    
    service = BaseNotificationService(http_client=mock_client)
    success = await service._send_to_discord(
        webhook_url="http://mock-discord.com",
        event_type="test",
        message="Integration test message",
        details={"status": "working"}
    )
    
    assert success is True
    assert mock_client.post.called
    args, kwargs = mock_client.post.call_args
    assert "embeds" in kwargs["json"]
    assert kwargs["json"]["embeds"][0]["title"] == "🔔 TEST"

@pytest.mark.asyncio
async def test_base_notification_service_telegram():
    
    mock_client = AsyncMock()
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_client.post.return_value = mock_resp
    
    service = BaseNotificationService(http_client=mock_client)
    success = await service._send_to_telegram(
        token="bot123",
        chat_id="chat456",
        event_type="success",
        message="Bot is online"
    )
    
    assert success is True
    assert mock_client.post.called
    args, kwargs = mock_client.post.call_args
    assert "bot123" in args[0]
    assert kwargs["json"]["chat_id"] == "chat456"

@pytest.mark.asyncio
async def test_base_mqtt_client_initialization():
    
    client = BaseMQTTClient(
        broker="localhost", 
        port=1883, 
        user="user", 
        password="pass", 
        client_id_prefix="Test"
    )
    assert client.broker == "localhost"
    assert client.port == 1883
    assert client.user == "user"
    assert "Test_" in client.client_id

@pytest.mark.asyncio
async def test_base_mqtt_client_connection_flow():
    
    with patch("shared_core.mqtt.MQTTClient") as MockMQTT:
        mock_instance = MockMQTT.return_value
        mock_instance.is_connected = False
        mock_instance.connect = AsyncMock()
        
        client = BaseMQTTClient("localhost", 1883)

        mqtt_c = await client.get_client(on_message_handler=lambda x: x)
        assert MockMQTT.called
        assert mqtt_c == mock_instance

@pytest.mark.asyncio
async def test_base_database_factory_health_check():
    
    from shared_core.database_factory import BaseConnectionFactory
    from shared_core.config import BaseInfraSettings
    
    settings = BaseInfraSettings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        CSRF_SECRET="test",
        MASTER_ENCRYPTION_KEY="test",
        INFRA_ADMIN_KEY="test",
        INFRA_CORE_KEY="test"
    )
    
    factory = BaseConnectionFactory(settings)

    is_healthy = await factory.check_health()
    assert is_healthy is True

    with patch.object(factory, "get_engine", side_effect=Exception("Connection lost")):
        is_healthy = await factory.check_health()
        assert is_healthy is False

@pytest.mark.asyncio
async def test_database_factory_singleton_engines():
    
    from shared_core.database_factory import BaseConnectionFactory
    from shared_core.config import BaseInfraSettings
    
    settings = BaseInfraSettings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        CSRF_SECRET="test",
        MASTER_ENCRYPTION_KEY="test",
        INFRA_ADMIN_KEY="test",
        INFRA_CORE_KEY="test"
    )
    factory = BaseConnectionFactory(settings)
    
    engine1 = await factory.get_engine()
    engine2 = await factory.get_engine()
    
    assert engine1 is engine2
    await factory.close_all()
