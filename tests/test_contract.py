import json
from pathlib import Path

import pytest


@pytest.fixture
def setup(direct_vm, direct_deploy, direct_accounts):
    owner, auditor, beneficiary, outsider = direct_accounts[:4]
    direct_vm.sender = owner
    source = Path(__file__).parents[1] / "contracts" / "energy_mix_receipt.py"
    contract = direct_deploy(str(source), sdk_version="v0.2.16")
    mix_id = contract.record_mix("october", "2026-10",
        ["Solar photovoltaic generation", "Gas turbine generation", "Wind turbine generation"],
        [60, 30, 10], auditor, beneficiary)
    return contract, mix_id, owner, auditor, beneficiary, outsider


def mock(vm, categories, alignment="SUPPORTED"):
    vm.clear_mocks()
    vm.mock_llm("Reconcile a supplier's frozen generation rows", json.dumps({"categories": categories, "alignment": alignment}))


REPORT = "For 2026-10, I attest 60 MWh solar photovoltaic generation, 30 MWh gas turbine generation, and 10 MWh wind turbine generation."


def test_issued_mix_allows_beneficiary_partial_retirement(setup, direct_vm):
    contract, mix_id, _owner, auditor, beneficiary, _outsider = setup
    direct_vm.sender = auditor
    mock(direct_vm, ["SOLAR", "FOSSIL", "WIND"])
    assert contract.attest_mix(mix_id, REPORT) == "ISSUED"
    state = json.loads(contract.get_mix(mix_id))
    assert state["renewable_mwh"] == 70 and state["renewable_bps"] == 7000
    assert state["categories"] == ["SOLAR", "FOSSIL", "WIND"]
    assert direct_vm.run_validator(leader_result={"categories": ["SOLAR", "FOSSIL", "WIND"], "alignment": "SUPPORTED"})
    assert not direct_vm.run_validator(leader_result={"categories": ["SOLAR", "WIND", "WIND"], "alignment": "SUPPORTED"})
    direct_vm.sender = beneficiary
    assert contract.retire(mix_id, 40) == 30
    assert contract.retire(mix_id, 30) == 0
    with direct_vm.expect_revert("retirement exceeds"):
        contract.retire(mix_id, 1)


def test_unauthorized_uncertain_and_malformed_cannot_issue(setup, direct_vm):
    contract, mix_id, owner, auditor, beneficiary, outsider = setup
    direct_vm.sender = outsider
    with direct_vm.expect_revert("pending mix auditor only"):
        contract.attest_mix(mix_id, REPORT)
    direct_vm.sender = beneficiary
    with direct_vm.expect_revert("issued mix beneficiary only"):
        contract.retire(mix_id, 1)
    direct_vm.sender = auditor
    before = contract.get_mix(mix_id)
    mock(direct_vm, ["SOLAR", "FOSSIL"])
    with direct_vm.expect_revert("invalid category vector"):
        contract.attest_mix(mix_id, REPORT)
    assert contract.get_mix(mix_id) == before
    mock(direct_vm, ["SOLAR", "FOSSIL", "WIND"], "UNCERTAIN")
    assert contract.attest_mix(mix_id, "The mix looks fine.") == "UNRESOLVED"
    direct_vm.sender = owner
    with direct_vm.expect_revert("issued mix beneficiary only"):
        contract.retire(mix_id, 1)


def test_input_bounds_owner_scope_and_conflict(setup, direct_vm):
    contract, mix_id, owner, auditor, beneficiary, outsider = setup
    with direct_vm.expect_revert("already exists"):
        contract.record_mix("october", "2026-10", ["Solar"], [1], auditor, beneficiary)
    with direct_vm.expect_revert("aligned sources"):
        contract.record_mix("bad", "2026-10", ["Solar", "Wind"], [1], auditor, beneficiary)
    with direct_vm.expect_revert("amount out of range"):
        contract.record_mix("bad", "2026-10", ["Solar"], [0], auditor, beneficiary)
    with direct_vm.expect_revert("three distinct"):
        contract.record_mix("bad", "2026-10", ["Solar"], [1], owner, beneficiary)
    direct_vm.sender = outsider
    assert contract.record_mix("october", "2026-10", ["Hydro"], [1], auditor, beneficiary) != mix_id
