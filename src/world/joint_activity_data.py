"""Data structures for joint activities.

Defines JointActivityOutcome and JointActivityRecord for multi-person interactive activities.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from src.world.clock import TimeState


@dataclass
class JointActivityOutcome:
    """Single participant's outcome in a joint activity.

    Owner: GodModel generates
    Modifier: Immutable after creation

    Represents the state changes for one participant in a joint activity.
    """

    agent_name: str
    delta_vitality: int = 0
    delta_fulfillment: Dict[str, int] = field(
        default_factory=dict
    )  # mood/social/esteem
    delta_skills: Dict[str, int] = field(default_factory=dict)
    # Items: List of dicts with {name, description, from/to}
    items_sent: List[Dict[str, Any]] = field(
        default_factory=list
    )  # Items gifted to others
    items_received: List[Dict[str, Any]] = field(
        default_factory=list
    )  # Items received from others

    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "delta_vitality": self.delta_vitality,
            "delta_fulfillment": dict(self.delta_fulfillment),
            "delta_skills": dict(self.delta_skills),
            "items_sent": list(self.items_sent),
            "items_received": list(self.items_received),
        }

    @staticmethod
    def from_dict(d: Dict) -> JointActivityOutcome:
        return JointActivityOutcome(
            agent_name=d["agent_name"],
            delta_vitality=d.get("delta_vitality", 0),
            delta_fulfillment=d.get("delta_fulfillment", {}),
            delta_skills=d.get("delta_skills", {}),
            items_sent=d.get("items_sent", []),
            items_received=d.get("items_received", []),
        )


@dataclass
class JointActivityRecord:
    """Complete joint activity record (for persistence).

    Owner: Belongs to agent's DataManager
    Modifier: Created by JointActivity.run(), written to JSONL

    Records one agent's participation in a joint activity, including their
    summary, reflection, and state changes (deltas, not full state).
    """

    agent_name: str
    time: TimeState
    activity_id: str
    activity_name: str

    # Agent's perspective on the activity
    summary: str = ""  # Summary of what happened in the activity
    reflection: str = ""  # Personal reflection on the activity

    # Activity metadata
    participants: List[str] = field(default_factory=list)  # All participants
    location: str = ""

    # State changes (outcome object, simplified from separate delta fields)
    outcome: JointActivityOutcome = None

    def to_dict(self) -> Dict:
        return {
            "type": "joint",
            "agent_name": self.agent_name,
            "time": str(self.time),
            "activity_id": self.activity_id,
            "activity_name": self.activity_name,
            "summary": self.summary,
            "reflection": self.reflection,
            "participants": list(self.participants),
            "location": self.location,
            "outcome": self.outcome.to_dict() if self.outcome else None,
        }

    @staticmethod
    def from_dict(d: Dict) -> JointActivityRecord:
        outcome = JointActivityOutcome.from_dict(d["outcome"])
        return JointActivityRecord(
            agent_name=d["agent_name"],
            time=TimeState.from_string(d["time"]),
            activity_id=d["activity_id"],
            activity_name=d["activity_name"],
            summary=d["summary"],
            reflection=d["reflection"],
            participants=d["participants"],
            location=d["location"],
            outcome=outcome,
        )
