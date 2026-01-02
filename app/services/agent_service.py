"""Agent Service - Manages agent configurations stored in JSON file"""

import json
import os
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path


class AgentConfig:
    """Agent configuration model"""
    
    def __init__(
        self,
        id: str = None,
        name: str = "",
        enabled: bool = True,
        model_provider: str = "google",
        model: str = "gemini-2.0-flash-exp",
        voice: str = "Puck",
        first_message: str = "Hello! How can I help you today?",
        noise_cancellation: bool = True,
        n8n_mcp_url: str = "",
        metadata: str = "",
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.enabled = enabled
        self.model_provider = model_provider
        self.model = model
        self.voice = voice
        self.first_message = first_message
        self.noise_cancellation = noise_cancellation
        self.n8n_mcp_url = n8n_mcp_url
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "model_provider": self.model_provider,
            "model": self.model,
            "voice": self.voice,
            "first_message": self.first_message,
            "noise_cancellation": self.noise_cancellation,
            "n8n_mcp_url": self.n8n_mcp_url,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        return cls(**data)


class AgentService:
    """Service for managing agent configurations"""
    
    # Common model providers and their models
    MODEL_PROVIDERS = {
        "google": {
            "name": "Google Gemini",
            "models": [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
            ]
        },
        "openai": {
            "name": "OpenAI",
            "models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
            ]
        },
        "anthropic": {
            "name": "Anthropic",
            "models": [
                "claude-3-5-sonnet-latest",
                "claude-3-5-haiku-latest",
                "claude-3-opus-latest",
            ]
        },
        "groq": {
            "name": "Groq",
            "models": [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
            ]
        },
        "deepseek": {
            "name": "DeepSeek",
            "models": [
                "deepseek-chat",
                "deepseek-reasoner",
            ]
        },
    }
    
    # Common voice options
    VOICES = {
        "google": ["Puck", "Charon", "Kore", "Fenrir", "Aoede"],
        "openai": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        "elevenlabs": ["Rachel", "Drew", "Clyde", "Paul", "Antoni"],
        "cartesia": ["sonic-english", "sonic-multilingual"],
    }
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Default to data directory in app root
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        self.agents_file = self.data_dir / "agents.json"
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory and agents file exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.agents_file.exists():
            self._save_agents([])
    
    def _load_agents(self) -> List[Dict[str, Any]]:
        """Load agents from JSON file"""
        try:
            with open(self.agents_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("agents", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_agents(self, agents: List[Dict[str, Any]]):
        """Save agents to JSON file"""
        with open(self.agents_file, "w", encoding="utf-8") as f:
            json.dump({"agents": agents}, f, indent=2, ensure_ascii=False)
    
    def list_agents(self) -> List[AgentConfig]:
        """List all agent configurations"""
        agents_data = self._load_agents()
        return [AgentConfig.from_dict(a) for a in agents_data]
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get a specific agent by ID"""
        agents = self._load_agents()
        for agent_data in agents:
            if agent_data.get("id") == agent_id:
                return AgentConfig.from_dict(agent_data)
        return None
    
    def create_agent(self, config: AgentConfig) -> AgentConfig:
        """Create a new agent configuration"""
        agents = self._load_agents()
        agents.append(config.to_dict())
        self._save_agents(agents)
        return config
    
    def update_agent(self, agent_id: str, **kwargs) -> Optional[AgentConfig]:
        """Update an existing agent configuration"""
        agents = self._load_agents()
        for i, agent_data in enumerate(agents):
            if agent_data.get("id") == agent_id:
                # Update only provided fields
                for key, value in kwargs.items():
                    if value is not None:
                        agent_data[key] = value
                agents[i] = agent_data
                self._save_agents(agents)
                return AgentConfig.from_dict(agent_data)
        return None
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent configuration"""
        agents = self._load_agents()
        original_len = len(agents)
        agents = [a for a in agents if a.get("id") != agent_id]
        if len(agents) < original_len:
            self._save_agents(agents)
            return True
        return False
    
    def toggle_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Toggle agent enabled status"""
        agents = self._load_agents()
        for i, agent_data in enumerate(agents):
            if agent_data.get("id") == agent_id:
                agent_data["enabled"] = not agent_data.get("enabled", True)
                agents[i] = agent_data
                self._save_agents(agents)
                return AgentConfig.from_dict(agent_data)
        return None
    
    def get_enabled_agents(self) -> List[AgentConfig]:
        """Get only enabled agents"""
        return [a for a in self.list_agents() if a.enabled]
    
    @classmethod
    def get_model_providers(cls) -> Dict[str, Any]:
        """Get available model providers and their models"""
        return cls.MODEL_PROVIDERS
    
    @classmethod
    def get_voices(cls) -> Dict[str, List[str]]:
        """Get available voices by provider"""
        return cls.VOICES


# Dependency injection for FastAPI
_agent_service: Optional[AgentService] = None

def get_agent_service() -> AgentService:
    """Get or create the agent service singleton"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
