# Security Policy

## Supported Versions

Only the latest active minor release receives security updates, vulnerability patches, and biosecurity filter enhancements.

| Version | Supported | Status |
| :--- | :---: | :--- |
| `2.2.x` | :white_check_mark: | Active release — fully supported |
| `< 2.2.0` | :x: | End-of-life — upgrade recommended |

---

## Biosecurity & Computational Safety Scope

This repository implements automated biocomputational pipelines and interactive cockpits interfacing with NVIDIA BioNeMo microservices. Defense-in-depth safety controls encompass:

1. **Sequence Sanitization & Biosecurity Screening:**
   - Canonical 20 IUPAC amino acid residue enforcement on macromolecular targets prior to ESM-2 / ESMFold inference.
   - Rejection of invalid characters, anomalous insertions, and prohibited biosecurity toxin/pathogen sequence signatures.

2. **Cheminformatics Validation:**
   - Strict RDKit SMILES sanitization with explicit valence checking, ring closure verification, and Lipinski Rule-of-5 boundary audits.
   - Prevention of malformed or chemically non-viable structures prior to DiffDock molecular docking or generative iterations.

3. **In-Flight Rate Limiting & Quota Guards:**
   - Client IP-based rate limiting via `InFlightRateLimiter` and daily compute budget limits via `TrialLimiter`.
   - Protection against denial-of-service and unauthorized API credit depletion.

4. **Secret Scrubbing & Credential Isolation:**
   - Zero hardcoding of API credentials; all remote invocations depend on `NVIDIA_API_KEY` loaded from environment variables.
   - Automated log and exception sanitization via `SecretScrubber` to prevent accidental credential leakage in production telemetry.

---

## Reporting a Vulnerability

We take security and biocomputational safety seriously. If you identify a vulnerability or security bypass:

1. **Do not create a public issue or pull request.**
2. Report the vulnerability privately via **[GitHub Security Advisories](https://github.com/Jorwalzzz/bionemo-nim-benchmark/security/advisories/new)**.
3. Alternatively, email the maintainers directly at `contact@jorwal.dev` with the subject `[SECURITY] BioNeMo Benchmark Vulnerability Report`.

### What to Include
- Detailed description of the vulnerability, including affected endpoints or modules.
- Minimal reproducible proof-of-concept (PoC) or step-by-step instructions.
- Potential impact assessment (e.g., DoS, data exposure, prompt injection, biosecurity bypass).

### Response SLA & Disclosure
- **Acknowledgment:** Within 48 hours of initial report receipt.
- **Triage & Assessment:** Status update and planned remediation timeline within 5 business days.
- **Coordinated Disclosure:** Security advisories and patched releases are coordinated with the reporter prior to public release.
