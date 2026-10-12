import json
from pathlib import Path

import pytest


@pytest.fixture
def setup(direct_vm, direct_deploy, direct_accounts):
    owner, outsider = direct_accounts[:2]
    direct_vm.sender = owner
    source = Path(__file__).parents[1] / "contracts" / "energy_mix_receipt.py"
    contract = direct_deploy(str(source), sdk_version="v0.2.16")
    mix_id = contract.record_mix("october", "2026-10", ["Solar photovoltaic generation", "Gas turbine generation", "Wind turbine generation"], [60, 30, 10])
    return contract, mix_id, owner, outsider


def mock(vm, categories):
    vm.clear_mocks()
    vm.mock_llm("Map each public generation-source description", json.dumps({"categories": categories}))


def test_vector_mapping_and_renewable_arithmetic(setup, direct_vm):
    contract, mix_id, _owner, _outsider = setup
    mock(direct_vm, ["SOLAR", "FOSSIL", "WIND"])
    assert contract.classify_mix(mix_id) == 7000
    state = json.loads(contract.get_mix(mix_id))
    assert state["renewable_mwh"] == 70 and state["total_mwh"] == 100
    assert state["categories"] == ["SOLAR", "FOSSIL", "WIND"]
    assert direct_vm.run_validator(leader_result=["SOLAR", "FOSSIL", "WIND"])
    assert not direct_vm.run_validator(leader_result=["SOLAR", "WIND", "WIND"])
    with direct_vm.expect_revert("already classified"):
        contract.classify_mix(mix_id)


def test_unauthorized_and_malformed_model_cannot_finalize(setup, direct_vm):
    contract, mix_id, owner, outsider = setup
    direct_vm.sender = outsider
    with direct_vm.expect_revert("mix owner only"):
        contract.classify_mix(mix_id)
    direct_vm.sender = owner
    before = contract.get_mix(mix_id)
    mock(direct_vm, ["SOLAR", "FOSSIL"])
    with direct_vm.expect_revert("invalid category vector"):
        contract.classify_mix(mix_id)
    assert contract.get_mix(mix_id) == before


def test_input_bounds_and_owner_scoped_ids(setup, direct_vm):
    contract, mix_id, _owner, outsider = setup
    with direct_vm.expect_revert("already exists"):
        contract.record_mix("october", "2026-10", ["Solar"], [1])
    with direct_vm.expect_revert("aligned sources"):
        contract.record_mix("bad", "2026-10", ["Solar", "Wind"], [1])
    with direct_vm.expect_revert("amount out of range"):
        contract.record_mix("bad", "2026-10", ["Solar"], [0])
    direct_vm.sender = outsider
    assert contract.record_mix("october", "2026-10", ["Hydro"], [1]) != mix_id
