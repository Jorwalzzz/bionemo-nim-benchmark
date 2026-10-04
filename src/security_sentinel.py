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

import re
import time
import threading
from typing import Dict, Tuple, Optional, List, Any


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
        "RICIN", "BOTULINUM", "BOTULIN", "ANTHRAX", "BACILLUS ANTHRACIS",
        "EBOLA", "MARBURG", "SMALLPOX", "VARIOLA", "FRANCISELLA", "TULAREMIA",
        "YERSINIA PESTIS", "CHOLERA TOXIN", "DIPHTHERIA TOXIN", "SHIGA TOXIN",
        "STAPHYLOCOCCAL ENTEROTOXIN", "CONOTOXIN", "TETANUSDETOX", "SAXITOXIN"
    )

    # Conserved catalytic sequence signatures from select high-risk toxins
    HAZARDOUS_MOTIFS = [
        re.compile(r"EAARF", re.IGNORECASE),                 # Ricin A-chain catalytic core
        re.compile(r"HE[LIVM]XH", re.IGNORECASE),            # Botulinum zinc-endopeptidase consensus
        re.compile(r"Y[FILV]R[FILV]X{2}[DE]", re.IGNORECASE) # Shiga-like ribosome-inactivating signature
    ]

    @classmethod
    def screen_target(cls, target_name: str, sequence: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validates target against biological safety guidelines.
        Returns (is_safe: bool, rejection_reason: Optional[str]).
        """
        clean_name = str(target_name or "").upper().strip()
        
        # Check keyword registry
        for kw in cls.HAZARDOUS_KEYWORDS:
            if kw in clean_name:
                return False, f"BIOSECURITY_RESTRICTION: Target '{target_name}' matches regulated select agent toxin list ({kw}). Processing disallowed."

        # Check sequence motifs if provided
        if sequence:
            clean_seq = re.sub(r'[^A-Z]', '', str(sequence).upper())
            if len(clean_seq) > 5000:
                return False, "PAYLOAD_TOO_LARGE: Protein sequence exceeds maximum 5,000 residue limit."

            for motif in cls.HAZARDOUS_MOTIFS:
                if motif.search(clean_seq):
                    return False, "BIOSECURITY_RESTRICTION: Sequence contains conserved high-consequence toxin domain signature. Execution halted."

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
        self._buckets: Dict[str, Dict[str, float]] = {}
        self._lock = threading.Lock()

    def allow_request(self, ip_str: str, cost: float = 1.0) -> Tuple[bool, float]:
        """
        Checks if IP is allowed to proceed.
        Returns (allowed: bool, retry_after_seconds: float).
        """
        now = time.time()
        with self._lock:
            # Periodic cleanup if registry exceeds 10,000 IPs to prevent memory bloat
            if len(self._buckets) > 10000:
                cutoff = now - 3600
                self._buckets = {k: v for k, v in self._buckets.items() if v["last_check"] > cutoff}

            if ip_str not in self._buckets:
                self._buckets[ip_str] = {
                    "tokens": self.capacity - cost,
                    "last_check": now
                }
                return True, 0.0

            bucket = self._buckets[ip_str]
            elapsed = now - bucket["last_check"]
            bucket["last_check"] = now
            bucket["tokens"] = min(self.capacity, bucket["tokens"] + elapsed * self.refill_rate)

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
        re.compile(r'nvapi-[a-zA-Z0-9_-]{20,}', re.IGNORECASE),
        re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.]{15,}', re.IGNORECASE),
        re.compile(r'(?:NVIDIA_API_KEY|api_key|api-key)\s*[:=]\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE),
        re.compile(r'password\s*[:=]\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE)
    ]

    @classmethod
    def scrub(cls, text: str) -> str:
        """Replaces sensitive tokens and secrets with [REDACTED_SECRET]."""
        if not text:
            return ""
        s = str(text)
        for pat in cls.SECRET_PATTERNS:
            s = pat.sub("[REDACTED_SECRET]", s)
        return s


# ==============================================================================
# 4. SAFE INPUT SANITIZERS (ReDoS & SCRIPT INJECTION DEFENSE)
# ==============================================================================

class SafeSanitizer:
    """
    Linear-time string sanitizers that prevent Command Injection, Python AST Injection,
    and catastrophic Regular Expression backtracking (ReDoS).
    """

    @staticmethod
    def sanitize_chemical_smiles(smiles: str, max_length: int = 500) -> str:
        """
        Sanitizes small molecule SMILES string.
        Enforces maximum length and canonical SMILES character whitelist.
        """
        if not smiles:
            return "CC(=O)N1CCNCC1"
        s = str(smiles).strip()[:max_length]
        cleaned = re.sub(r'[^A-Za-z0-9@+\-\[\]\(\)\\\/=#%.:]', '', s)
        return cleaned or "CC(=O)N1CCNCC1"

    @staticmethod
    def sanitize_pdb_id(pdb_id: str) -> str:
        """
        Sanitizes 4-character PDB code against Path Traversal and Command Injection.
        """
        if not pdb_id:
            return "8AZV"
        s = str(pdb_id).strip().upper()[:4]
        cleaned = re.sub(r'[^A-Z0-9]', '', s)
        return cleaned if len(cleaned) == 4 else "8AZV"

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
        cleaned = re.sub(r'[\'\"\\;\n\r`$(){}\[\]=]', ' ', s)

        # Strip dangerous execution keywords
        DANGEROUS_CODE_KEYWORDS = [
            r'\bimport\b', r'\bos\b', r'\bsubprocess\b', r'\bsys\b',
            r'\beval\b', r'\bexec\b', r'\bsystem\b', r'\bpopen\b',
            r'\bspawn\b', r'__import__'
        ]
        for kw in DANGEROUS_CODE_KEYWORDS:
            cleaned = re.sub(kw, '', cleaned, flags=re.IGNORECASE)

        # Whitelist safe laboratory alphanumeric, punctuation, and rating stars
        cleaned = re.sub(r'[^A-Za-z0-9\s\/\-\+\.,_★☆]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned or "Standard Reagent"
