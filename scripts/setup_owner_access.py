#!/usr/bin/env python3
"""
Agentic BioNeMo - Workstation Owner Access Provisioning Utility

Provisions a machine-bound Owner Access credential record stored strictly outside
the repository directory (%LOCALAPPDATA%\\bionemo-nim\\owner_auth.json).

Security Invariants:
- Zero secrets printed to console or written to repository files.
- Bound to the current machine's Windows MachineGuid SHA-256 fingerprint.
- Protected by user-only ACLs (icacls on Windows / chmod 0600 on POSIX).
- Cryptography: hashlib.scrypt (16-byte random salt) + secrets.token_hex(32) signing key.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import secrets
import sys
from pathlib import Path

# Add project root to sys.path so standalone invocation resolves src package
ROOT_DIR = Path(__file__).resolve().parent.parent


def _load_owner_security():
    src_path = str(ROOT_DIR / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from bionemo_benchmark.infra.owner_security import (
        apply_strict_file_acls,
        get_machine_guid_fingerprint,
        get_owner_auth_path,
        hash_password,
    )

    return (
        apply_strict_file_acls,
        get_machine_guid_fingerprint,
        get_owner_auth_path,
        hash_password,
    )


def provision_owner_credentials(
    owner_id: str | None = None,
    password: str | None = None,
    target_path: Path | None = None,
) -> int:
    """Provisions owner credentials, writes file, and sets strict ACLs."""
    (
        apply_strict_file_acls,
        get_machine_guid_fingerprint,
        get_owner_auth_path,
        hash_password,
    ) = _load_owner_security()
    print("=" * 72)
    print(" BioNeMo Cockpit - Machine-Bound Localhost Owner Provisioning")
    print("=" * 72)

    # 1. Hardware Fingerprint Validation
    guid_fingerprint = get_machine_guid_fingerprint()
    if not guid_fingerprint:
        print("\n[ERROR] Unable to retrieve hardware MachineGuid fingerprint on this system.")
        print("Owner Access Mode requires a stable Windows MachineGuid or valid machine identifier.")
        return 1

    print(f"\n[HARDWARE LOCK] MachineGuid SHA-256: {guid_fingerprint[:16]}...{guid_fingerprint[-8:]}")

    # 2. Interactive Credential Gathering (if not passed programmatically)
    if not owner_id:
        try:
            owner_id = input("\nEnter Owner Identifier (e.g. jorwal): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            return 1

    if not owner_id:
        print("[ERROR] Owner Identifier cannot be empty.")
        return 1

    if not password:
        try:
            p1 = getpass.getpass("Enter Owner Password: ")
            if len(p1) < 8:
                print("[ERROR] Password must be at least 8 characters long.")
                return 1
            p2 = getpass.getpass("Confirm Owner Password: ")
            if p1 != p2:
                print("[ERROR] Passwords do not match.")
                return 1
            password = p1
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            return 1

    # 3. Cryptographic derivation (stdlib scrypt + random signing key)
    print("\n[COMPUTING] Deriving scrypt hash (N=16384, r=8, p=1, dklen=64)...")
    salt_hex, hash_hex = hash_password(password)
    signing_key_hex = secrets.token_hex(32)

    # 4. Resolve Target Storage Destination
    out_path = target_path or get_owner_auth_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "owner_id": owner_id,
        "machine_guid_hash": guid_fingerprint,
        "salt_hex": salt_hex,
        "scrypt_hash_hex": hash_hex,
        "signing_key_hex": signing_key_hex,
        "created_at": int(os.environ.get("SOURCE_DATE_EPOCH", "0")) or None,
    }

    # 5. Atomic write and ACL application
    temp_path = out_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    if out_path.exists():
        out_path.unlink()
    temp_path.replace(out_path)

    apply_strict_file_acls(out_path)

    print("\n[SUCCESS] Owner Access Mode configured successfully!")
    print(f"  - Storage Path: {out_path}")
    print(f"  - Owner ID:     {owner_id}")
    print(f"  - Hardware Bind: {guid_fingerprint[:16]}...")
    print("  - Permissions:  Restricted to current user only")
    print("  - Repo Secrets: ZERO (stored entirely outside repository)")
    print("=" * 72)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision machine-bound Owner Access Mode credentials.")
    parser.add_argument("--owner-id", help="Owner Identifier (non-interactive)")
    parser.add_argument("--password", help="Owner Password (non-interactive)")
    parser.add_argument("--path", help="Override output path (for testing)")
    args = parser.parse_args()

    custom_path = Path(args.path).resolve() if args.path else None
    return provision_owner_credentials(
        owner_id=args.owner_id,
        password=args.password,
        target_path=custom_path,
    )


if __name__ == "__main__":
    sys.exit(main())
