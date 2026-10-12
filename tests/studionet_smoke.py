"""Opt-in full StudioNet flow; the wallet is encrypted outside this repository."""
import json
import secrets

from gltest.types import TransactionHashVariant
from release_support import prepare, save_proof, send


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
