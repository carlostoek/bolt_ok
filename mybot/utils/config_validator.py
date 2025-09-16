"""
Configuration validation and security utilities for the narrative system.
Task 33: Update system configuration for new features.

This module provides:
- Configuration validation
- Security configuration checks
- Content validation rules
- Admin access control configuration
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional
from utils.config import Config
from utils.database_config import validate_all_configs
from utils.performance_config import validate_performance_config

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Comprehensive configuration validator for the narrative system."""

    @staticmethod
    def validate_all() -> Dict[str, Any]:
        """Validate all system configurations."""
        results = {
            "basic": ConfigValidator.validate_basic_config(),
            "database": validate_all_configs()["database"],
            "cache": validate_all_configs()["cache"],
            "security": ConfigValidator.validate_security_config(),
            "performance": validate_performance_config(),
            "narrative": ConfigValidator.validate_narrative_config(),
        }

        # Overall validation status
        results["overall_valid"] = all(
            result.get("overall_valid", True) for result in results.values()
            if isinstance(result, dict)
        )

        return results

    @staticmethod
    def validate_basic_config() -> Dict[str, Any]:
        """Validate basic bot configuration."""
        validation_results = {}

        try:
            # Check bot token exists and has correct format
            bot_token = Config.BOT_TOKEN
            validation_results["bot_token_exists"] = bool(bot_token and bot_token != "YOUR_BOT_TOKEN")
            validation_results["bot_token_format"] = bool(re.match(r'^\d+:[A-Za-z0-9_-]+$', bot_token)) if bot_token else False

            # Check admin IDs are configured
            admin_id = Config.ADMIN_ID
            validation_results["admin_id_configured"] = admin_id > 0

            # Check database URL is valid
            db_url = Config.DATABASE_URL
            validation_results["database_url_valid"] = bool(db_url and ("sqlite" in db_url or "postgresql" in db_url))

            # Check Gemini API key if AI integration is enabled
            if Config.AI_INTEGRATION_ENABLED:
                gemini_key = Config.GEMINI_API_KEY
                validation_results["gemini_api_key_exists"] = bool(gemini_key)
            else:
                validation_results["gemini_api_key_exists"] = True

            validation_results["overall_valid"] = all([
                validation_results["bot_token_exists"],
                validation_results["bot_token_format"],
                validation_results["admin_id_configured"],
                validation_results["database_url_valid"],
                validation_results["gemini_api_key_exists"],
            ])

        except Exception as e:
            validation_results["error"] = str(e)
            validation_results["overall_valid"] = False

        return validation_results

    @staticmethod
    def validate_security_config() -> Dict[str, Any]:
        """Validate security configuration."""
        validation_results = {}

        try:
            # Check content validation settings
            validation_results["content_validation_enabled"] = Config.CONTENT_VALIDATION_ENABLED
            validation_results["max_content_length_valid"] = 100 <= Config.MAX_CONTENT_LENGTH <= 50000

            # Check file upload security
            max_file_size = Config.MAX_FILE_SIZE_MB
            validation_results["file_size_valid"] = 1 <= max_file_size <= 100

            allowed_types = Config.ALLOWED_FILE_TYPES
            safe_types = {"jpg", "jpeg", "png", "gif", "mp4", "mp3", "txt", "pdf", "webp", "svg"}
            validation_results["file_types_safe"] = all(ft.lower() in safe_types for ft in allowed_types)

            # Check admin session timeout
            session_timeout = Config.ADMIN_SESSION_TIMEOUT
            validation_results["session_timeout_valid"] = 300 <= session_timeout <= 28800  # 5 min to 8 hours

            # Check rate limiting
            admin_rate = Config.RATE_LIMIT_ADMIN_OPERATIONS
            validation_results["admin_rate_limit_valid"] = 10 <= admin_rate <= 1000

            user_rate = Config.RATE_LIMIT_USER_INTERACTIONS
            validation_results["user_rate_limit_valid"] = 100 <= user_rate <= 10000

            # Check AI rate limiting
            ai_rate = Config.AI_RATE_LIMIT_PER_MINUTE
            validation_results["ai_rate_limit_valid"] = 1 <= ai_rate <= 300

            validation_results["overall_valid"] = all([
                validation_results["max_content_length_valid"],
                validation_results["file_size_valid"],
                validation_results["file_types_safe"],
                validation_results["session_timeout_valid"],
                validation_results["admin_rate_limit_valid"],
                validation_results["user_rate_limit_valid"],
                validation_results["ai_rate_limit_valid"],
            ])

        except Exception as e:
            validation_results["error"] = str(e)
            validation_results["overall_valid"] = False

        return validation_results

    @staticmethod
    def validate_narrative_config() -> Dict[str, Any]:
        """Validate narrative system specific configuration."""
        validation_results = {}

        try:
            # Check feature flags
            validation_results["analytics_enabled"] = Config.ANALYTICS_REAL_TIME_ENABLED
            validation_results["lore_auto_unlock"] = Config.LORE_AUTO_UNLOCK_ENABLED
            validation_results["coordinator_enabled"] = Config.COORDINATOR_ENABLED

            # Check narrative cache settings
            cache_ttl = Config.NARRATIVE_CACHE_TTL
            validation_results["cache_ttl_valid"] = 300 <= cache_ttl <= 86400  # 5 min to 1 day

            fragment_cache = Config.FRAGMENT_CACHE_SIZE
            validation_results["fragment_cache_valid"] = 100 <= fragment_cache <= 10000

            # Check lore settings
            lore_cache = Config.LORE_CACHE_DURATION
            validation_results["lore_cache_valid"] = 300 <= lore_cache <= 7200  # 5 min to 2 hours

            # Check progress settings
            auto_save = Config.PROGRESS_AUTO_SAVE_INTERVAL
            validation_results["auto_save_valid"] = 30 <= auto_save <= 600  # 30 sec to 10 min

            choice_timeout = Config.CHOICE_TIMEOUT_MINUTES
            validation_results["choice_timeout_valid"] = 5 <= choice_timeout <= 120  # 5 min to 2 hours

            # Check coordinator settings
            if Config.COORDINATOR_ENABLED:
                coord_sync = Config.COORDINATOR_SYNC_INTERVAL
                validation_results["coordinator_sync_valid"] = 30 <= coord_sync <= 300  # 30 sec to 5 min
            else:
                validation_results["coordinator_sync_valid"] = True

            validation_results["overall_valid"] = all([
                validation_results["cache_ttl_valid"],
                validation_results["fragment_cache_valid"],
                validation_results["lore_cache_valid"],
                validation_results["auto_save_valid"],
                validation_results["choice_timeout_valid"],
                validation_results["coordinator_sync_valid"],
            ])

        except Exception as e:
            validation_results["error"] = str(e)
            validation_results["overall_valid"] = False

        return validation_results


class ContentValidator:
    """Content validation utilities for the narrative system."""

    @staticmethod
    def validate_content_length(content: str) -> bool:
        """Validate content length against configured limits."""
        if not Config.CONTENT_VALIDATION_ENABLED:
            return True
        return len(content) <= Config.MAX_CONTENT_LENGTH

    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """Validate file type against allowed types."""
        if not filename:
            return False

        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        return extension in [ft.lower() for ft in Config.ALLOWED_FILE_TYPES]

    @staticmethod
    def validate_file_size(file_size_bytes: int) -> bool:
        """Validate file size against configured limits."""
        max_size_bytes = Config.MAX_FILE_SIZE_MB * 1024 * 1024
        return file_size_bytes <= max_size_bytes

    @staticmethod
    def sanitize_content(content: str) -> str:
        """Sanitize content for safe storage and display."""
        if not Config.CONTENT_VALIDATION_ENABLED:
            return content

        # Remove potentially dangerous HTML/script tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<iframe[^>]*>.*?</iframe>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<object[^>]*>.*?</object>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<embed[^>]*>.*?</embed>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Limit content length
        if len(content) > Config.MAX_CONTENT_LENGTH:
            content = content[:Config.MAX_CONTENT_LENGTH] + "..."

        return content.strip()

    @staticmethod
    def validate_narrative_key(key: str) -> bool:
        """Validate narrative key format."""
        # Keys should be alphanumeric with underscores and hyphens
        pattern = r'^[a-zA-Z0-9_-]{1,50}$'
        return bool(re.match(pattern, key))

    @staticmethod
    def validate_lore_code(code: str) -> bool:
        """Validate lore piece code format."""
        # Lore codes should follow a specific pattern
        pattern = r'^[A-Z0-9_]{3,20}$'
        return bool(re.match(pattern, code))


class SecurityAudit:
    """Security audit utilities for the narrative system."""

    @staticmethod
    def audit_configuration() -> Dict[str, Any]:
        """Perform a comprehensive security audit of the configuration."""
        audit_results = {
            "timestamp": "2025-09-16",
            "checks": {},
            "warnings": [],
            "errors": [],
        }

        try:
            # Check environment variables security
            audit_results["checks"]["env_vars_secure"] = SecurityAudit._check_env_vars()

            # Check file permissions
            audit_results["checks"]["file_permissions_ok"] = SecurityAudit._check_file_permissions()

            # Check content validation
            audit_results["checks"]["content_validation_enabled"] = Config.CONTENT_VALIDATION_ENABLED

            # Check rate limiting
            audit_results["checks"]["rate_limiting_enabled"] = (
                Config.RATE_LIMIT_ADMIN_OPERATIONS > 0 and
                Config.RATE_LIMIT_USER_INTERACTIONS > 0
            )

            # Check admin session security
            audit_results["checks"]["admin_session_secure"] = Config.ADMIN_SESSION_TIMEOUT <= 3600

            # Check file upload security
            audit_results["checks"]["file_upload_secure"] = (
                Config.MAX_FILE_SIZE_MB <= 50 and
                len(Config.ALLOWED_FILE_TYPES) <= 10
            )

            # Collect warnings and errors
            SecurityAudit._collect_security_issues(audit_results)

        except Exception as e:
            audit_results["errors"].append(f"Security audit failed: {str(e)}")

        return audit_results

    @staticmethod
    def _check_env_vars() -> bool:
        """Check if sensitive environment variables are properly configured."""
        sensitive_vars = ["BOT_TOKEN", "GEMINI_API_KEY", "DATABASE_URL"]
        for var in sensitive_vars:
            value = os.environ.get(var, "")
            if not value or value in ["YOUR_BOT_TOKEN", "your_api_key", "default"]:
                return False
        return True

    @staticmethod
    def _check_file_permissions() -> bool:
        """Check if configuration files have appropriate permissions."""
        config_files = [".env", "utils/config.py"]
        for file_path in config_files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                # Check if file is readable by others (potential security risk)
                if stat.st_mode & 0o044:  # Others can read
                    return False
        return True

    @staticmethod
    def _collect_security_issues(audit_results: Dict[str, Any]):
        """Collect security warnings and errors from audit results."""
        checks = audit_results["checks"]

        if not checks.get("env_vars_secure", True):
            audit_results["errors"].append("Sensitive environment variables not properly configured")

        if not checks.get("content_validation_enabled", True):
            audit_results["warnings"].append("Content validation is disabled")

        if not checks.get("rate_limiting_enabled", True):
            audit_results["warnings"].append("Rate limiting is not properly configured")

        if not checks.get("admin_session_secure", True):
            audit_results["warnings"].append("Admin session timeout is too long")

        if Config.MAX_FILE_SIZE_MB > 50:
            audit_results["warnings"].append(f"File size limit is high: {Config.MAX_FILE_SIZE_MB}MB")


def run_full_configuration_check() -> Dict[str, Any]:
    """Run a complete configuration validation and security audit."""
    return {
        "validation": ConfigValidator.validate_all(),
        "security_audit": SecurityAudit.audit_configuration(),
        "timestamp": "2025-09-16",
    }