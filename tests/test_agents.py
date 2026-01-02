"""Tests for agent routes"""
import pytest
from fastapi import status


def test_agents_requires_auth(client):
    """Test that agents page requires authentication"""
    response = client.get("/agents")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_agents_page_with_auth(client, auth_headers):
    """Test agents page with authentication"""
    response = client.get("/agents", headers=auth_headers)
    # Should return 200 (page loads) or 403 (agents disabled)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]


def test_agents_create_requires_auth(client):
    """Test that agent creation requires authentication"""
    response = client.post("/agents/create", data={
        "csrf_token": "test",
        "name": "Test Agent",
        "model_provider": "google",
        "model": "gemini-2.0-flash-exp",
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_agents_toggle_requires_auth(client):
    """Test that agent toggle requires authentication"""
    response = client.post("/agents/test-id/toggle", data={"csrf_token": "test"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_agents_delete_requires_auth(client):
    """Test that agent deletion requires authentication"""
    response = client.post("/agents/test-id/delete", data={"csrf_token": "test"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
