from unittest import mock

import pytest

from macuitest.lib import core
from macuitest.lib.core import wait_condition


@pytest.fixture
def clock():
    now = [0.0]

    def sleep(seconds):
        now[0] += seconds

    with (
        mock.patch.object(core.time, "sleep", side_effect=sleep) as sleep_mock,
        mock.patch.object(core.time, "monotonic", side_effect=lambda: now[0]),
    ):
        yield sleep_mock


def test_returns_a_ready_result_without_sleeping(clock):
    assert wait_condition(lambda: "ready") == "ready"
    clock.assert_not_called()


def test_polls_every_interval_until_truthy(clock):
    results = iter([None, 0, "done"])

    assert wait_condition(lambda: next(results), interval=0.2) == "done"
    assert [call.args[0] for call in clock.call_args_list] == [0.2, 0.2]


def test_returns_false_after_the_timeout(clock):
    predicate = mock.Mock(return_value=None)

    assert wait_condition(predicate, timeout=1, interval=0.25) is False
    assert predicate.call_count == 5


def test_listed_exceptions_count_as_falsy(clock):
    results = iter([LookupError(), "found"])

    def predicate():
        result = next(results)
        if isinstance(result, Exception):
            raise result
        return result

    assert wait_condition(predicate, 1, (LookupError,)) == "found"


def test_passes_extra_arguments_to_the_predicate(clock):
    assert wait_condition(lambda a, b=0: a + b, 1, (Exception,), 2, b=3) == 5


def test_zero_timeout_still_checks_once(clock):
    predicate = mock.Mock(return_value=None)

    assert wait_condition(predicate, timeout=0) is False
    predicate.assert_called_once()
