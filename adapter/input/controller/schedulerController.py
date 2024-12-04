async def generate_data():
    """데이터를 생성하고 WebSocket으로 전송합니다."""
    try:
        # 각 센서에 대해 데이터 생성
        sensor_ids = ["sensor-1", "sensor-2", "sensor-3"]  # 예시 센서 ID들
        for sensor_id in sensor_ids:
            sensor_data = container.data_generator.generate_sensor_data(sensor_id)
            container.sensor_service.process_sensor_data(
                sensor_id=sensor_data.sensor_id,
                value=sensor_data.value,
                timestamp=sensor_data.timestamp
            )

        # 모든 활성 WebSocket 연결에 데이터 전송
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps({"status": "success"}))
            except:
                active_connections.remove(connection)
    except Exception as e:
        print(f"Error generating data: {e}")
