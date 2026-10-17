"""Combine independent part actions with locomotion and foot contacts.

A rig declares named slots and the channels that each slot can change.
One action can use one slot at a time. A source clip or direct control values
can supply the action pose. The foot contact solver has final authority over
IK goals, so an action cannot replace the moving body's ground contacts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping, Sequence

if TYPE_CHECKING:
    from .rigdoc import RigDocument


@dataclass(frozen=True)
class Articulation:
    """One authored clip or direct control signal in one articulation slot."""

    slot: str
    clip: str | None = None
    time: float = 0.0
    weight: float = 1.0
    values: Mapping[str, float] = field(default_factory=dict)


class PoseComposer:
    """Sample a base clip and mix independent actions by channel ownership.

    The same instance can be used for each frame. It holds no gait state.
    One action per slot makes the result independent of action list order.
    """

    def __init__(self, document: RigDocument):
        self.doc = document
        self.slots = {
            name: frozenset(channels)
            for name, channels in document.data.get("articulation_slots", {}).items()
        }
        all_channels = [channel for channels in self.slots.values()
                        for channel in channels]
        if len(all_channels) != len(set(all_channels)):
            raise ValueError("articulation slots cannot share channels")
        self.contact_channels = frozenset(
            f"{chain['channel_prefix']}_{suffix}"
            for chain in document.ik_chains
            for suffix in ("x", "y", "pitch", "bend")
            if "channel_prefix" in chain
        )
        if self.contact_channels.intersection(all_channels):
            raise ValueError("an articulation slot cannot own an IK contact goal")

    def sample(
        self,
        base_clip: str,
        base_time: float,
        actions: Sequence[Articulation] = (),
        *,
        contacts: Mapping[str, float] | None = None,
    ) -> dict[str, float]:
        """Get one channel sample without changing the source document."""
        if base_clip not in self.doc.clips:
            raise ValueError(f"unknown base clip: {base_clip}")
        values = self.doc.sample(base_clip, base_time)
        used_slots: set[str] = set()
        for action in actions:
            allowed = self.slots.get(action.slot)
            if allowed is None:
                raise ValueError(f"unknown articulation slot: {action.slot}")
            if action.slot in used_slots:
                raise ValueError(f"two actions use the same slot: {action.slot}")
            used_slots.add(action.slot)
            if not (0.0 <= action.weight <= 1.0):
                raise ValueError("action weight must be between zero and one")
            if action.clip is not None and action.clip not in self.doc.clips:
                raise ValueError(f"unknown action clip: {action.clip}")
            sampled = (self.doc.sample(action.clip, action.time)
                       if action.clip is not None else {})
            sampled.update(action.values)
            extra = set(sampled) - allowed
            if extra:
                raise ValueError(
                    f"action {action.slot} changes channels outside its slot: {sorted(extra)}"
                )
            for channel, goal in sampled.items():
                initial = values.get(channel, 0.0)
                values[channel] = initial + action.weight * (float(goal) - initial)
        if contacts is not None:
            extra = set(contacts) - self.contact_channels
            if extra:
                raise ValueError(f"non-contact channels in foot goals: {sorted(extra)}")
            values.update({key: float(value) for key, value in contacts.items()})
        return values

    def solve(
        self,
        base_clip: str,
        base_time: float,
        actions: Sequence[Articulation] = (),
        *,
        contacts: Mapping[str, float] | None = None,
    ):
        """Solve one combined pose with one base clip sample."""
        sample = self.sample(base_clip, base_time, actions, contacts=contacts)
        return self.doc.solve(base_clip, base_time, sampled_channels=sample)
