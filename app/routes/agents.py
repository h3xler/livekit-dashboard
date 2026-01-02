"""Agent Management Routes"""

import os
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from urllib.parse import quote

from app.services.agent_service import (
    AgentService,
    AgentConfig,
    get_agent_service,
)
from app.services.livekit import LiveKitClient, get_livekit_client
from app.security.basic_auth import requires_admin, get_current_user
from app.security.csrf import get_csrf_token, verify_csrf_token


router = APIRouter()


def is_agents_enabled() -> bool:
    """Check if agents feature is enabled"""
    return os.environ.get("ENABLE_AGENTS", "true").lower() == "true"


@router.get("/agents", response_class=HTMLResponse)
@requires_admin
async def agents_index(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
    flash_message: Optional[str] = None,
    flash_type: Optional[str] = None,
):
    """Agents management page"""
    if not is_agents_enabled():
        templates = request.app.state.templates
        return templates.TemplateResponse(
            "base.html.j2",
            {
                "request": request,
                "error": "Agents feature is not enabled. Set ENABLE_AGENTS=true.",
            },
            status_code=403,
        )
    
    agents = agent_service.list_agents()
    model_providers = AgentService.get_model_providers()
    voices = AgentService.get_voices()
    
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "agents/index.html.j2",
        {
            "request": request,
            "agents": agents,
            "model_providers": model_providers,
            "voices": voices,
            "flash_message": flash_message,
            "flash_type": flash_type,
            "csrf_token": get_csrf_token(request),
        },
    )


@router.post("/agents/create", response_class=HTMLResponse)
@requires_admin
async def create_agent(
    request: Request,
    csrf_token: str = Form(...),
    name: str = Form(...),
    model_provider: str = Form("google"),
    model: str = Form("gemini-2.0-flash-exp"),
    voice: str = Form("Puck"),
    first_message: str = Form("Hello! How can I help you today?"),
    noise_cancellation: bool = Form(False),
    n8n_mcp_url: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Create a new agent configuration"""
    verify_csrf_token(request, csrf_token)
    
    try:
        agent = AgentConfig(
            name=name,
            model_provider=model_provider,
            model=model,
            voice=voice,
            first_message=first_message,
            noise_cancellation=noise_cancellation,
            n8n_mcp_url=n8n_mcp_url or "",
            metadata=metadata or "",
        )
        agent_service.create_agent(agent)
        
        message = quote(f"Agent '{name}' created successfully")
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type=success",
            status_code=303,
        )
    except Exception as e:
        message = quote(f"Error creating agent: {str(e)}")
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type=error",
            status_code=303,
        )


@router.post("/agents/{agent_id}/update", response_class=HTMLResponse)
@requires_admin
async def update_agent(
    request: Request,
    agent_id: str,
    csrf_token: str = Form(...),
    name: str = Form(...),
    model_provider: str = Form("google"),
    model: str = Form("gemini-2.0-flash-exp"),
    voice: str = Form("Puck"),
    first_message: str = Form("Hello! How can I help you today?"),
    noise_cancellation: bool = Form(False),
    n8n_mcp_url: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Update an existing agent configuration"""
    verify_csrf_token(request, csrf_token)
    
    try:
        updated = agent_service.update_agent(
            agent_id,
            name=name,
            model_provider=model_provider,
            model=model,
            voice=voice,
            first_message=first_message,
            noise_cancellation=noise_cancellation,
            n8n_mcp_url=n8n_mcp_url or "",
            metadata=metadata or "",
        )
        
        if updated:
            message = quote(f"Agent '{name}' updated successfully")
            flash_type = "success"
        else:
            message = quote(f"Agent not found")
            flash_type = "error"
        
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type={flash_type}",
            status_code=303,
        )
    except Exception as e:
        message = quote(f"Error updating agent: {str(e)}")
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type=error",
            status_code=303,
        )


@router.post("/agents/{agent_id}/delete", response_class=HTMLResponse)
@requires_admin
async def delete_agent(
    request: Request,
    agent_id: str,
    csrf_token: str = Form(...),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Delete an agent configuration"""
    verify_csrf_token(request, csrf_token)
    
    try:
        deleted = agent_service.delete_agent(agent_id)
        
        if deleted:
            message = quote("Agent deleted successfully")
            flash_type = "success"
        else:
            message = quote("Agent not found")
            flash_type = "error"
        
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type={flash_type}",
            status_code=303,
        )
    except Exception as e:
        message = quote(f"Error deleting agent: {str(e)}")
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type=error",
            status_code=303,
        )


@router.post("/agents/{agent_id}/toggle", response_class=HTMLResponse)
@requires_admin
async def toggle_agent(
    request: Request,
    agent_id: str,
    csrf_token: str = Form(...),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Toggle agent enabled/disabled status"""
    verify_csrf_token(request, csrf_token)
    
    try:
        agent = agent_service.toggle_agent(agent_id)
        
        if agent:
            status = "enabled" if agent.enabled else "disabled"
            message = quote(f"Agent '{agent.name}' {status}")
            flash_type = "success"
        else:
            message = quote("Agent not found")
            flash_type = "error"
        
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type={flash_type}",
            status_code=303,
        )
    except Exception as e:
        message = quote(f"Error toggling agent: {str(e)}")
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type=error",
            status_code=303,
        )


@router.post("/agents/{agent_id}/test", response_class=HTMLResponse)
@requires_admin
async def test_agent(
    request: Request,
    agent_id: str,
    csrf_token: str = Form(...),
    agent_service: AgentService = Depends(get_agent_service),
    lk: LiveKitClient = Depends(get_livekit_client),
):
    """Test an agent by creating a test room and dispatching the agent"""
    verify_csrf_token(request, csrf_token)
    
    agent = agent_service.get_agent(agent_id)
    if not agent:
        message = quote("Agent not found")
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type=error",
            status_code=303,
        )
    
    if not agent.enabled:
        message = quote("Agent is disabled. Enable it first to test.")
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type=error",
            status_code=303,
        )
    
    try:
        import uuid
        test_room_name = f"agent-test-{uuid.uuid4().hex[:8]}"
        
        # Create test room
        room = await lk.create_room(
            name=test_room_name,
            empty_timeout=300,  # 5 minutes
            max_participants=2,
            metadata=f'{{"test_agent": "{agent.name}"}}',
        )
        
        # Generate token for user to join the test room
        token = lk.generate_token(
            room=test_room_name,
            identity="test-user",
            name="Test User",
            ttl=300,
        )
        
        # Prepare agent metadata for dispatch
        agent_metadata = {
            "model_provider": agent.model_provider,
            "model": agent.model,
            "voice": agent.voice,
            "first_message": agent.first_message,
            "noise_cancellation": agent.noise_cancellation,
            "n8n_mcp_url": agent.n8n_mcp_url,
        }
        
        # Note: Agent dispatch happens automatically via dispatch rules
        # or the agent server picks up new rooms based on configuration
        
        message = quote(f"Test room '{test_room_name}' created. Token generated for testing.")
        templates = request.app.state.templates
        return templates.TemplateResponse(
            "agents/test.html.j2",
            {
                "request": request,
                "agent": agent,
                "room_name": test_room_name,
                "token": token,
                "livekit_url": os.environ.get("LIVEKIT_URL", ""),
                "csrf_token": get_csrf_token(request),
            },
        )
    except Exception as e:
        message = quote(f"Error creating test room: {str(e)}")
        return RedirectResponse(
            url=f"/agents?flash_message={message}&flash_type=error",
            status_code=303,
        )
