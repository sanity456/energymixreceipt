# Release audit

- Mechanism: consensus normalizes an ordered vector of generation-source descriptions; deterministic code aggregates owner-declared MWh and computes renewable share. There is no threshold event, run selection, or observer quorum.
- Source policy: all descriptions and quantities are public caller declarations. The contract never scrapes supplier sites or authenticates generation claims.
- Security: owner-scoped keys, owner-only one-time classification, aligned vector and amount bounds, strict result parsing, and independent validator rerun. No funds are held.
- Local gates: GenVM lint and strict type check passed; 3 direct tests passed, including owner authorization, vector mismatch, and malformed output.
- StudioNet gate: full deploy/record/classify flow passed with its own fresh wallet; final state `CLASSIFIED` at 7,000 bps; read-only release proof passed. The manifest binds receipt hashes, source bytes, and ABI.
- Limits: the result is an accounting view of declared amounts, not a renewable-energy certificate.
