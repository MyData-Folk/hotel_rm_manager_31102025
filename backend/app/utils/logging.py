import json
from typing import Any, Dict, Optional

from sqlmodel import Session

from ..models.entities import ActivityLog


def log_activity(session: Session, action: str, entity: str, metadata: Optional[Dict[str, Any]] = None) -> ActivityLog:
    activity = ActivityLog(action=action, entity=entity, metadata=json.dumps(metadata or {}))
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity
