"""
Configuration initialization script for the narrative system.
Task 33: Update system configuration for new features.

This script initializes default configuration values in the database
and validates the system configuration for the narrative features.
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import get_session_factory
from services.config_service import ConfigService
from utils.config_validator import run_full_configuration_check
from utils.database_config import validate_all_configs

logger = logging.getLogger(__name__)


class ConfigInitializer:
    """Initialize configuration values for the narrative system."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.config_service = ConfigService(session)

    async def initialize_narrative_config(self) -> dict:
        """Initialize default narrative system configuration in the database."""
        results = {"initialized": [], "skipped": [], "errors": []}

        default_configs = [
            # Feature toggles
            ("narrative_analytics_enabled", "true", "Enable narrative analytics"),
            ("lore_auto_unlock_enabled", "true", "Enable automatic lore unlocking"),
            ("content_validation_enabled", "true", "Enable content validation"),
            ("performance_monitoring_enabled", "true", "Enable performance monitoring"),
            ("ai_integration_enabled", "true", "Enable AI integration"),
            ("coordinator_enabled", "true", "Enable CoordinadorCentral"),

            # Performance settings
            ("cache_ttl_seconds", "3600", "Cache TTL in seconds"),
            ("analytics_batch_size", "100", "Analytics batch processing size"),
            ("db_pool_size", "15", "Database connection pool size"),
            ("rate_limit_admin_operations", "100", "Admin operations rate limit per hour"),
            ("rate_limit_user_interactions", "1000", "User interactions rate limit per hour"),

            # Security settings
            ("admin_session_timeout_minutes", "30", "Admin session timeout in minutes"),
            ("max_content_length", "5000", "Maximum content length"),
            ("max_file_size_mb", "10", "Maximum file size in MB"),
            ("allowed_file_types", "jpg,jpeg,png,gif,mp4,mp3,txt,pdf", "Allowed file types"),
        ]

        for key, default_value, description in default_configs:
            try:
                existing_value = await self.config_service.get_value(key)
                if existing_value is None:
                    await self.config_service.set_value(key, default_value)
                    results["initialized"].append(f"{key} = {default_value} ({description})")
                    logger.info(f"Initialized config: {key} = {default_value}")
                else:
                    results["skipped"].append(f"{key} = {existing_value} (already set)")
            except Exception as e:
                error_msg = f"Failed to initialize {key}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

        return results

    async def validate_existing_config(self) -> dict:
        """Validate existing configuration values in the database."""
        validation_results = await self.config_service.validate_narrative_config()

        if not validation_results.get("overall_valid", False):
            logger.warning("Configuration validation failed. Some settings may need adjustment.")
        else:
            logger.info("Configuration validation passed.")

        return validation_results

    async def get_config_summary(self) -> dict:
        """Get a summary of all narrative configuration."""
        return await self.config_service.get_narrative_config_summary()

    async def reset_to_defaults(self) -> dict:
        """Reset all narrative configuration to default values."""
        results = {"reset": [], "errors": []}

        default_configs = [
            # Feature toggles - reset to enabled by default
            ("narrative_analytics_enabled", "true"),
            ("lore_auto_unlock_enabled", "true"),
            ("content_validation_enabled", "true"),
            ("performance_monitoring_enabled", "true"),
            ("ai_integration_enabled", "true"),
            ("coordinator_enabled", "true"),

            # Performance settings - conservative defaults
            ("cache_ttl_seconds", "3600"),
            ("analytics_batch_size", "100"),
            ("db_pool_size", "15"),
            ("rate_limit_admin_operations", "100"),
            ("rate_limit_user_interactions", "1000"),

            # Security settings - secure defaults
            ("admin_session_timeout_minutes", "30"),
            ("max_content_length", "5000"),
            ("max_file_size_mb", "10"),
            ("allowed_file_types", "jpg,jpeg,png,gif,mp4,mp3,txt,pdf"),
        ]

        for key, default_value in default_configs:
            try:
                await self.config_service.set_value(key, default_value)
                results["reset"].append(f"{key} = {default_value}")
                logger.info(f"Reset config: {key} = {default_value}")
            except Exception as e:
                error_msg = f"Failed to reset {key}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

        return results


class AdminConfigLoader:
    """Load and manage admin configuration from YAML file."""

    def __init__(self, config_path: str = "config/admin_config.yaml"):
        self.config_path = Path(config_path)
        self._config_data: Optional[Dict[str, Any]] = None

    def load_config(self) -> Dict[str, Any]:
        """Load admin configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Admin config file not found: {self.config_path}")

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)

            logger.info(f"Admin configuration loaded from {self.config_path}")
            return self._config_data

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in admin config: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to load admin config: {str(e)}")
            raise

    def get_automation_config(self) -> Dict[str, Any]:
        """Get automation section configuration."""
        if self._config_data is None:
            self.load_config()
        return self._config_data.get("automation", {})

    def get_admin_panel_config(self) -> Dict[str, Any]:
        """Get admin panel section configuration."""
        if self._config_data is None:
            self.load_config()
        return self._config_data.get("admin_panel", {})

    def get_vip_management_config(self) -> Dict[str, Any]:
        """Get VIP management section configuration."""
        if self._config_data is None:
            self.load_config()
        return self._config_data.get("vip_management", {})

    def get_coordinator_config(self) -> Dict[str, Any]:
        """Get coordinator integration configuration."""
        if self._config_data is None:
            self.load_config()
        return self._config_data.get("coordinator", {})

    def get_error_handling_config(self) -> Dict[str, Any]:
        """Get error handling configuration."""
        if self._config_data is None:
            self.load_config()
        return self._config_data.get("error_handling", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        if self._config_data is None:
            self.load_config()
        return self._config_data.get("logging", {})

    def get_subscription_reminders_config(self) -> Dict[str, Any]:
        """Get subscription reminders configuration (Requirement 6.1)."""
        automation = self.get_automation_config()
        return automation.get("subscription_reminders", {})

    def get_message_cleanup_config(self) -> Dict[str, Any]:
        """Get message cleanup configuration (Requirement 6.2)."""
        automation = self.get_automation_config()
        return automation.get("message_cleanup", {})

    def is_automation_enabled(self) -> bool:
        """Check if automation service is enabled."""
        automation = self.get_automation_config()
        scheduler = automation.get("scheduler", {})
        return scheduler.get("enabled", False)

    def get_metadata(self) -> Dict[str, Any]:
        """Get configuration metadata."""
        if self._config_data is None:
            self.load_config()
        return self._config_data.get("metadata", {})


async def initialize_system_configuration():
    """Initialize the complete system configuration."""
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            initializer = ConfigInitializer(session)

            print("🔧 Initializing narrative system configuration...")

            # Initialize default values
            init_results = await initializer.initialize_narrative_config()
            print(f"✅ Initialized {len(init_results['initialized'])} configuration values")

            if init_results['initialized']:
                print("\nInitialized configurations:")
                for config in init_results['initialized']:
                    print(f"  - {config}")

            if init_results['skipped']:
                print(f"\n⏭️  Skipped {len(init_results['skipped'])} existing configurations")

            if init_results['errors']:
                print(f"\n❌ {len(init_results['errors'])} errors occurred:")
                for error in init_results['errors']:
                    print(f"  - {error}")

            # Validate configuration
            print("\n🔍 Validating configuration...")
            validation_results = await initializer.validate_existing_config()

            if validation_results.get("overall_valid", False):
                print("✅ Configuration validation passed")
            else:
                print("⚠️  Configuration validation warnings detected")
                for key, value in validation_results.items():
                    if key.endswith("_valid") and not value:
                        print(f"  - {key}: {value}")

            # Show configuration summary
            print("\n📋 Configuration Summary:")
            summary = await initializer.get_config_summary()

            print("\nFeatures:")
            for feature, enabled in summary["features"].items():
                status = "✅" if enabled else "❌"
                print(f"  {status} {feature}")

            print("\nPerformance Settings:")
            for setting, value in summary["performance"].items():
                print(f"  - {setting}: {value}")

            print("\nSecurity Settings:")
            for setting, value in summary["security"].items():
                print(f"  - {setting}: {value}")

            return {
                "initialization": init_results,
                "validation": validation_results,
                "summary": summary
            }

    except Exception as e:
        error_msg = f"Configuration initialization failed: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return {"error": error_msg}


async def run_configuration_diagnostics():
    """Run comprehensive configuration diagnostics."""
    print("🔍 Running comprehensive configuration diagnostics...")

    try:
        # Run full configuration check
        full_check = run_full_configuration_check()

        print("\n📊 Configuration Validation Results:")
        validation = full_check["validation"]

        for category, results in validation.items():
            if category == "overall_valid":
                continue

            if isinstance(results, dict):
                status = "✅" if results.get("overall_valid", True) else "❌"
                print(f"  {status} {category.title()}")

                if not results.get("overall_valid", True) and "error" not in results:
                    # Show specific validation failures
                    for key, value in results.items():
                        if key.endswith("_valid") and not value:
                            print(f"    ⚠️  {key}")

        # Security audit results
        print("\n🔒 Security Audit Results:")
        security_audit = full_check["security_audit"]

        if security_audit["errors"]:
            print("  ❌ Security Errors:")
            for error in security_audit["errors"]:
                print(f"    - {error}")

        if security_audit["warnings"]:
            print("  ⚠️  Security Warnings:")
            for warning in security_audit["warnings"]:
                print(f"    - {warning}")

        if not security_audit["errors"] and not security_audit["warnings"]:
            print("  ✅ No security issues detected")

        # Overall status
        overall_valid = validation.get("overall_valid", False)
        has_security_errors = bool(security_audit["errors"])

        if overall_valid and not has_security_errors:
            print("\n🎉 System configuration is valid and secure!")
        elif overall_valid:
            print("\n⚠️  System configuration is valid but has security warnings")
        else:
            print("\n❌ System configuration needs attention")

        return full_check

    except Exception as e:
        error_msg = f"Configuration diagnostics failed: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return {"error": error_msg}


if __name__ == "__main__":
    # Run as script for manual configuration initialization
    async def main():
        print("🚀 Narrative System Configuration Initializer")
        print("=" * 50)

        # Initialize configuration
        init_result = await initialize_system_configuration()

        print("\n" + "=" * 50)

        # Run diagnostics
        diagnostics_result = await run_configuration_diagnostics()

        print("\n" + "=" * 50)
        print("✅ Configuration initialization and validation complete!")

    asyncio.run(main())