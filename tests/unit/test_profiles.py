import hashlib
from unittest.mock import MagicMock

import pytest
from neo4j.exceptions import ServiceUnavailable
from pydantic import ValidationError

from backend.errors import ApiError
from backend.schemas import PersonalLogin, Profile, ProfileInput
from backend.services import profiles, sessions


def test_name_is_trimmed_and_role_cannot_be_supplied():
    assert ProfileInput(displayName="  Isaac  ").displayName == "Isaac"
    for payload in ({"displayName": "   "}, {"displayName": "x" * 101},
                    {"displayName": "Isaac", "role": "editor"}):
        with pytest.raises(ValidationError):
            ProfileInput(**payload)


def test_creation_commits_identity_and_only_code_hash_before_graph_sync():
    sql, graph = MagicMock(), MagicMock()
    events = []
    def save(profile_id, name, code_hash, *args):
        events.append("sql")
        return Profile(profileId=profile_id, displayName=name, role="listener")
    sql.create_personal_profile.side_effect = save
    sql.graph_pending.return_value = True
    graph.ensure_profile.side_effect = lambda _: events.append("graph")
    created, token = profiles.create(sql, graph, ProfileInput(displayName="Isaac"), None)
    assert events == ["sql", "graph"]
    assert profiles.ACCESS_PATTERN.fullmatch(created.accessCode)
    args = sql.create_personal_profile.call_args.args
    assert args[2] == hashlib.sha256(created.accessCode.encode("ascii")).hexdigest()
    assert created.accessCode not in args
    assert args[3] == sessions.hash_cookie(token)
    assert not created.graphPending


def test_failed_graph_keeps_durable_pending_flag_and_can_be_retried():
    sql, graph = MagicMock(), MagicMock()
    sql.graph_pending.return_value = True
    graph.ensure_profile.side_effect = ServiceUnavailable("test outage")
    assert profiles.sync_graph(sql, graph, "p-test", tolerate_failure=True)
    sql.mark_graph_synced.assert_not_called()
    with pytest.raises(ServiceUnavailable):
        profiles.sync_graph(sql, graph, "p-test")
    graph.ensure_profile.side_effect = None
    assert not profiles.sync_graph(sql, graph, "p-test")
    sql.mark_graph_synced.assert_called_once_with("p-test")


def test_malformed_code_and_unknown_profile_do_not_start_session():
    sql, graph = MagicMock(), MagicMock()
    sql.find_personal_profile.return_value = None
    for code in ("Isaac", "p-" + "a" * 32 + "." + "b" * 43):
        with pytest.raises(ApiError) as error:
            profiles.sign_in(sql, graph, PersonalLogin(code=code), None)
        assert error.value.status == 401
    sql.create_session.assert_not_called()
