# EnergyMixReceipt

Batch B2. A reusable GenLayer intelligent contract for a declared generation mix and a nontransferable, single-use renewable allocation. A supplier records one to eight source descriptions and MWh amounts and designates a separate auditor and beneficiary. The auditor submits a wallet-bound report. Validators independently reconcile that report with every row and classify each source; only an aligned report issues a renewable amount that the beneficiary can retire in bounded increments.

Descriptions, MWh values, and the auditor report remain declarations. The contract does not authenticate a meter, regulated renewable certificate, or environmental claim. A category of `OTHER` does not count as renewable. The designated auditor must be genuinely independent for real use; this is not a tradable REC or carbon credit.

## Interface

`record_mix(mix_key, period, descriptions, amounts_mwh, auditor, beneficiary)` freezes an owner-scoped mix. Only the auditor may call `attest_mix(mix_id, auditor_report)`. Only the beneficiary may call `retire(mix_id, amount_mwh)` after issue, and retirement cannot exceed the unretired renewable amount. `get_mix(mix_id)` returns canonical JSON; `get_mix_count()` returns the number of mixes.

## Review boundary

The model maps descriptions to a same-length category vector and decides whether the separately attested report supports the period, every type, and every amount. Validators independently rerun and compare both decision fields. Amounts, share, and remaining retirement capacity are deterministic. Role separation, caps, immutable rows, and one-time attestation protect the accounting transition.

## Verification

Use the GenVM v0.2.16 bundle that contains the contract's pinned runner. In PowerShell run `$env:PYTHONUTF8='1'; $env:GENVM_VERSION='v0.2.16'`, then run `genvm-lint check contracts/energy_mix_receipt.py`, `genvm-lint typecheck contracts/energy_mix_receipt.py --strict`, `pytest -q`, and `python tests/studionet_release_proof.py`. `tests/studionet_smoke.py` exercises the full StudioNet flow and a rejected over-retirement attempt, then reads the mix again to verify the failed call did not change retired MWh. `deployments/studionet.json` binds the deployment to the exact source commit and hash and records the ABI, transaction receipts, negative-test execution result, and readback. `tests/studionet_release_proof.py` rechecks the source, ABI, and evidence.

Current StudioNet deployment: [0xf405D47b70b839e3F369F9f7c196e98A219a22a8](https://explorer-studio.genlayer.com/address/0xf405D47b70b839e3F369F9f7c196e98A219a22a8). The exact source hash and finalized receipts are in `deployments/studionet.json`. Do not submit the older address. See `AUDIT.md` for the review boundary and test results.
