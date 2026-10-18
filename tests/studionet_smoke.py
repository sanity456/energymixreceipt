"""Opt-in full StudioNet flow; the wallet is encrypted outside this repository."""
import json
import secrets
from pathlib import Path

from gltest.types import TransactionHashVariant
from release_support import prepare, reject, save_negative_proof, save_proof, send


def test_studionet_energy_mix_flow():
    ctx = prepare("energy_mix_receipt.py", ("owner", "auditor", "beneficiary"))
    owner, account = ctx["contracts"]["owner"], ctx["accounts"]["owner"]
    transactions = {"deploy": ctx["deployment_hash"]}
    mix_key = "release_" + secrets.token_hex(4)
    send(transactions, "record_mix", owner.record_mix(args=[mix_key, "2026-10", ["Solar photovoltaic panels", "Natural gas turbine", "Wind turbines"], [60, 30, 10], ctx["accounts"]["auditor"].address, ctx["accounts"]["beneficiary"].address]))
    mix_id = account.address.lower() + ":" + mix_key
    initial = json.loads(owner.get_mix(args=[mix_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert initial["status"] == "AWAITING_AUDITOR" and initial["total_mwh"] == 100
    report = "For 2026-10 I independently attest 60 MWh from solar photovoltaic panels, 30 MWh from a natural gas turbine, and 10 MWh from wind turbines."
    send(transactions, "attest_mix", ctx["contracts"]["auditor"].attest_mix(args=[mix_id, report]))
    send(transactions, "retire", ctx["contracts"]["beneficiary"].retire(args=[mix_id, 25]))
    final = json.loads(owner.get_mix(args=[mix_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert final["status"] == "ISSUED" and final["categories"] == ["SOLAR", "FOSSIL", "WIND"], final
    assert final["renewable_mwh"] == 70 and final["renewable_bps"] == 7000 and final["retired_mwh"] == 25, final

    save_proof(ctx, transactions, mix_id, "ISSUED_WITH_25_MWH_RETIRED")


def test_studionet_over_retirement_guard():
    ctx = prepare("energy_mix_receipt.py", ("owner", "auditor", "beneficiary"))
    manifest = json.loads((Path(__file__).parents[1] / "deployments" / "studionet.json").read_text(encoding="utf-8"))
    mix_id = manifest["full_flow_test"]["workflow_id"]
    owner = ctx["contracts"]["owner"]
    transactions = {}
    before = json.loads(owner.get_mix(args=[mix_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert before["status"] == "ISSUED" and before["renewable_mwh"] - before["retired_mwh"] == 45, before
    # A single rejected transaction demonstrates the bound without repeating
    # the LLM-based issuance workflow.
    rejected = reject(transactions, "reject_over_retirement",
        ctx["contracts"]["beneficiary"].retire(args=[mix_id, 46]))
    after_rejection = json.loads(owner.get_mix(args=[mix_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert after_rejection == before, after_rejection
    details = {**rejected, "mix_id": mix_id, "attempted_mwh": 46,
        "available_before_attempt_mwh": 45, "retired_after_attempt_mwh": after_rejection["retired_mwh"],
        "state_unchanged": True, "state_after": after_rejection}
    save_negative_proof(transactions, "over_retirement", details)
