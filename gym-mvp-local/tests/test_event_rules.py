from edge_service.event_rules import EventRulesEngine, RuleConfig
from shared.schemas import EventType


def test_transitions_to_cleaning_attempt():
    engine = EventRulesEngine(RuleConfig(occupy_start_s=2, occupy_end_s=1, cleaning_window_s=5))

    e1 = engine.process(ts_utc=0.0, zone_id="z1", tracks_in_zone=["t_1"], cleaning_motion=False)
    assert e1 == []
    e2 = engine.process(ts_utc=2.1, zone_id="z1", tracks_in_zone=["t_1"], cleaning_motion=False)
    assert any(e.event_type == EventType.MACHINE_OCCUPIED_START for e in e2)

    e3 = engine.process(ts_utc=2.5, zone_id="z1", tracks_in_zone=[], cleaning_motion=False)
    assert e3 == []
    e4 = engine.process(ts_utc=3.6, zone_id="z1", tracks_in_zone=[], cleaning_motion=False)
    assert [e.event_type for e in e4] == [EventType.MACHINE_OCCUPIED_END, EventType.CLEANING_WINDOW_OPEN]

    e5 = engine.process(ts_utc=4.0, zone_id="z1", tracks_in_zone=[], cleaning_motion=True)
    assert any(e.event_type == EventType.CLEANING_ATTEMPT and e.needs_mm for e in e5)
