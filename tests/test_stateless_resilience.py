import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.services.init_db import init_database


@pytest.fixture(autouse=True)
async def setup_db():
    await init_database()
    yield


@pytest.mark.asyncio
async def test_instance_identification_header():
    """Verify that every response carries the X-Instance-ID header for node tracking."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        assert "x-instance-id" in res.headers
        assert res.headers["x-instance-id"] == settings.INSTANCE_ID
        assert res.json()["instance_id"] == settings.INSTANCE_ID


@pytest.mark.asyncio
async def test_cross_instance_consistency():
    """
    Lab 2 Requirement 2.5: Cross-Instance Consistency Testing
    Simulate requests hopping across independent instances without sticky sessions:
    1. POST (Create) -> Instance 1
    2. GET (Read)   -> Instance 2
    3. POST (Batch Update) -> Instance 2
    4. GET (Read fresh state) -> Instance 1
    """
    # Create two simulated instances with distinct Node IDs sharing the same persistence layer
    settings_1_id = "backend-instance-1"
    settings_2_id = "backend-instance-2"

    async def client_request(instance_id: str, method: str, url: str, **kwargs):
        # Dynamically set node identity for the request
        settings.INSTANCE_ID = instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            if method == "POST":
                return await client.post(url, **kwargs)
            elif method == "GET":
                return await client.get(url, **kwargs)
            elif method == "PATCH":
                return await client.patch(url, **kwargs)
            elif method == "DELETE":
                return await client.delete(url, **kwargs)

    # Step 1: POST to Instance 1 -> Creates board
    create_payload = {
        "title": "Stateless Architecture Moodboard",
        "description": "Cross-instance verification board",
        "background_color": "#FAF8F5",
        "grid_type": "freeform",
        "owner_id": 1,
    }
    res1 = await client_request(settings_1_id, "POST", "/api/v1/boards", json=create_payload)
    assert res1.status_code == 201
    assert res1.headers["x-instance-id"] == "backend-instance-1"
    board_data = res1.json()
    board_id = board_data["id"]
    assert board_data["version"] == 1

    # Step 2: GET from Instance 2 -> Reads newly created board
    res2 = await client_request(settings_2_id, "GET", f"/api/v1/boards/{board_id}")
    assert res2.status_code == 200
    assert res2.headers["x-instance-id"] == "backend-instance-2"
    assert res2.json()["title"] == "Stateless Architecture Moodboard"
    assert res2.json()["version"] == 1

    # Step 3: POST batch update to Instance 2 -> Mutates state (Optimistic locking version increments)
    batch_payload = {
        "expected_board_version": 1,
        "elements": [
            {
                "element_type": "note",
                "x": 120.0,
                "y": 140.0,
                "width": 260.0,
                "height": 180.0,
                "z_index": 1,
                "content": {"title": "Zero In-Memory State", "text": "Every worker is interchangeable."},
            }
        ],
    }
    res3 = await client_request(
        settings_2_id, "POST", f"/api/v1/boards/{board_id}/elements/batch", json=batch_payload
    )
    assert res3.status_code == 200
    assert res3.headers["x-instance-id"] == "backend-instance-2"
    batch_res = res3.json()
    assert batch_res["updated_count"] == 1
    assert batch_res["new_board_version"] == 2

    # Step 4: GET from Instance 1 -> Confirms latest version and elements on the OTHER instance
    res4 = await client_request(settings_1_id, "GET", f"/api/v1/boards/{board_id}")
    assert res4.status_code == 200
    assert res4.headers["x-instance-id"] == "backend-instance-1"
    fresh_board = res4.json()
    assert fresh_board["version"] == 2
    assert len(fresh_board["elements"]) == 1
    assert fresh_board["elements"][0]["content"]["title"] == "Zero In-Memory State"


@pytest.mark.asyncio
async def test_instance_loss_and_recovery():
    """
    Lab 2 Requirement 2.5: Instance Loss Scenario
    Simulate sudden death of Instance 1 and verify Instance 2 continues without data loss.
    """
    # 1. Instance 1 creates a board
    settings.INSTANCE_ID = "backend-instance-1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_1:
        res_create = await client_1.post(
            "/api/v1/boards",
            json={"title": "Surviving Node Board", "owner_id": 1},
        )
        assert res_create.status_code == 201
        board_id = res_create.json()["id"]

    # 2. Simulate Instance 1 crashing / dying (client_1 session is discarded)
    # 3. Instance 2 immediately takes over
    settings.INSTANCE_ID = "backend-instance-2"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_2:
        res_read = await client_2.get(f"/api/v1/boards/{board_id}")
        assert res_read.status_code == 200
        assert res_read.headers["x-instance-id"] == "backend-instance-2"
        assert res_read.json()["title"] == "Surviving Node Board"

        # Instance 2 successfully exports the snapshot created by the dead node
        res_export = await client_2.get(f"/api/v1/boards/{board_id}/export")
        assert res_export.status_code == 200
        assert res_export.headers["x-instance-id"] == "backend-instance-2"
        assert res_export.json()["board"]["id"] == board_id
