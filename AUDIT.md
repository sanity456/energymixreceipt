# Release audit

- Mechanism (v2): frozen generation rows, a separate auditor's wallet-bound report, validator-agreed categories and row/report alignment, then deterministic renewable MWh accounting and beneficiary-only bounded retirement.
- Source policy: rows and quantities are public supplier declarations and the audit is a separate public wallet-bound declaration. The contract never scrapes supplier sites or authenticates physical generation claims.
- Security: owner-scoped keys, three distinct nonzero roles, one-time auditor attestation, beneficiary-only retirement bounded by the issued renewable amount, aligned vector and amount bounds, strict result parsing, and independent validator rerun. No funds are held.
- Local gates: GenVM lint and strict type check passed; 3 v2 direct tests passed, including role authorization, vector mismatch, malformed output, and over-retirement.
- StudioNet gate: fresh v2 deployment, record/auditor-attest/beneficiary-retire flow, and read-only release proof passed with three isolated wallets. The deployed source is byte-identical to `contracts/energy_mix_receipt.py`, the ABI matches, and all four receipts finalized. The v1 address must not be submitted as evidence for this source.
- Limits: issuer/auditor agreement and bounded retirement do not produce a regulated renewable-energy certificate or independently prove metered generation. A real deployment needs an independent auditor-selection policy.
