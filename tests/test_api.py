import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.init_db import init_database


@pytest.fixture(autouse=True)
async def setup_db():
    await init_database()
    yield


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data


@pytest.mark.asyncio
async def test_get_users():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users")
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 2
        assert any("tetiana" in u["email"].lower() for u in users)


@pytest.mark.asyncio
async def test_boards_crud_and_optimistic_locking():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Board
        create_payload = {
            "title": "Minimalist Bauhaus Concept",
            "description": "Primary colors and geometrical forms.",
            "background_color": "#FAF8F5",
            "grid_type": "freeform",
            "owner_id": 1
        }
        res_create = await ac.post("/api/v1/boards", json=create_payload)
        assert res_create.status_code == 201
        board = res_create.json()
        board_id = board["id"]
        assert board["version"] == 1
        assert board["title"] == "Minimalist Bauhaus Concept"

        # 2. Add Element
        el_payload = {
            "element_type": "note",
            "x": 100.0,
            "y": 120.0,
            "width": 260.0,
            "height": 180.0,
            "z_index": 1,
            "content": {"title": "Form follows function", "text": "Less is more."}
        }
        res_el = await ac.post(f"/api/v1/boards/{board_id}/elements", json=el_payload)
        assert res_el.status_code == 201
        element = res_el.json()
        el_id = element["id"]

        # Board version should increment to 2
        res_board = await ac.get(f"/api/v1/boards/{board_id}")
        assert res_board.status_code == 200
        assert res_board.json()["version"] == 2

        # 3. Batch Update Drag & Drop Coordinates
        batch_payload = {
            "expected_board_version": 2,
            "elements": [
                {
                    "id": el_id,
                    "element_type": "note",
                    "x": 250.0,
                    "y": 300.0,
                    "width": 260.0,
                    "height": 180.0,
                    "z_index": 2,
                    "content": {"title": "Form follows function", "text": "Updated via drag-and-drop batch!"}
                }
            ]
        }
        res_batch = await ac.post(f"/api/v1/boards/{board_id}/elements/batch", json=batch_payload)
        assert res_batch.status_code == 200
        batch_data = res_batch.json()
        assert batch_data["updated_count"] == 1
        assert batch_data["new_board_version"] == 3

        # 4. Test Optimistic Concurrency Conflict (HTTP 409)
        # Client tries to save using stale version (expected_version: 2, but board is now at 3)
        stale_batch_payload = {
            "expected_board_version": 2,
            "elements": [
                {
                    "id": el_id,
                    "element_type": "note",
                    "x": 500.0,
                    "y": 500.0,
                }
            ]
        }
        res_conflict = await ac.post(f"/api/v1/boards/{board_id}/elements/batch", json=stale_batch_payload)
        assert res_conflict.status_code == 409
        conflict_detail = res_conflict.json()["detail"]
        assert "Optimistic Concurrency Conflict" in conflict_detail

        # 5. Export Board (High-Load Scenario Endpoint)
        res_export = await ac.get(f"/api/v1/boards/{board_id}/export")
        assert res_export.status_code == 200
        export_data = res_export.json()
        assert "board" in export_data
        assert "elements" in export_data
        assert "summary" in export_data
        assert export_data["summary"]["total_elements"] >= 1


@pytest.mark.asyncio
async def test_collaborators_management():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create board
        res_b = await ac.post("/api/v1/boards", json={
            "title": "Collab Space",
            "owner_id": 1
        })
        board_id = res_b.json()["id"]

        # Add User 2 as EDITOR
        res_collab = await ac.post(f"/api/v1/boards/{board_id}/collaborators", json={
            "user_id": 2,
            "role": "EDITOR"
        })
        assert res_collab.status_code == 201
        assert res_collab.json()["role"] == "EDITOR"

        # List collabs
        res_list = await ac.get(f"/api/v1/boards/{board_id}/collaborators")
        assert res_list.status_code == 200
        collabs = res_list.json()
        assert len(collabs) >= 2  # OWNER (1) + EDITOR (2)

        # Remove collaborator
        res_del = await ac.delete(f"/api/v1/boards/{board_id}/collaborators/2")
        assert res_del.status_code == 204
