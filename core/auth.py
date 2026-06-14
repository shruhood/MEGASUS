"""
MEGASUS Auth System - Role-based access control
Roles: admin (full access), operator (no destructive), viewer (read-only)
"""
import hashlib
import secrets
import time
import json
import os
from datetime import datetime, timedelta

from core.engine import CONFIG

ROLES = {
    "admin": {
        "level": 3,
        "description": "Full access - all modules, all commands, config changes",
        "can_install": True,
        "can_uninstall": True,
        "can_shell": True,
        "can_extract_data": True,
        "can_surveillance": True,
        "can_manage_users": True,
        "can_view_logs": True,
    },
    "operator": {
        "level": 2,
        "description": "Operational access - device control, apps, files, no config",
        "can_install": True,
        "can_uninstall": False,
        "can_shell": True,
        "can_extract_data": True,
        "can_surveillance": False,
        "can_manage_users": False,
        "can_view_logs": False,
    },
    "viewer": {
        "level": 1,
        "description": "Read-only - device info, logs, reports",
        "can_install": False,
        "can_uninstall": False,
        "can_shell": False,
        "can_extract_data": False,
        "can_surveillance": False,
        "can_manage_users": False,
        "can_view_logs": True,
    },
}


class Session:
    """User session with role and expiry"""

    def __init__(self, username, role="viewer"):
        self.username = username
        self.role = role
        self.token = secrets.token_hex(32)
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(
            minutes=CONFIG.get("auth", {}).get("session_timeout_minutes", 30)
        )

    def is_valid(self):
        return datetime.now() < self.expires_at

    def refresh(self):
        self.expires_at = datetime.now() + timedelta(
            minutes=CONFIG.get("auth", {}).get("session_timeout_minutes", 30)
        )

    def has_permission(self, perm):
        perms = ROLES.get(self.role, ROLES["viewer"])
        return perms.get(perm, False)


class AuthManager:
    """Manages user authentication and sessions"""

    def __init__(self):
        self.sessions = {}
        self._load_users()

    def _load_users(self):
        """Load users from config or use defaults"""
        auth_config = CONFIG.get("auth", {})
        self.users = {
            "admin": {
                "password_hash": self._hash(auth_config.get("admin_password", "megasus2026")),
                "role": "admin",
                "created": datetime.now().isoformat(),
            },
            "operator": {
                "password_hash": self._hash(auth_config.get("operator_password", "operator2026")),
                "role": "operator",
                "created": datetime.now().isoformat(),
            },
        }

    def _hash(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        """Authenticate user and return session token"""
        if username not in self.users:
            return None, "User not found"
        if self.users[username]["password_hash"] != self._hash(password):
            return None, "Invalid password"
        role = self.users[username]["role"]
        session = Session(username, role)
        self.sessions[session.token] = session
        return session, "OK"

    def validate_token(self, token):
        """Validate session token"""
        if token not in self.sessions:
            return None, "Invalid session"
        session = self.sessions[token]
        if not session.is_valid():
            del self.sessions[token]
            return None, "Session expired"
        session.refresh()
        return session, "OK"

    def change_password(self, username, new_password, admin_token):
        """Admin can change any password"""
        session, msg = self.validate_token(admin_token)
        if not session:
            return False, msg
        if not session.has_permission("can_manage_users"):
            return False, "Insufficient permissions"
        if username not in self.users:
            # Create new user
            self.users[username] = {
                "password_hash": self._hash(new_password),
                "role": "viewer",
                "created": datetime.now().isoformat(),
            }
        else:
            self.users[username]["password_hash"] = self._hash(new_password)
        return True, f"Password updated for {username}"

    def create_user(self, username, password, role, admin_token):
        """Create a new user (admin only)"""
        session, msg = self.validate_token(admin_token)
        if not session:
            return False, msg
        if not session.has_permission("can_manage_users"):
            return False, "Insufficient permissions"
        if role not in ROLES:
            return False, f"Invalid role. Choose from: {', '.join(ROLES.keys())}"
        self.users[username] = {
            "password_hash": self._hash(password),
            "role": role,
            "created": datetime.now().isoformat(),
        }
        return True, f"User '{username}' created with role '{role}'"

    def list_users(self, admin_token):
        """List all users (admin only)"""
        session, msg = self.validate_token(admin_token)
        if not session:
            return None, msg
        if not session.has_permission("can_manage_users"):
            return None, "Insufficient permissions"
        result = {}
        for uname, udata in self.users.items():
            result[uname] = {"role": udata["role"], "created": udata["created"]}
        return result, "OK"

    def check_permission(self, token, perm):
        """Check if session has specific permission"""
        session, msg = self.validate_token(token)
        if not session:
            return False
        return session.has_permission(perm)
