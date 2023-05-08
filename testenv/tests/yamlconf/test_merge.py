
import pytest

from kvmd.yamlconf import merger


@pytest.mark.asyncio
async def test_no_merge_strategy() -> None:
    dest: dict = {"a": "1", "b": "2", "c": [1, 2, 3, {"d": 4}]}
    src: dict = {"a": "3", "b": "2", "c": [3, 4, 5, {"e": 6}]}
    merger.yaml_merge(dest, src)
    assert dest == {"a": "3", "b": "2", "c": [3, 4, 5, {"e": 6}]}


@pytest.mark.asyncio
async def test_merge_strategy_merge() -> None:
    dest: dict = {"a": "1", "b": "2", "c": [1, 2, 3, {"d": 4}]}
    src: dict = {"Merge Strategy": "Merge", "a": "3", "b": "2", "c": [3, 4, 5, {"e": 6}]}
    merger.yaml_merge(dest, src)
    assert dest == {"a": "3", "b": "2", "c": [3, 4, 5, {"e": 6}]}


@pytest.mark.asyncio
async def test_default_is_same_as_merge_strategy() -> None:
    exp_result: dict = {"a": "3", "b": "2", "c": [3, 4, 5, {"e": 6}]}
    dest: dict = {"a": "1", "b": "2", "c": [1, 2, 3, {"d": 4}]}
    src: dict = {"a": "3", "b": "2", "c": [3, 4, 5, {"e": 6}]}
    merger.yaml_merge(dest, src)
    assert dest == exp_result
    src: dict = {"Merge Strategy": "Merge", "a": "3", "b": "2"}
    merger.yaml_merge(dest, src)
    assert dest == exp_result
