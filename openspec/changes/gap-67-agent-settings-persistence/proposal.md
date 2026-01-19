# GAP-67: Agent Settings Not Persisted

**Status**: Draft
**Priority**: Critical
**Type**: Bug - Data Not Persisted
**Source**: VISION_REALITY_DELTA.md Gap #67

## Problem Statement

Agent settings endpoint accepts PUT requests to save settings and GET requests to retrieve them, but nothing is actually persisted. PUT returns the settings that were sent, and GET always returns hardcoded defaults. This makes agent configuration completely non-functional.

**Impact**:
- Users cannot configure agents
- Agent behavior cannot be customized
- Settings are lost immediately after being "saved"
- Demo blocker - agent system appears configurable but isn't
- Wastes user time configuring agents that ignore settings

**Evidence**:
```python
# app/api/agents.py:225, 256, 291
@router.get("/{agent_name}/settings", response_model=AgentSettings)
async def get_agent_settings(agent_name: str):
    # TODO: Load from database/config file
    # For now, return default configs
    return default_settings[agent_name]

@router.put("/{agent_name}/settings", response_model=AgentSettings)
async def update_agent_settings(agent_name: str, settings: AgentSettings):
    # TODO: Save to database/config file
    # For now, just return the requested settings
    return settings
```

## Requirements

### MUST

- Agent settings MUST be persisted to database
- Settings MUST survive server restarts
- GET MUST return the last saved settings (or defaults if never configured)
- PUT MUST validate settings before saving
- Settings MUST be scoped per agent (each agent has its own config)

### SHOULD

- Settings SHOULD have versioning/history
- Invalid settings SHOULD be rejected with clear error messages
- Settings SHOULD support JSON schema validation
- Setting updates SHOULD be logged for audit trail
- Agents SHOULD reload settings when changed (without restart)

### MAY

- Settings MAY support environment-based overrides (dev/staging/prod)
- Settings MAY support bulk import/export
- Settings MAY have rollback capability

## Proposed Solution

### 1. Create Agent Settings Model

```python
# app/models/agent_settings.py
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, JSON, DateTime, Text
from app.database.base import Base

class AgentSettingsRecord(Base):
    __tablename__ = "agent_settings"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = Column(String(255), unique=True, nullable=False, index=True)

    # Settings stored as JSON for flexibility
    settings: Dict[str, Any] = Column(JSON, nullable=False)

    # Schema version for migrations
    schema_version: str = Column(String(50), default="1.0")

    # Audit fields
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Optional[str] = Column(String(36))  # User ID who made change

    # Change history (optional)
    previous_settings: Optional[Dict] = Column(JSON)
    change_reason: Optional[str] = Column(Text)
```

### 2. Create Settings Repository

```python
# app/repositories/agent_settings_repo.py
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.agent_settings import AgentSettingsRecord

class AgentSettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_settings(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get settings for an agent, returns None if not configured"""
        record = self.db.query(AgentSettingsRecord)\
            .filter(AgentSettingsRecord.agent_name == agent_name)\
            .first()

        return record.settings if record else None

    async def save_settings(
        self,
        agent_name: str,
        settings: Dict[str, Any],
        user_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> AgentSettingsRecord:
        """Save or update agent settings"""
        record = self.db.query(AgentSettingsRecord)\
            .filter(AgentSettingsRecord.agent_name == agent_name)\
            .first()

        if record:
            # Update existing
            record.previous_settings = record.settings  # Save history
            record.settings = settings
            record.updated_at = datetime.utcnow()
            record.updated_by = user_id
            record.change_reason = reason
        else:
            # Create new
            record = AgentSettingsRecord(
                agent_name=agent_name,
                settings=settings,
                updated_by=user_id,
                change_reason=reason or "Initial configuration"
            )
            self.db.add(record)

        self.db.commit()
        self.db.refresh(record)
        return record

    async def delete_settings(self, agent_name: str):
        """Delete agent settings (reset to defaults)"""
        record = self.db.query(AgentSettingsRecord)\
            .filter(AgentSettingsRecord.agent_name == agent_name)\
            .first()

        if record:
            self.db.delete(record)
            self.db.commit()

    async def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get settings for all configured agents"""
        records = self.db.query(AgentSettingsRecord).all()
        return {record.agent_name: record.settings for record in records}
```

### 3. Update API Endpoints

```python
# app/api/agents.py
from app.repositories.agent_settings_repo import AgentSettingsRepository
from app.auth import require_auth, User
from pydantic import ValidationError

# Default settings for each agent type
DEFAULT_SETTINGS = {
    "matchmaker-agent": {
        "enabled": True,
        "matching_threshold": 0.7,
        "max_matches_per_run": 50,
        "require_location_match": False,
        "priority_local": True
    },
    "inventory-agent": {
        "enabled": False,
        "reorder_threshold": 0.2,
        "check_interval_hours": 24
    },
    # ... other defaults
}

@router.get("/{agent_name}/settings", response_model=AgentSettings)
async def get_agent_settings(
    agent_name: str,
    db: Session = Depends(get_db)
):
    """Get agent settings (from DB or defaults)"""

    if agent_name not in DEFAULT_SETTINGS:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")

    repo = AgentSettingsRepository(db)
    settings = await repo.get_settings(agent_name)

    # Return saved settings or defaults
    if settings:
        return AgentSettings(**settings)
    else:
        return AgentSettings(**DEFAULT_SETTINGS[agent_name])

@router.put("/{agent_name}/settings", response_model=AgentSettings)
async def update_agent_settings(
    agent_name: str,
    settings: AgentSettings,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update agent settings with persistence"""

    if agent_name not in DEFAULT_SETTINGS:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")

    # Validate settings schema
    try:
        validated_settings = settings.dict()
        # Additional validation logic here
        validate_agent_settings(agent_name, validated_settings)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Save to database
    repo = AgentSettingsRepository(db)
    record = await repo.save_settings(
        agent_name=agent_name,
        settings=validated_settings,
        user_id=current_user.id,
        reason=f"Updated by {current_user.name}"
    )

    # Notify agent to reload settings (if running)
    await notify_agent_settings_changed(agent_name)

    return AgentSettings(**record.settings)

@router.delete("/{agent_name}/settings", status_code=204)
async def reset_agent_settings(
    agent_name: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Reset agent settings to defaults"""

    repo = AgentSettingsRepository(db)
    await repo.delete_settings(agent_name)

    await notify_agent_settings_changed(agent_name)

def validate_agent_settings(agent_name: str, settings: Dict) -> None:
    """Validate agent-specific settings"""

    # Common validations
    if "enabled" in settings and not isinstance(settings["enabled"], bool):
        raise ValueError("enabled must be boolean")

    # Agent-specific validations
    if agent_name == "matchmaker-agent":
        threshold = settings.get("matching_threshold")
        if threshold and (threshold < 0 or threshold > 1):
            raise ValueError("matching_threshold must be between 0 and 1")

        max_matches = settings.get("max_matches_per_run")
        if max_matches and max_matches < 1:
            raise ValueError("max_matches_per_run must be positive")

    # Add more agent-specific validations

async def notify_agent_settings_changed(agent_name: str):
    """Notify running agent that settings changed"""
    # Could use NATS, Redis pub/sub, or direct agent method call
    # For now, agents will check settings on next run
    pass
```

### 4. Update Base Agent to Load Settings

```python
# app/agents/framework/base_agent.py
class BaseAgent:
    def __init__(self, agent_name: str, db: Session):
        self.agent_name = agent_name
        self.db = db
        self.settings = None
        self.load_settings()

    def load_settings(self):
        """Load settings from database"""
        from app.repositories.agent_settings_repo import AgentSettingsRepository

        repo = AgentSettingsRepository(self.db)
        self.settings = repo.get_settings(self.agent_name)

        if not self.settings:
            # Use defaults
            from app.api.agents import DEFAULT_SETTINGS
            self.settings = DEFAULT_SETTINGS.get(self.agent_name, {})

    def reload_settings(self):
        """Reload settings from database (for hot-reload)"""
        self.load_settings()
        logger.info(f"{self.agent_name} reloaded settings: {self.settings}")

    async def execute(self, context: dict) -> dict:
        """Execute with current settings"""

        # Check if enabled
        if not self.settings.get("enabled", True):
            logger.info(f"{self.agent_name} is disabled, skipping execution")
            return {"status": "disabled"}

        # Use settings in execution
        return await self._execute_internal(context)
```

## Implementation Steps

1. Create `agent_settings` database table
2. Create `AgentSettingsRecord` model
3. Create `AgentSettingsRepository`
4. Update API endpoints to use repository
5. Add settings validation logic
6. Update `BaseAgent` to load settings from DB
7. Add database migration
8. Add comprehensive tests
9. Add settings change audit logging

## Test Scenarios

### WHEN a user saves agent settings
THEN the settings MUST be persisted to the database
AND GET request MUST return the saved settings
AND the updated_at timestamp MUST be updated

### WHEN settings are saved with invalid values
THEN the API MUST return 422 Unprocessable Entity
AND the error message MUST explain what's invalid
AND the previous valid settings MUST remain unchanged

### WHEN an agent is executed
THEN it MUST use the persisted settings (not defaults)
AND if disabled in settings, it MUST skip execution

### WHEN settings are reset to defaults
THEN the database record MUST be deleted
AND GET request MUST return default settings again

### WHEN settings are updated multiple times
THEN the history MUST be preserved (previous_settings)
AND the updated_by field MUST track who made changes

## Database Schema

```sql
CREATE TABLE agent_settings (
    id VARCHAR(36) PRIMARY KEY,
    agent_name VARCHAR(255) UNIQUE NOT NULL,
    settings JSON NOT NULL,
    schema_version VARCHAR(50) DEFAULT '1.0',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    updated_by VARCHAR(36),
    previous_settings JSON,
    change_reason TEXT,
    INDEX idx_agent_name (agent_name),
    INDEX idx_updated_at (updated_at)
);
```

## Files to Create/Modify

- `app/models/agent_settings.py` - New model
- `app/repositories/agent_settings_repo.py` - New repository
- `app/api/agents.py` - Update endpoints to use persistence
- `app/agents/framework/base_agent.py` - Load settings from DB
- `app/database/migrations/` - Add migration
- `tests/test_agent_settings_persistence.py` - Comprehensive tests
- `app/api/agents.py` - Add validation logic

## Migration Path

For existing deployments:

1. Run migration to create table
2. Agents will use defaults until configured
3. No breaking changes - defaults still work
4. Users can gradually configure agents

## Related Gaps

- GAP-66: Agent stats (similar persistence pattern)
- GAP-68: Base agent DB queries (agents need to actually use settings)
- All agent-specific gaps (settings control agent behavior)
