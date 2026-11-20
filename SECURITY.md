# Security Policy

## Supported Versions

Only active releases receive security updates, vulnerability patches, and biosecurity filter enhancements.

| Version | Supported | Status |
| :--- | :---: | :--- |
| `2.2.x` | :white_check_mark: | Active release — fully supported |
| `< 2.2.0` | :x: | End-of-life — upgrade recommended |

---

## Defense-in-Depth & Supply Chain Security Architecture

This repository implements automated biocomputational pipelines and interactive cockpits interfacing with NVIDIA BioNeMo microservices. Defense-in-depth security controls encompass:

### 1. Automated CI Security Gates & Supply Chain Hardening
- **Python SAST (`bandit`):** Continuous automated static analysis scanning codebase AST for security flaws (CWE-22, CWE-78, CWE-88, CWE-89) at Medium and High severity.
- **Dependency CVE Auditing (`pip-audit`):** Automated auditing of declared dependencies in `pyproject.toml` against PyPI/OSV advisory databases to prevent supply chain contamination.
- **Secret Pattern Scanning:** Pre-merge and CI gates that scan all tracked files for exposed credential patterns (e.g. `nvapi-`, `ghp_`, `github_pat_`, and private key headers).
- **Least-Privilege GitHub Actions:** All CI workflows strictly pin permissions to `contents: read` and enforce explicit `timeout-minutes` (15m) to mitigate hijacked runner abuse.

### 2. Frontend & DOM Hardening
- **Strict Content Security Policy (CSP):** Meta CSP allowlisting only `'self'`, Google Fonts, explicitly trusted CDNs, and RCSB endpoints (`https://files.rcsb.org`, `https://data.rcsb.org`), with `object-src 'none'`, `base-uri 'self'`, and `form-action 'self'`.
- **Subresource Integrity (SRI):** External vendor scripts and stylesheets are pinned with cryptographic SHA-384 hashes (`integrity="sha384-..." crossorigin="anonymous"`).
- **DOM XSS Sanitization:** All dynamic data insertions (RCSB entry titles, user uploads, SMILES strings) use safe DOM sinks (`textContent`) or contextual HTML escaping (`escapeHtml()`).
- **Client-Side Upload DoS Guard:** Hard file size limits (`MAX_FILE_BYTES = 5 MB`) and row caps (`MAX_ROWS = 5000`) protect against browser thread exhaustion.

### 3. API Gateway, Network & Server Hardening
- **Strict PDB Identifier Validation:** Input PDB IDs are verified against regex `^[1-9][A-Za-z0-9]{3}$`, rejecting command injections, path traversal tokens, and shell metacharacters.
- **Path Traversal Guard:** All filesystem accesses enforce directory confinement via `Path.resolve().is_relative_to(ALLOWED_ROOT)`, preventing CWE-22 directory traversal.
- **SSRF Mitigation & Outbound Allowlisting:** Outbound HTTP requests are restricted to explicit trusted hosts (`files.rcsb.org`, `data.rcsb.org`, `integrate.api.nvidia.com`) with mandatory TLS verification and strict timeouts.
- **Local Server Isolation:** FastAPI and cockpit servers bind strictly to `127.0.0.1` by default, enforce CORS origin boundaries, and emit hardened headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`).
- **In-Flight Secret Scrubbing:** `SecretScrubber` redacts API keys and tokens from exceptions, log streams, and debug telemetry.

### 4. Biosecurity & Computational Safety Scope
- **Sequence Screening:** Macromolecular targets are validated against canonical 20 IUPAC amino acid residues prior to ESM-2 / ESMFold inference.
- **Dual-Use Pathogen Detection:** Multi-scale k-mer and sliding-window homology checks against Select Agent catalogs (NIST / GDM-100 compliant).
- **Cheminformatics Validation:** Strict RDKit SMILES sanitization with explicit valence checking, ring closure verification, and Lipinski Rule-of-5 boundary audits prior to DiffDock molecular docking.

---

## Reporting a Vulnerability

We take security and biocomputational safety seriously. If you identify a vulnerability or security bypass:

1. **Do not create a public issue or pull request.**
2. Report the vulnerability privately via **[GitHub Security Advisories](https://github.com/Jorwalzzz/bionemo-nim-benchmark/security/advisories/new)**.
3. Alternatively, email the maintainers directly at `contact@jorwal.dev` with the subject `[SECURITY] BioNeMo Benchmark Vulnerability Report`.

### What to Include
- Detailed description of the vulnerability, including affected endpoints or modules.
- Minimal reproducible proof-of-concept (PoC) or step-by-step instructions.
- Potential impact assessment (e.g., DoS, data exposure, command execution, biosecurity bypass).

### Response SLA & Disclosure
- **Acknowledgment:** Within 48 hours of initial report receipt.
- **Triage & Assessment:** Status update and planned remediation timeline within 5 business days.
- **Coordinated Disclosure:** Security advisories and patched releases are coordinated with the reporter prior to public release.
