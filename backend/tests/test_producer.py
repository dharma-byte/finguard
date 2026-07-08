from datetime import datetime, timezone

import pandas as pd

from producer import NUM_SYNTHETIC_ACCOUNTS, to_message


def test_to_message_builds_expected_shape():
    row = pd.Series(
        {
            "Time": 120.0,
            "Amount": 49.99,
            "Class": 0,
            **{f"V{i}": float(i) for i in range(1, 29)},
        }
    )
    start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    message = to_message(idx=3, row=row, start_time=start_time)

    assert message["account_id"] == f"acct_{3 % NUM_SYNTHETIC_ACCOUNTS:04d}"
    assert message["amount"] == 49.99
    assert message["time_offset_seconds"] == 120.0
    assert message["true_label"] == 0
    assert set(message["features"].keys()) == {f"V{i}" for i in range(1, 29)}
    assert message["timestamp"] == "2026-01-01T00:02:00+00:00"
