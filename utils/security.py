"""
Security utilities: IP-based brute-force tracking, lockout, persistent ban list,
and security audit logging.
"""

import os
import json
import time
import threading
import logging
import re
from logging.handlers import RotatingFileHandler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BLOCKED_IPS_PATH = os.path.join(_BASE_DIR, "config", "blocked_ips.json")
_LOG_DIR = os.path.join(_BASE_DIR, "logs")

# ---------------------------------------------------------------------------
# Security audit logger (writes to logs/security.log)
# ---------------------------------------------------------------------------
os.makedirs(_LOG_DIR, exist_ok=True)

security_logger = logging.getLogger("security_audit")
if not security_logger.handlers:
    _handler = RotatingFileHandler(
        os.path.join(_LOG_DIR, "security.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    _handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    security_logger.addHandler(_handler)
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False

# ---------------------------------------------------------------------------
# In-memory brute-force tracker (thread-safe)
# ---------------------------------------------------------------------------
_lock = threading.Lock()

# {ip: {"count": int, "window_start": float, "lockout_until": float, "lockout_level": int}}
_attempt_tracker: dict = {}

# Configuration
WINDOW_SECONDS = 60          # sliding window length
MAX_FAILURES = 5             # failures before first lockout
LOCKOUT_DURATIONS = [60, 300, 1800, 3600]  # escalating lockout durations in seconds


def _lockout_duration(level: int) -> int:
    """Return lockout seconds for a given escalation level (0-based)."""
    idx = min(level, len(LOCKOUT_DURATIONS) - 1)
    return LOCKOUT_DURATIONS[idx]


def record_failed_login(ip: str, username: str) -> dict:
    """
    Record a failed login attempt for *ip*.
    Returns a dict with keys:
      - locked_out: bool
      - lockout_seconds: int (0 if not locked out)
      - attempts: int
    """
    now = time.time()
    with _lock:
        entry = _attempt_tracker.get(ip)
        if entry is None:
            entry = {
                "count": 0,
                "window_start": now,
                "lockout_until": 0.0,
                "lockout_level": 0,
            }
            _attempt_tracker[ip] = entry

        # Reset window if it has expired and no active lockout
        if now > entry["lockout_until"] and (now - entry["window_start"]) > WINDOW_SECONDS:
            entry["count"] = 0
            entry["window_start"] = now

        entry["count"] += 1
        count = entry["count"]

        locked_out = False
        lockout_seconds = 0

        if count >= MAX_FAILURES:
            level = entry["lockout_level"]
            duration = _lockout_duration(level)
            entry["lockout_until"] = now + duration
            entry["lockout_level"] = level + 1
            entry["count"] = 0
            entry["window_start"] = now
            locked_out = True
            lockout_seconds = duration
            security_logger.warning(
                "IP_LOCKOUT ip=%s username=%r attempts=%d lockout_seconds=%d level=%d",
                ip, username, count, duration, level,
            )
        else:
            security_logger.warning(
                "LOGIN_FAILED ip=%s username=%r attempt=%d/%d",
                ip, username, count, MAX_FAILURES,
            )

        return {"locked_out": locked_out, "lockout_seconds": lockout_seconds, "attempts": count}


def is_ip_locked_out(ip: str) -> tuple[bool, int]:
    """
    Check whether *ip* is currently under a temporary lockout.
    Returns (is_locked, seconds_remaining).
    """
    now = time.time()
    with _lock:
        entry = _attempt_tracker.get(ip)
        if entry is None:
            return False, 0
        remaining = entry["lockout_until"] - now
        if remaining > 0:
            return True, int(remaining)
        return False, 0


def record_successful_login(ip: str, username: str) -> None:
    """Clear failed-login counters for *ip* and log success."""
    with _lock:
        _attempt_tracker.pop(ip, None)
    security_logger.info("LOGIN_SUCCESS ip=%s username=%r", ip, username)


def record_logout(ip: str, username: str) -> None:
    security_logger.info("LOGOUT ip=%s username=%r", ip, username)


def record_unauthorized_admin_access(ip: str, username: str, path: str) -> None:
    security_logger.warning(
        "UNAUTHORIZED_ADMIN_ACCESS ip=%s username=%r path=%r", ip, username, path
    )


# ---------------------------------------------------------------------------
# Persistent ban list
# ---------------------------------------------------------------------------

def _load_blocked_ips() -> list:
    try:
        if os.path.exists(_BLOCKED_IPS_PATH):
            with open(_BLOCKED_IPS_PATH, "r", encoding="utf-8") as f:
                return json.load(f) or []
    except Exception:
        security_logger.exception("Failed to load blocked_ips.json")
    return []


def _save_blocked_ips(entries: list) -> bool:
    try:
        os.makedirs(os.path.dirname(_BLOCKED_IPS_PATH), exist_ok=True)
        tmp = _BLOCKED_IPS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        os.replace(tmp, _BLOCKED_IPS_PATH)
        return True
    except Exception:
        security_logger.exception("Failed to save blocked_ips.json")
        return False


def _is_valid_ip(ip: str) -> bool:
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def get_blocked_ips() -> list:
    """Return list of persistent ban records."""
    return _load_blocked_ips()


def is_ip_permanently_banned(ip: str) -> bool:
    """Return True if *ip* is in the persistent ban list."""
    entries = _load_blocked_ips()
    return any(e.get("ip") == ip for e in entries)


def ban_ip(ip: str, reason: str, banned_by: str) -> tuple[bool, str]:
    """
    Add *ip* to the persistent ban list.
    Returns (success, error_message).
    """
    if not _is_valid_ip(ip):
        return False, "Invalid IP address format"
    entries = _load_blocked_ips()
    if any(e.get("ip") == ip for e in entries):
        return False, "IP already banned"
    entries.append({
        "ip": ip,
        "reason": reason,
        "banned_by": banned_by,
        "banned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    ok = _save_blocked_ips(entries)
    if ok:
        security_logger.warning("IP_BANNED ip=%s reason=%r by=%r", ip, reason, banned_by)
    return ok, "" if ok else "Failed to save ban list"


def unban_ip(ip: str, unbanned_by: str) -> tuple[bool, str]:
    """
    Remove *ip* from the persistent ban list.
    Returns (success, error_message).
    """
    entries = _load_blocked_ips()
    new_entries = [e for e in entries if e.get("ip") != ip]
    if len(new_entries) == len(entries):
        return False, "IP not found in ban list"
    ok = _save_blocked_ips(new_entries)
    if ok:
        security_logger.info("IP_UNBANNED ip=%s by=%r", ip, unbanned_by)
    return ok, "" if ok else "Failed to save ban list"


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------
_USERNAME_RE = re.compile(r'^[a-zA-Z0-9_\-]+$')


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate a username.
    Returns (valid, error_message).
    """
    if not username:
        return False, "Nom d'utilisateur requis."
    if len(username) < 3:
        return False, "Le nom d'utilisateur doit contenir au moins 3 caractères."
    if len(username) > 64:
        return False, "Le nom d'utilisateur ne peut pas dépasser 64 caractères."
    if not _USERNAME_RE.match(username):
        return False, "Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores."
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate a password for strength.
    Returns (valid, error_message).
    """
    if not password:
        return False, "Mot de passe requis."
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if not re.search(r'[0-9]', password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    if not re.search(r'[^a-zA-Z0-9]', password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial."
    return True, ""


# ---------------------------------------------------------------------------
# Security log tail helper
# ---------------------------------------------------------------------------

def get_security_log_tail(lines: int = 100) -> list[str]:
    """Return the last *lines* lines from the security audit log."""
    log_path = os.path.join(_LOG_DIR, "security.log")
    try:
        if not os.path.exists(log_path):
            return []
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return [l.rstrip("\n") for l in all_lines[-lines:]]
    except Exception:
        security_logger.exception("Failed to read security log")
        return []
