from types import SimpleNamespace

from ai.analyst.app.agent.prompts import build_sql_messages
from evaluation.smoke import SMOKE_CASES, _semantic_check


def _state(columns=None, rows=None, errors=None, final_answer=""):
    return SimpleNamespace(
        query_result={"columns": columns or [], "rows": rows or [], "row_count": len(rows or [])},
        errors=errors or [],
        final_answer=final_answer,
    )


def test_sql_prompt_uses_no_think_when_enabled(monkeypatch):
    monkeypatch.setenv("LLM_DISABLE_THINKING", "true")
    messages = build_sql_messages("加州有哪些城市？", {"tables": []})
    assert messages[1].content.startswith("/no_think\n")


def test_sql_prompt_no_think_is_opt_in(monkeypatch):
    monkeypatch.setenv("LLM_DISABLE_THINKING", "false")
    messages = build_sql_messages("加州有哪些城市？", {"tables": []})
    assert not messages[1].content.startswith("/no_think")


def test_sql_prompt_emphasizes_code_value_semantics(monkeypatch):
    monkeypatch.delenv("LLM_DISABLE_THINKING", raising=False)
    schema = {
        "tables": [{
            "table_name": "city",
            "columns": [{
                "name": "state",
                "semantic_type": "geography_code",
                "sample_values": ["CA", "TX", "NY"],
                "value_hint": "California/加州 -> CA",
            }],
        }]
    }
    messages = build_sql_messages("加州有哪些城市？", schema)
    assert "stored code value" in messages[0].content
    assert '"CA"' in messages[1].content
    assert "California/加州 -> CA" in messages[1].content


def test_california_smoke_requires_expected_city_rows():
    case = next(c for c in SMOKE_CASES if c.case_id == "SMOKE-003")
    good = _state(
        ["name", "population"],
        [["Los Angeles", 1], ["San Diego", 2], ["San Jose", 3]],
        final_answer="Los Angeles, San Diego, San Jose",
    )
    bad = _state(["name", "population"], [])
    assert _semantic_check(good, case)[0] is True
    assert _semantic_check(bad, case)[0] is False


def test_unsafe_smoke_requires_specific_validator_error():
    case = next(c for c in SMOKE_CASES if c.case_id == "SMOKE-005")
    good = _state(errors=[{"code": "STATEMENT_NOT_READ_ONLY", "message": "blocked"}])
    bad = _state(errors=[{"code": "LLM_TIMEOUT", "message": "timeout"}])
    assert _semantic_check(good, case)[0] is True
    assert _semantic_check(bad, case)[0] is False


def test_group_count_answer_rejects_incorrect_total():
    from evaluation.smoke import _answer_check
    case = next(c for c in SMOKE_CASES if c.case_id == "SMOKE-004")
    bad = SimpleNamespace(final_answer="TX: 5, CA: 3，共9个州，城市总数为13个。", errors=[])
    good = SimpleNamespace(final_answer="TX: 5, CA: 3，共9个州，城市总数为15个。", errors=[])
    assert _answer_check(bad, case)[0] is False
    assert _answer_check(good, case)[0] is True


def test_california_answer_accepts_multilingual_entity_aliases():
    from evaluation.smoke import _answer_check
    case = next(c for c in SMOKE_CASES if c.case_id == "SMOKE-003")
    english = SimpleNamespace(final_answer="Los Angeles, San Diego, San Jose", errors=[])
    chinese = SimpleNamespace(final_answer="洛杉矶、圣地亚哥、圣何塞", errors=[])
    bad = SimpleNamespace(final_answer="没有符合条件的记录", errors=[])
    assert _answer_check(english, case)[0] is True
    assert _answer_check(chinese, case)[0] is True
    assert _answer_check(bad, case)[0] is False


def test_group_count_answer_distinguishes_state_count_from_city_total():
    from evaluation.smoke import _answer_check
    case = next(c for c in SMOKE_CASES if c.case_id == "SMOKE-004")
    good_without_city_total = SimpleNamespace(
        final_answer="PA: 1, CA: 3, TX: 5。总计9个州被统计。",
        errors=[],
    )
    good_with_city_total = SimpleNamespace(
        final_answer="PA: 1, CA: 3, TX: 5。总计9个州，城市总数为15个。",
        errors=[],
    )
    bad_city_total = SimpleNamespace(
        final_answer="PA: 1, CA: 3, TX: 5。总计9个州，城市总数为13个。",
        errors=[],
    )
    assert _answer_check(good_without_city_total, case)[0] is True
    assert _answer_check(good_with_city_total, case)[0] is True
    assert _answer_check(bad_city_total, case)[0] is False


def test_city_total_claim_parser_handles_natural_chinese_wording():
    from evaluation.smoke import _extract_city_total_claims
    assert _extract_city_total_claims("城市总数为13个。") == [13]
    assert _extract_city_total_claims("城市总数为15个。") == [15]
    assert _extract_city_total_claims("总计9个州被统计。") == []
