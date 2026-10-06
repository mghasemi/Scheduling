import pandas as pd
import pytest

from scheduling.use_cases.pcb import Primary911


def test_pcb_api_is_separate_with_a_deprecated_root_alias():
    import scheduling

    assert "Perimeter" not in scheduling.__all__
    with pytest.warns(DeprecationWarning, match="scheduling.use_cases.pcb"):
        assert scheduling.Perimeter.__name__ == "Perimeter"


def test_primary911_uses_explicit_source_and_cache_paths(tmp_path):
    source = tmp_path / "calls.csv"
    cache = tmp_path / "normalized" / "calls.csv"
    pd.DataFrame(
        [
            {
                "Phone": "555-0100",
                "Name": "Caller",
                "Municipality": "City",
                "Offer Time": "2024-01-01 10:00:00",
                "Answer Time": "2024-01-01 10:00:10",
                "Transfer Time": "2024-01-01 10:01:00",
                "Disconnect Time": "2024-01-01 10:05:00",
                "Transfer Answer Time": "2024-01-01 10:01:10",
                "Service Class": "Emergency",
                "Transfer DN": "7809443700",
            },
            {
                "Phone": "555-0101",
                "Name": "Caller",
                "Municipality": "City",
                "Offer Time": "2024-01-02 10:00:00",
                "Answer Time": "2024-01-02 10:00:10",
                "Transfer Time": "2024-01-02 10:01:00",
                "Disconnect Time": "2024-01-02 10:05:00",
                "Transfer Answer Time": "2024-01-02 10:01:10",
                "Service Class": "Emergency",
                "Transfer DN": "7809443700",
            },
        ]
    ).to_csv(source, index=False)

    analysis = Primary911(fname=source, cache_path=cache)

    assert len(analysis.df) == 1
    assert analysis.daily_avg == 1
    assert analysis.df.iloc[0]["duration"] == 300
    assert cache.is_file()
