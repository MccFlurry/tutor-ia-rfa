"""Unit tests del motor de nudges (puro, sin BD ni LLM)."""
from app.schemas.tutor import StudentSnapshot
from app.services.tutor_service import build_nudges


def _snap(**over):
    base = dict(
        has_level=True, level="beginner", overall_pct=40.0,
        last_quiz_passed=None, last_quiz_topic_title=None, last_quiz_topic_id=None,
        days_inactive=None, near_complete_module_title=None,
        near_complete_module_id=None, streak_days=0,
    )
    base.update(over)
    return StudentSnapshot(**base)


def test_no_level_returns_only_assessment_nudge():
    nudges = build_nudges(_snap(has_level=False, level=None), context="dashboard")
    assert len(nudges) == 1
    assert nudges[0].id == "no_level"
    assert nudges[0].cta_route == "/assessment"


def test_zero_progress_shows_welcome():
    nudges = build_nudges(_snap(overall_pct=0.0), context="dashboard")
    assert any(n.id == "welcome_start" for n in nudges)


def test_inactivity_shows_welcome_back_with_topic_cta():
    nudges = build_nudges(
        _snap(days_inactive=9, last_quiz_topic_title="Variables",
              last_quiz_topic_id=5),
        context="dashboard",
    )
    n = next(n for n in nudges if n.id == "inactive")
    assert n.cta_route == "/topics/5"
    assert "Variables" in n.message


def test_near_complete_module_nudge():
    nudges = build_nudges(
        _snap(near_complete_module_title="Kotlin", near_complete_module_id=2),
        context="dashboard",
    )
    n = next(n for n in nudges if n.id == "near_complete")
    assert n.cta_route == "/modules/2"


def test_streak_milestone_nudge():
    nudges = build_nudges(_snap(streak_days=7), context="dashboard")
    assert any(n.id == "streak_7" for n in nudges)


def test_no_streak_nudge_off_milestone():
    nudges = build_nudges(_snap(streak_days=4), context="dashboard")
    assert not any(n.id.startswith("streak_") for n in nudges)


def test_dashboard_caps_at_three_nudges():
    nudges = build_nudges(
        _snap(overall_pct=0.0, days_inactive=10, last_quiz_topic_id=1,
              last_quiz_topic_title="X", near_complete_module_title="M",
              near_complete_module_id=1, streak_days=7),
        context="dashboard",
    )
    assert len(nudges) == 3


def test_topic_context_quiz_retry_nudge():
    nudges = build_nudges(
        _snap(last_quiz_passed=False, last_quiz_topic_title="Bucles",
              last_quiz_topic_id=8),
        context="topic", topic_id=8,
    )
    assert any(n.id == "quiz_retry" for n in nudges)


# --- Fase 4: contextos de resultado (independientes del snapshot) ---
from app.services.tutor_service import build_nudges as _bn


def test_quiz_result_high_score():
    n = _bn(None, "quiz_result", topic_id=5, score=90)
    assert len(n) == 1 and n[0].id == "quiz_result_high" and n[0].tone == "success"


def test_quiz_result_pass_band():
    n = _bn(None, "quiz_result", topic_id=5, score=70)
    assert n[0].id == "quiz_result_pass"
    assert n[0].cta_route == "/topics/5"


def test_quiz_result_low_score_warns_and_links_topic():
    n = _bn(None, "quiz_result", topic_id=8, score=40)
    assert n[0].id == "quiz_result_low" and n[0].tone == "warning"
    assert n[0].cta_route == "/topics/8"


def test_coding_result_bands():
    assert _bn(None, "coding_result", score=85)[0].id == "coding_result_high"
    assert _bn(None, "coding_result", score=65)[0].id == "coding_result_mid"
    assert _bn(None, "coding_result", score=30)[0].id == "coding_result_low"


def test_assessment_result_levels_link_modules():
    beginner = _bn(None, "assessment_result", score=20)[0]
    assert beginner.id == "assessment_result" and beginner.cta_route == "/modules"
    assert _bn(None, "assessment_result", score=60)[0].cta_route == "/modules"
    assert _bn(None, "assessment_result", score=90)[0].cta_route == "/modules"


def test_result_context_without_score_is_empty():
    assert _bn(None, "quiz_result", score=None) == []
