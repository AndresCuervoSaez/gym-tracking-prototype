"""Gym-specific event rules based on track-ROI interactions."""
from __future__ import annotations

from dataclasses import dataclass, field

from shared.schemas import EventType


@dataclass
class ZoneState:
    occupied: bool = False
    occupant_track: str | None = None
    first_seen_in_roi_ts: float | None = None
    left_ts: float | None = None
    cleaning_window_until: float | None = None
    cleaning_attempted: bool = False


@dataclass
class RuleConfig:
    occupy_start_s: float = 5.0
    occupy_end_s: float = 3.0
    cleaning_window_s: float = 45.0


@dataclass
class RuleEvent:
    event_type: EventType
    zone_id: str
    track_id: str
    dwell_s: float = 0.0
    needs_mm: bool = False


@dataclass
class EventRulesEngine:
    cfg: RuleConfig
    states: dict[str, ZoneState] = field(default_factory=dict)

    def process(self, ts_utc: float, zone_id: str, tracks_in_zone: list[str], cleaning_motion: bool) -> list[RuleEvent]:
        state = self.states.setdefault(zone_id, ZoneState())
        events: list[RuleEvent] = []

        if tracks_in_zone:
            cur_track = tracks_in_zone[0]
            if state.first_seen_in_roi_ts is None or state.occupant_track != cur_track:
                state.first_seen_in_roi_ts = ts_utc
                state.occupant_track = cur_track

            dwell = ts_utc - state.first_seen_in_roi_ts
            if not state.occupied and dwell >= self.cfg.occupy_start_s:
                state.occupied = True
                state.left_ts = None
                events.append(RuleEvent(EventType.MACHINE_OCCUPIED_START, zone_id, cur_track, dwell_s=dwell))
        else:
            if state.occupied:
                if state.left_ts is None:
                    state.left_ts = ts_utc
                elif ts_utc - state.left_ts >= self.cfg.occupy_end_s:
                    track = state.occupant_track or "t_0000"
                    events.append(RuleEvent(EventType.MACHINE_OCCUPIED_END, zone_id, track))
                    events.append(RuleEvent(EventType.CLEANING_WINDOW_OPEN, zone_id, track))
                    state.occupied = False
                    state.cleaning_window_until = ts_utc + self.cfg.cleaning_window_s
                    state.cleaning_attempted = False
                    state.first_seen_in_roi_ts = None
                    state.occupant_track = None
            elif state.cleaning_window_until and ts_utc <= state.cleaning_window_until and cleaning_motion and not state.cleaning_attempted:
                state.cleaning_attempted = True
                events.append(RuleEvent(EventType.CLEANING_ATTEMPT, zone_id, "t_cleaner", needs_mm=True))

        if state.cleaning_window_until and ts_utc > state.cleaning_window_until:
            state.cleaning_window_until = None
            state.cleaning_attempted = False

        return events
