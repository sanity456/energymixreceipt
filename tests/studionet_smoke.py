"""Opt-in full StudioNet flow; the wallet is encrypted outside this repository."""
import json
import secrets

from gltest.types import TransactionHashVariant
from release_support import prepare, save_proof, send


def test_studionet_energy_mix_flow():
    ctx = prepare("energy_mix_receipt.py", ("owner",))
    owner, account = ctx["contracts"]["owner"], ctx["accounts"]["owner"]
    transactions = {"deploy": ctx["deployment_hash"]}
    mix_key = "release_" + secrets.token_hex(4)
    send(transactions, "record_mix", owner.record_mix(args=[mix_key, "2026-10", ["Solar photovoltaic panels", "Natural gas turbine", "Wind turbines"], [60, 30, 10]]))
    mix_id = account.address.lower() + ":" + mix_key
    initial = json.loads(owner.get_mix(args=[mix_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert initial["status"] == "UNREVIEWED" and initial["total_mwh"] == 100
    send(transactions, "classify_mix", owner.classify_mix(args=[mix_id]))
    final = json.loads(owner.get_mix(args=[mix_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert final["status"] == "CLASSIFIED" and final["categories"] == ["SOLAR", "FOSSIL", "WIND"], final
    assert final["renewable_mwh"] == 70 and final["renewable_bps"] == 7000, final
    save_proof(ctx, transactions, mix_id, "CLASSIFIED")
