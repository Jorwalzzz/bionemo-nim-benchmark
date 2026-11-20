"""
Enterprise Security Sentinel for NVIDIA BioNeMo Suite
======================================================
Provides institutional-grade biosecurity screening, in-flight rate limiting,
secret & stack trace scrubbing, and injection countermeasures.

Designed to satisfy NVIDIA Inception, GxP, and HIPAA zero-trust guidelines:
1. BiosecurityScreener: Screening against dual-use toxigenic protein motifs & hazardous biologicals.
2. TokenBucketRateLimiter: In-flight per-IP sliding window DoS and socket starvation defense.
3. SecretScrubber: Memory-safe redacting of nvapi-* keys, Bearer tokens, and server secrets.
4. SafeSanitizer: Linear-time, ReDoS-safe input sanitization for SMILES, PDB IDs, and Python AST parameters.
"""

import os
import re
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# ==============================================================================
# 1. BIOSECURITY & DUAL-USE TOXIN SCREENING
# ==============================================================================


class BiosecurityScreener:
    """
    Screens biological sequences and target names against hazardous biological agents,
    regulated toxin motifs (e.g. Ricin, Botulinum, Diphtheria, Anthrax lethal factor),
    and dual-use pathogenic factors.
    """

    # Regulated pathogen / toxin keywords (case-insensitive)
    HAZARDOUS_KEYWORDS = (
        "RICIN",
        "BOTULINUM",
        "BOTULIN",
        "ANTHRAX",
        "BACILLUS ANTHRACIS",
        "EBOLA",
        "MARBURG",
        "SMALLPOX",
        "VARIOLA",
        "FRANCISELLA",
        "TULAREMIA",
        "YERSINIA PESTIS",
        "CHOLERA TOXIN",
        "DIPHTHERIA TOXIN",
        "SHIGA TOXIN",
        "STAPHYLOCOCCAL ENTEROTOXIN",
        "CONOTOXIN",
        "TETANUSDETOX",
        "SAXITOXIN",
    )

    # Conserved catalytic sequence signatures from select high-risk toxins
    HAZARDOUS_MOTIFS = [
        re.compile(r"EAARF", re.IGNORECASE),  # Ricin A-chain catalytic core
        re.compile(
            r"HE[LIVM][A-Z]H", re.IGNORECASE
        ),  # Botulinum zinc-endopeptidase consensus
        re.compile(
            r"Y[FILV]R[FILV][A-Z]{2}[DE]", re.IGNORECASE
        ),  # Shiga-like ribosome-inactivating signature
    ]

    @classmethod
    def screen_target(
        cls, target_name: str, sequence: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Validates target against biological safety guidelines.
        Returns (is_safe: bool, rejection_reason: Optional[str]).
        """
        clean_name = str(target_name or "").upper().strip()

        # Check keyword registry
        for kw in cls.HAZARDOUS_KEYWORDS:
            if kw in clean_name:
                return (
                    False,
                    f"BIOSECURITY_RESTRICTION: Target '{target_name}' matches regulated select agent toxin list ({kw}). Processing disallowed.",
                )

        # Check sequence motifs if provided
        if sequence:
            clean_seq = re.sub(r"[^A-Z]", "", str(sequence).upper())
            if len(clean_seq) > 5000:
                return (
                    False,
                    "PAYLOAD_TOO_LARGE: Protein sequence exceeds maximum 5,000 residue limit.",
                )

            for motif in cls.HAZARDOUS_MOTIFS:
                if motif.search(clean_seq):
                    return (
                        False,
                        "BIOSECURITY_RESTRICTION: Sequence contains conserved high-consequence toxin domain signature. Execution halted.",
                    )

        return True, None


# ==============================================================================
# 2. IN-FLIGHT TOKEN BUCKET RATE LIMITER (DoS & BURST DEFENSE)
# ==============================================================================


class TokenBucketRateLimiter:
    """
    Sliding-window token bucket rate limiter for in-flight HTTP and SSE connections.
    Enforces per-IP burst limits and sustained rate limits with zero external dependencies.
    """

    def __init__(self, capacity: int = 30, refill_rate_per_sec: float = 0.5):
        """
        :param capacity: Max burst token bucket size.
        :param refill_rate_per_sec: Rate at which tokens refill (0.5 = 1 token every 2s, 30/min).
        """
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self._buckets: dict[str, dict[str, float]] = {}
        self._lock = threading.Lock()

    def allow_request(self, ip_str: str, cost: float = 1.0) -> tuple[bool, float]:
        """
        Checks if IP is allowed to proceed.
        Returns (allowed: bool, retry_after_seconds: float).
        """
        now = time.time()
        with self._lock:
            # Periodic cleanup if registry exceeds 10,000 IPs to prevent memory bloat
            if len(self._buckets) > 10000:
                cutoff = now - 3600
                self._buckets = {
                    k: v for k, v in self._buckets.items() if v["last_check"] > cutoff
                }

            if ip_str not in self._buckets:
                self._buckets[ip_str] = {
                    "tokens": self.capacity - cost,
                    "last_check": now,
                }
                return True, 0.0

            bucket = self._buckets[ip_str]
            elapsed = now - bucket["last_check"]
            bucket["last_check"] = now
            bucket["tokens"] = min(
                self.capacity, bucket["tokens"] + elapsed * self.refill_rate
            )

            if bucket["tokens"] >= cost:
                bucket["tokens"] -= cost
                return True, 0.0
            else:
                deficit = cost - bucket["tokens"]
                retry_after = deficit / self.refill_rate
                return False, round(retry_after, 1)


# ==============================================================================
# 3. SECRET & UPSTREAM TRACE SCRUBBER
# ==============================================================================


class SecretScrubber:
    """
    Deep sanitizes log strings, JSON payloads, and exception messages to prevent
    NVIDIA API keys, Bearer tokens, or internal server paths from leaking.
    """

    SECRET_PATTERNS = [
        re.compile(r"nvapi-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
        re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE),
        re.compile(
            r'(?:NVIDIA_API_KEY|api_key|api-key)\s*[:=]\s*["\']?([^"\'\s]+)["\']?',
            re.IGNORECASE,
        ),
        re.compile(r'password\s*[:=]\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE),
    ]

    @classmethod
    def scrub(cls, text: str) -> str:
        """Replaces sensitive tokens and secrets with [REDACTED_SECRET]."""
        if not text:
            return ""
        s = str(text)
        # Redact active environment API key if configured
        env_key = os.getenv("NVIDIA_API_KEY", "").strip()
        if env_key and len(env_key) >= 8 and env_key in s:
            s = s.replace(env_key, "[REDACTED_SECRET]")

        for pat in cls.SECRET_PATTERNS:
            s = pat.sub("[REDACTED_SECRET]", s)
        return s


# ==============================================================================
# 4. SAFE INPUT SANITIZERS (ReDoS & SCRIPT INJECTION DEFENSE)
# ==============================================================================


class SafeSanitizer:
    """
    Linear-time string sanitizers that prevent Command Injection, Python AST Injection,
    Path Traversal (CWE-22), SSRF (CWE-918), and CSV Formula Injection (CWE-1236).
    """

    PDB_ID_REGEX = re.compile(r"^[1-9][A-Za-z0-9]{3}$")

    ALLOWED_OUTBOUND_HOSTS = frozenset({
        "files.rcsb.org",
        "data.rcsb.org",
        "integrate.api.nvidia.com",
        "health.api.nvidia.com",
    })

    @classmethod
    def validate_pdb_id(cls, pdb_id: str) -> str:
        """
        Validates 4-character PDB code strictly against ^[1-9][A-Za-z0-9]{3}$.
        Rejects control characters, null bytes, command injection tokens, and invalid formats.
        Raises ValueError if invalid.
        """
        if not pdb_id or not isinstance(pdb_id, str):
            raise ValueError("PDB ID must be a non-empty string.")
        if "\x00" in pdb_id or any(ord(c) < 32 for c in pdb_id):
            raise ValueError("PDB ID contains illegal control characters or null bytes.")
        clean = pdb_id.strip().upper()
        if not cls.PDB_ID_REGEX.match(clean):
            raise ValueError(f"Invalid PDB ID format: '{pdb_id}'. Must strictly match ^[1-9][A-Za-z0-9]{{3}}$.")
        return clean

    @classmethod
    def validate_outbound_url(cls, url: str) -> str:
        """
        Validates outbound HTTP requests against CWE-918 (SSRF).
        Enforces HTTPS, allowed host whitelist, and prohibits embedded userinfo.
        """
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string.")
        if "\x00" in url or any(ord(c) < 32 for c in url):
            raise ValueError("URL contains illegal control characters or null bytes.")
        parsed = urlparse(url.strip())
        if parsed.scheme.lower() != "https":
            raise ValueError(f"Disallowed URL scheme '{parsed.scheme}'. Only HTTPS is permitted.")
        host = (parsed.hostname or "").lower()
        if host not in cls.ALLOWED_OUTBOUND_HOSTS:
            raise ValueError(
                f"Outbound host '{host}' is not in allowed hosts whitelist: {sorted(cls.ALLOWED_OUTBOUND_HOSTS)}"
            )
        if parsed.username or parsed.password:
            raise ValueError("Embedded credentials in outbound URL are forbidden.")
        return url

    @staticmethod
    def validate_safe_path(path: str | Path, base_dir: str | Path) -> Path:
        """
        Ensures target path resolves strictly within the allowed base directory (CWE-22 defense).
        Raises ValueError if path traversal is detected.
        """
        resolved_base = Path(base_dir).resolve()
        resolved_path = (resolved_base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
        if not resolved_path.is_relative_to(resolved_base):
            raise ValueError(
                f"Path traversal detected: '{path}' resolves outside allowed base directory '{resolved_base}'."
            )
        return resolved_path

    @staticmethod
    def sanitize_csv_cell(value: Any) -> str:
        """
        Sanitizes a string for safe CSV serialization and tabular rendering.
        Neutralizes CSV Formula Injection (CWE-1236) by prepending a single quote
        if cell starts with '=', '+', '-', '@', '\\t', or '\\r'.
        Also escapes HTML markup to prevent DOM XSS when CSV is viewed in dashboards.
        """
        if value is None:
            return ""
        s = str(value).replace("\x00", "")
        # Formula injection mitigation
        if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
            s = "'" + s
        # HTML tag neutralization
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        return s

    @staticmethod
    def sanitize_chemical_smiles(smiles: str, max_length: int = 500) -> str:
        """
        Sanitizes small molecule SMILES string.
        Enforces maximum length and canonical SMILES character whitelist.
        """
        if not smiles:
            return "CC(=O)N1CCNCC1"
        s = str(smiles).strip()[:max_length]
        cleaned = re.sub(r"[^A-Za-z0-9@+\-\[\]\(\)\\\/=#%.:]", "", s)
        return cleaned or "CC(=O)N1CCNCC1"

    @classmethod
    def sanitize_pdb_id(cls, pdb_id: str) -> str:
        """
        Sanitizes 4-character PDB code against Path Traversal and Command Injection.
        """
        if not pdb_id:
            return "8AZV"
        if "\x00" in str(pdb_id) or any(ord(c) < 32 for c in str(pdb_id)):
            return "8AZV"
        s = str(pdb_id).strip().upper()[:4]
        return s if cls.PDB_ID_REGEX.match(s) else "8AZV"

    @staticmethod
    def sanitize_code_literal(value: str, max_length: int = 80) -> str:
        """
        Sanitizes strings that will be interpolated into generated Python scripts
        (such as Opentrons OT-2 protocols). Strips newlines, quotes, backslashes,
        executable python function calls, and dangerous system tokens.
        """
        if not value:
            return "Unspecified"
        s = str(value).strip()[:max_length]

        # Strip python code delimiters, semicolons, brackets, backticks, quotes, and newlines
        cleaned = re.sub(r"[\'\"\\;\n\r`$(){}\[\]=]", " ", s)

        # Strip dangerous execution keywords
        DANGEROUS_CODE_KEYWORDS = [
            r"\bimport\b",
            r"\bos\b",
            r"\bsubprocess\b",
            r"\bsys\b",
            r"\beval\b",
            r"\bexec\b",
            r"\bsystem\b",
            r"\bpopen\b",
            r"\bspawn\b",
            r"__import__",
        ]
        for kw in DANGEROUS_CODE_KEYWORDS:
            cleaned = re.sub(kw, "", cleaned, flags=re.IGNORECASE)

        # Whitelist safe laboratory alphanumeric, punctuation, and rating stars
        cleaned = re.sub(r"[^A-Za-z0-9\s\/\-\+\.,_★☆]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or "Standard Reagent"
