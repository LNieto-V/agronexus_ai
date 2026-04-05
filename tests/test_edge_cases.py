import pytest
from app.services.parser_service import is_anomaly

# Test para verificar detección de anomalías con valores atípicos absurdos pero posibles en error de hardware
@pytest.mark.asyncio
async def test_extreme_negative_temperature():
    sensor_data = {"temperature": -50.0, "humidity": 10.0}
    assert is_anomaly(sensor_data)

@pytest.mark.asyncio
async def test_extreme_high_temperature():
    sensor_data = {"temperature": 150.0, "humidity": 10.0}
    assert is_anomaly(sensor_data)

@pytest.mark.asyncio
async def test_extreme_humidity():
    sensor_data = {"temperature": 25.0, "humidity": 110.0} # Imposible pero la API debe manejarlo como anomalía
    assert is_anomaly(sensor_data)

@pytest.mark.asyncio
async def test_normal_conditions():
    sensor_data = {"temperature": 28.0, "humidity": 50.0}
    assert not is_anomaly(sensor_data)
