"""Data structures for public activities.

Defines PublicActivityRecord for persistence.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.world.clock import TimeState


@dataclass
class PublicActivityOutcome:
    """Outcome from GodModel for public activity.

    Similar to ActionOutcome but without consumption/money/items.
    """

    outcome: str  # Natural language message describing outcome
    delta_vitality: int = 0
    delta_fulfillment: Dict[str, int] = field(
        default_factory=dict
    )  # mood/material/social/esteem
    delta_skills: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome,
            "delta_vitality": self.delta_vitality,
            "delta_fulfillment": dict(self.delta_fulfillment),
            "delta_skills": dict(self.delta_skills),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PublicActivityOutcome":
        return PublicActivityOutcome(
            outcome=d["outcome"],
            delta_vitality=d.get("delta_vitality", 0),
            delta_fulfillment=d.get("delta_fulfillment", {}),
            delta_skills=d.get("delta_skills", {}),
        )


@dataclass
class PublicActivityRecord:
    """Complete public activity record (for persistence).

    Owner: Belongs to agent_name's DataManager
    Modifier: Created by PublicActivity.run(), written to JSONL
    """

    agent_name: str
    time: TimeState
    activity_id: str
    activity_name: str
    event_description: str
    participants: List[str]  # All participants in this public activity
    participation: str  # This agent's participation description
    reflection: str  # This agent's reflection after activity
    outcome: Optional[PublicActivityOutcome] = None  # GodModel evaluation result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "public",
            "agent_name": self.agent_name,
            "time": str(self.time),
            "activity_id": self.activity_id,
            "activity_name": self.activity_name,
            "event_description": self.event_description,
            "participants": self.participants,
            "participation": self.participation,
            "reflection": self.reflection,
            "outcome": self.outcome.to_dict() if self.outcome else None,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PublicActivityRecord":
        outcome_data = d.get("outcome")
        outcome = (
            PublicActivityOutcome.from_dict(outcome_data) if outcome_data else None
        )
        return PublicActivityRecord(
            agent_name=d["agent_name"],
            time=TimeState.from_string(d["time"]),
            activity_id=d["activity_id"],
            activity_name=d["activity_name"],
            event_description=d["event_description"],
            participants=d["participants"],
            participation=d["participation"],
            reflection=d["reflection"],
            outcome=outcome,
        )
