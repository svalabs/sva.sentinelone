# Copyright: (c) 2026, Marco Wester <marco.wester@sva.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import copy
from urllib.parse import parse_qs, urlparse

import pytest

from ansible.module_utils import basic
from ansible_collections.sva.sentinelone.plugins.modules import custom_rules


SITE_ID = "test-site-id"
RULE_ID = "test-rule-id"
QUERY = 'event.type = "Process Creation"'
CORRELATION = {
    "entity": "endpoint",
    "matchInOrder": False,
    "subQueries": [{"subQuery": QUERY, "matchesRequired": 3}],
}


class ModuleResult(Exception):
    def __init__(self, result):
        self.result = result


class ModuleFailure(ModuleResult):
    pass


class RuleAPI:
    def __init__(self):
        self.rules = []
        self.calls = []
        self.write_response = None
        self.pages = None
        self.create_status = None
        self.update_status = None
        self.action_status = None
        self.action_affected = 1

    def call(self, module, api_endpoint, http_method="get", **kwargs):
        self.calls.append((http_method.upper(), api_endpoint, copy.deepcopy(kwargs.get("body"))))
        path = urlparse(api_endpoint).path
        query = parse_qs(urlparse(api_endpoint).query)
        if path.endswith("/accounts"):
            return {"pagination": {"totalItems": 1}, "data": [{"id": "account-id"}]}
        if path.endswith("/sites"):
            return {"pagination": {"totalItems": 1}, "data": {"sites": [{"id": SITE_ID}]}}
        if http_method.lower() == "get":
            assert query["siteIds"] == [SITE_ID]
            assert query["scopeLevel"] == ["site"]
            if self.pages is not None:
                page = int(query.get("cursor", ["0"])[0])
                next_cursor = str(page + 1) if page + 1 < len(self.pages) else None
                return {"data": copy.deepcopy(self.pages[page]), "pagination": {"nextCursor": next_cursor}}
            return {"data": copy.deepcopy(self.rules), "pagination": {"nextCursor": None}}
        if self.write_response is not None:
            return copy.deepcopy(self.write_response)
        if http_method == "DELETE":
            assert kwargs["body"] == {"filter": {"siteIds": [SITE_ID], "ids": [RULE_ID]}}
            self.rules = []
            return {"data": {"affected": 1}}
        if path.endswith(("/enable", "/disable")):
            assert http_method == "PUT"
            assert kwargs["body"] == {"filter": {"siteIds": [SITE_ID], "ids": [RULE_ID]}}
            if self.action_affected == 1:
                self.rules[0]["status"] = self.action_status or ("Activating" if path.endswith("/enable") else "Disabled")
            return {"data": {"affected": self.action_affected}}
        if http_method == "PUT":
            assert path.endswith("/" + RULE_ID)
        assert kwargs["body"]["filter"] == {"siteIds": [SITE_ID]}
        rule = copy.deepcopy(kwargs["body"]["data"])
        if http_method == "PUT" and "coolOffSettings" not in rule:
            rule["coolOffSettings"] = copy.deepcopy(self.rules[0].get("coolOffSettings"))
        if rule.get("coolOffSettings") == {"renotifyMinutes": 0}:
            rule["coolOffSettings"] = None
        rule.update(id=RULE_ID, scope="site", scopeId=[SITE_ID])
        override_status = self.create_status if http_method == "POST" else self.update_status
        if override_status is not None:
            rule["status"] = override_status
        self.rules = [rule]
        return {"data": copy.deepcopy(rule)}

    @property
    def writes(self):
        return [call for call in self.calls if call[0] != "GET"]


@pytest.fixture
def api(monkeypatch):
    api = RuleAPI()
    monkeypatch.setattr(custom_rules.SentineloneCustomRules, "api_call", lambda self, *args, **kwargs: api.call(*args, **kwargs))
    return api


@pytest.fixture
def run_module(monkeypatch):
    def exit_json(self, **kwargs):
        raise ModuleResult(kwargs)

    def fail_json(self, **kwargs):
        raise ModuleFailure(kwargs)

    monkeypatch.setattr(basic.AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(basic.AnsibleModule, "fail_json", fail_json)

    def run(**kwargs):
        params = dict(console_url="https://example.sentinelone.net", token="secret-token", site_name="Production", name="Test rule")
        params.update(kwargs)
        monkeypatch.setattr(basic, "_load_params", lambda: copy.deepcopy(params))
        try:
            custom_rules.run_module()
        except ModuleFailure:
            raise
        except ModuleResult as result:
            return result.result
        pytest.fail("Module did not exit")

    return run


def test_create_event_defaults_and_second_run_is_unchanged(api, run_module):
    assert run_module(event_query=QUERY)["changed"]
    method, endpoint, body = api.writes[0]
    assert method == "POST"
    assert endpoint.endswith("/web/api/v2.1/cloud-detection/rules")
    assert body == {
        "filter": {"siteIds": [SITE_ID]},
        "data": {
            "name": "Test rule", "description": "", "severity": "Medium", "expirationMode": "Permanent",
            "status": "Active", "queryLang": "2.0", "networkQuarantine": False,
            "treatAsThreat": "UNDEFINED", "queryType": "events", "s1ql": QUERY,
        },
    }
    assert not run_module(event_query=QUERY)["changed"]
    assert len(api.writes) == 1


def test_correlation_is_forwarded_unchanged_and_api_default_is_idempotent(api, run_module):
    original = copy.deepcopy(CORRELATION)
    assert run_module(correlation_query=CORRELATION)["changed"]
    assert api.writes[0][2]["data"]["correlationParams"] == original
    assert "s1ql" not in api.writes[0][2]["data"]
    api.rules[0]["correlationParams"]["timeWindow"] = {"windowMinutes": 480}
    assert not run_module(correlation_query=CORRELATION)["changed"]
    assert CORRELATION == original


def test_update_options_and_clear_description_and_cool_off(api, run_module):
    run_module(
        event_query=QUERY, description="Description", cool_off_minutes=60, severity="High", status="Disabled",
        network_quarantine=True, treat_as_threat="Malicious", query_lang="1.0",
    )
    assert api.rules[0]["coolOffSettings"] == {"renotifyMinutes": 60}
    assert api.rules[0]["description"] == "Description"
    assert api.rules[0]["networkQuarantine"] is True
    assert api.rules[0]["treatAsThreat"] == "Malicious"
    assert run_module(event_query=QUERY)["changed"]
    assert api.writes[-1][0] == "PUT"
    assert api.writes[-1][2]["data"]["coolOffSettings"] == {"renotifyMinutes": 0}
    assert api.writes[-1][2]["data"]["description"] == ""
    assert not run_module(event_query=QUERY)["changed"]


@pytest.mark.parametrize("option", [{"description": "Description"}, {"cool_off_minutes": 60}])
def test_omitted_option_alone_triggers_update(api, run_module, option):
    run_module(event_query=QUERY, **option)
    assert run_module(event_query=QUERY)["changed"]
    assert api.writes[-1][0] == "PUT"
    assert api.writes[-1][2]["data"]["description"] == ""
    if "cool_off_minutes" in option:
        assert api.writes[-1][2]["data"]["coolOffSettings"] == {"renotifyMinutes": 0}
    else:
        assert "coolOffSettings" not in api.writes[-1][2]["data"]
    assert not run_module(event_query=QUERY)["changed"]


@pytest.mark.parametrize("query", [{"event_query": QUERY}, {"correlation_query": CORRELATION}])
def test_cool_off_reset_is_idempotent_and_can_be_reenabled(api, run_module, query):
    run_module(cool_off_minutes=60, **query)
    before = copy.deepcopy(api.rules[0])
    write_count = len(api.writes)
    assert run_module(_ansible_check_mode=True, **query)["changed"]
    assert api.rules[0] == before
    assert len(api.writes) == write_count
    assert run_module(**query)["changed"]
    assert api.writes[-1][2]["data"]["coolOffSettings"] == {"renotifyMinutes": 0}
    assert api.rules[0]["coolOffSettings"] is None
    assert not run_module(**query)["changed"]
    assert len(api.writes) == write_count + 1
    assert run_module(cool_off_minutes=1, **query)["changed"]
    assert api.rules[0]["coolOffSettings"] == {"renotifyMinutes": 1}
    assert not run_module(cool_off_minutes=1, **query)["changed"]


def test_update_without_existing_cool_off_omits_field(api, run_module):
    run_module(event_query=QUERY)
    api.rules[0]["coolOffSettings"] = None
    assert run_module(event_query=QUERY, severity="High")["changed"]
    assert "coolOffSettings" not in api.writes[-1][2]["data"]
    assert not run_module(event_query=QUERY, severity="High")["changed"]


def test_correlation_change_replaces_object_without_mutating_input(api, run_module):
    run_module(correlation_query=CORRELATION)
    changed = copy.deepcopy(CORRELATION)
    changed["subQueries"][0]["matchesRequired"] = 4
    assert run_module(correlation_query=changed)["changed"]
    assert api.writes[-1][2]["data"]["correlationParams"] == changed
    assert CORRELATION["subQueries"][0]["matchesRequired"] == 3
    assert not run_module(correlation_query=changed)["changed"]


@pytest.mark.parametrize("minutes", [1, 1440])
def test_cool_off_boundaries(api, run_module, minutes):
    run_module(event_query=QUERY, cool_off_minutes=minutes)
    assert api.writes[-1][2]["data"]["coolOffSettings"] == {"renotifyMinutes": minutes}
    assert not run_module(event_query=QUERY, cool_off_minutes=minutes)["changed"]


def test_temporary_expiration_normalization_and_reset_to_permanent(api, run_module):
    run_module(event_query=QUERY, expiration_date="2027-03-15T11:20:00+01:00")
    assert api.rules[0]["expiration"] == "2027-03-15T10:20:00Z"
    assert api.rules[0]["expirationMode"] == "Temporary"
    api.rules[0]["expiration"] = "2027-03-15T10:20:00.000000Z"
    assert not run_module(event_query=QUERY, expiration_date="2027-03-15T10:20:00Z")["changed"]
    assert run_module(event_query=QUERY)["changed"]
    assert api.rules[0]["expirationMode"] == "Permanent"
    assert "expiration" not in api.writes[-1][2]["data"]
    assert not run_module(event_query=QUERY)["changed"]


@pytest.mark.parametrize("first,second", [
    ({"event_query": QUERY}, {"correlation_query": CORRELATION}),
    ({"correlation_query": CORRELATION}, {"event_query": QUERY}),
])
def test_switch_query_type(api, run_module, first, second):
    run_module(**first)
    assert run_module(**second)["changed"]
    assert len(api.writes) == 2
    assert not run_module(**second)["changed"]
    if "event_query" in second:
        assert "correlationParams" not in api.writes[-1][2]["data"]
    else:
        assert "s1ql" not in api.writes[-1][2]["data"]


def test_site_parameter(api, run_module):
    assert run_module(site_name="Production", event_query=QUERY)["changed"]


@pytest.mark.parametrize("name", ["A", "AB", "Rule with spaces & + / umlaut \u00e4"])
def test_rule_lookup_name_prefilter(api, run_module, name):
    run_module(name=name, event_query=QUERY)
    assert not run_module(name=name, event_query=QUERY)["changed"]
    queries = [
        parse_qs(urlparse(endpoint).query)
        for method, endpoint, unused_body in api.calls
        if method == "GET" and "/cloud-detection/rules?" in endpoint
    ]
    assert queries
    for query in queries:
        if len(name) >= 2:
            assert query["name__contains"] == [name]
        else:
            assert "name__contains" not in query


def test_delete_and_repeated_absent_without_query(api, run_module):
    run_module(event_query=QUERY)
    assert run_module(state="absent")["changed"]
    assert api.writes[-1][0] == "DELETE"
    assert not run_module(state="absent")["changed"]


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
@pytest.mark.parametrize("query", [{"event_query": QUERY}, {"correlation_query": CORRELATION}])
def test_check_mode_does_not_write(api, run_module, operation, query):
    if operation != "create":
        run_module(**query)
    before = copy.deepcopy(api.rules)
    api.calls.clear()
    params = {"state": "absent"} if operation == "delete" else dict(query, severity="High")
    result = run_module(_ansible_check_mode=True, **params)
    assert result["changed"]
    assert result["message"].startswith("Would change: ")
    assert api.rules == before
    assert not api.writes


@pytest.mark.parametrize("query", [{"event_query": QUERY}, {"correlation_query": CORRELATION}])
@pytest.mark.parametrize("exists", [False, True])
def test_check_mode_no_changes_message(api, run_module, query, exists):
    if exists:
        run_module(**query)
    before = copy.deepcopy(api.rules)
    api.calls.clear()
    params = query if exists else {"state": "absent"}
    result = run_module(_ansible_check_mode=True, **params)
    assert not result["changed"]
    assert result["message"].startswith("No changes would be made")
    assert api.rules == before
    assert not api.writes


def test_pagination_exact_name_and_scope(api, run_module):
    run_module(event_query=QUERY)
    rule = copy.deepcopy(api.rules[0])
    api.calls.clear()
    api.pages = [
        [
            dict(rule, name="Test rule suffix"),
            dict(rule, scope="account"),
            dict(rule, scopeId=["another-site"]),
        ],
        [rule],
    ]
    assert not run_module(event_query=QUERY)["changed"]
    assert not api.writes
    assert any("cursor=1" in endpoint for unused_method, endpoint, unused_body in api.calls)
    for unused_method, endpoint, unused_body in api.calls:
        if "/cloud-detection/rules?" in endpoint:
            assert parse_qs(urlparse(endpoint).query)["name__contains"] == ["Test rule"]


def test_duplicate_names_fail_without_writes(api, run_module):
    run_module(event_query=QUERY)
    api.rules.append(copy.deepcopy(api.rules[0]))
    api.calls.clear()
    with pytest.raises(ModuleFailure) as failure:
        run_module(event_query=QUERY)
    assert "Multiple custom rules" in failure.value.result["msg"]
    assert not api.writes


def test_repeated_cursor_fails_without_writes(api, run_module, monkeypatch):
    original_call = api.call

    def repeated_cursor(module, api_endpoint, http_method="get", **kwargs):
        response = original_call(module, api_endpoint, http_method, **kwargs)
        if "/cloud-detection/rules?" in api_endpoint:
            response["pagination"]["nextCursor"] = "repeated"
        return response

    monkeypatch.setattr(api, "call", repeated_cursor)
    with pytest.raises(ModuleFailure) as failure:
        run_module(event_query=QUERY)
    assert "repeated pagination cursor" in failure.value.result["msg"]
    assert not api.writes


def test_custom_rules_site_parameter_is_mapped_for_shared_base(api, monkeypatch):
    monkeypatch.setattr(custom_rules.SentineloneCustomRules, "api_call", lambda self, *args, **kwargs: api.call(*args, **kwargs))
    module = basic.AnsibleModule.__new__(basic.AnsibleModule)
    module.params = {
        "console_url": "https://example.sentinelone.net", "token": "secret-token", "site_name": "Production",
        "name": "Test rule", "state": "absent",
    }
    obj = custom_rules.SentineloneCustomRules(module)
    assert obj.site_name == "Production"
    assert obj.site_id == SITE_ID
    assert obj.api_endpoint_custom_rules.endswith("/web/api/v2.1/cloud-detection/rules")


@pytest.mark.parametrize("params", [
    {},
    {"event_query": QUERY, "correlation_query": CORRELATION},
    {"event_query": ""},
    {"event_query": "  "},
    {"correlation_query": {}},
    {"event_query": QUERY, "cool_off_minutes": 0},
    {"event_query": QUERY, "cool_off_minutes": 1441},
    {"event_query": QUERY, "cool_off_minutes": -1},
    {"event_query": QUERY, "expiration_date": "2027-03-15"},
    {"event_query": QUERY, "expiration_date": "2027-03-15T10:20:00"},
    {"event_query": QUERY, "expiration_date": "not-a-date"},
    {"event_query": QUERY, "severity": "Invalid"},
    {"event_query": QUERY, "status": "Deleting"},
    {"event_query": QUERY, "query_lang": "3.0"},
    {"event_query": QUERY, "description": "x" * 2001},
    {"event_query": QUERY, "name": ""},
])
def test_invalid_arguments_fail_without_writes(api, run_module, params):
    with pytest.raises(ModuleFailure):
        run_module(**params)
    assert not api.writes


@pytest.mark.parametrize("value", [True, False])
def test_hide_logic_is_not_supported(api, run_module, value):
    with pytest.raises(ModuleFailure) as failure:
        run_module(event_query=QUERY, hide_logic=value)
    assert "Unsupported parameters" in failure.value.result["msg"]
    assert not api.calls


@pytest.mark.parametrize("operation,response", [
    ("create", {"data": {}}),
    ("create", {"data": None}),
    ("update", {"data": {}}),
    ("delete", {"data": {"affected": 0}}),
    ("delete", {"data": {"affected": 2}}),
])
def test_unsuccessful_write_responses_fail(api, run_module, operation, response):
    if operation != "create":
        run_module(event_query=QUERY)
    api.write_response = response
    with pytest.raises(ModuleFailure):
        if operation == "delete":
            run_module(state="absent")
        else:
            run_module(event_query=QUERY, severity="High")


@pytest.mark.parametrize("status,expected", [("Activating", "Active"), ("Disabling", "Disabled")])
def test_transitional_status_does_not_trigger_repeated_updates(api, run_module, status, expected):
    run_module(event_query=QUERY, status=expected)
    api.rules[0]["status"] = status
    assert not run_module(event_query=QUERY, status=expected)["changed"]


def test_undefined_threat_alias(api, run_module):
    run_module(event_query=QUERY, treat_as_threat="Undefined")
    assert api.rules[0]["treatAsThreat"] == "UNDEFINED"
    assert not run_module(event_query=QUERY)["changed"]


def test_null_threat_response_is_undefined(api, run_module):
    run_module(event_query=QUERY)
    api.rules[0]["treatAsThreat"] = None
    assert not run_module(event_query=QUERY)["changed"]
    assert run_module(event_query=QUERY, treat_as_threat="Suspicious")["changed"]
    assert api.rules[0]["treatAsThreat"] == "Suspicious"


@pytest.mark.parametrize("query", [{"event_query": QUERY}, {"correlation_query": CORRELATION}])
@pytest.mark.parametrize("desired,returned,action", [
    ("Active", "Draft", "enable"),
    ("Disabled", "Draft", "disable"),
    ("Draft", "Active", RULE_ID),
])
def test_creation_enforces_requested_status(api, run_module, query, desired, returned, action):
    api.create_status = returned
    assert run_module(status=desired, **query)["changed"]
    assert len(api.writes) == 2
    assert api.writes[-1][0] == "PUT"
    assert api.writes[-1][1].endswith("/" + action)
    if desired == "Draft":
        assert api.writes[-1][2]["data"]["status"] == "Draft"
    else:
        assert api.writes[-1][2] == {"filter": {"siteIds": [SITE_ID], "ids": [RULE_ID]}}
    assert custom_rules.SentineloneCustomRules.normalize_status(api.rules[0]["status"]) == desired
    assert not run_module(status=desired, **query)["changed"]
    assert len(api.writes) == 2


@pytest.mark.parametrize("desired,returned", [
    ("Active", "Active"), ("Active", "Activating"), ("Disabled", "Disabled"),
    ("Disabled", "Disabling"), ("Draft", "Draft"),
])
def test_creation_accepts_matching_and_transitional_status(api, run_module, desired, returned):
    api.create_status = returned
    assert run_module(event_query=QUERY, status=desired)["changed"]
    assert len(api.writes) == 1
    assert not run_module(event_query=QUERY, status=desired)["changed"]


@pytest.mark.parametrize("desired", ["Active", "Disabled", "Draft"])
def test_update_enforces_requested_status(api, run_module, desired):
    run_module(event_query=QUERY, status=desired)
    api.update_status = "Draft" if desired != "Draft" else "Active"
    if desired == "Draft":
        # The first update differs; allow the follow-up Draft PUT to take effect.
        original_call = api.call

        def reset_override(*args, **kwargs):
            response = original_call(*args, **kwargs)
            if len(args) > 2 and args[2] == "PUT":
                api.update_status = None
            return response

        api.call = reset_override
    assert run_module(event_query=QUERY, status=desired, severity="High")["changed"]
    assert len(api.writes) == 3
    assert not run_module(event_query=QUERY, status=desired, severity="High")["changed"]


@pytest.mark.parametrize("affected", [0, 2, None])
def test_status_endpoint_must_confirm_exactly_one_rule(api, run_module, affected):
    api.create_status = "Draft"
    api.action_affected = affected
    with pytest.raises(ModuleFailure) as failure:
        run_module(event_query=QUERY, status="Disabled")
    assert "exactly one rule" in failure.value.result["msg"]
    assert failure.value.result["changed"]
    assert failure.value.result["rule_id"] == RULE_ID


@pytest.mark.parametrize("desired,returned", [("Active", "Draft"), ("Disabled", "Active"), ("Draft", "Active")])
def test_status_enforcement_must_be_verified(api, run_module, desired, returned):
    api.create_status = returned
    api.action_status = returned
    api.update_status = returned
    with pytest.raises(ModuleFailure) as failure:
        run_module(event_query=QUERY, status=desired)
    assert f"expected {desired} after enforcement" in failure.value.result["msg"]
    assert len(api.writes) == 2


def test_status_enforcement_fails_if_created_rule_cannot_be_read(api, run_module):
    api.create_status = "Draft"
    api.pages = [[]]
    with pytest.raises(ModuleFailure) as failure:
        run_module(event_query=QUERY, status="Disabled")
    assert "Could not read" in failure.value.result["msg"]
    assert failure.value.result["rule_id"] == RULE_ID


def test_check_mode_does_not_create_or_enforce_status(api, run_module):
    api.create_status = "Draft"
    assert run_module(event_query=QUERY, status="Disabled", _ansible_check_mode=True)["changed"]
    assert not api.writes
