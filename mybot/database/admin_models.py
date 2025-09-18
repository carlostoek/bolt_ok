# database/admin_models.py
"""
Administrative models for the Channel Administration Module.

This module provides comprehensive models for admin action logging, audit trails,
and administrative operations tracking to support the enhanced DianaBot
administration system.

MIGRATION NOTES:
- AdminActionLog in this module uses table 'admin_action_logs_v2' to coexist with the
  existing AdminActionLog model in models.py (table 'admin_action_logs').
- This enhanced version provides extended features for the modulo-admon specification.
- For migration: services should gradually transition to use AdminActionLogV2 from this module.
- The existing AdminActionLog in models.py can be deprecated once all services are updated.

MODELS OVERVIEW:
- AdminActionLog: Enhanced logging with detailed categorization and audit trails
- AdminSession: Session tracking for administrative security monitoring
- AdminOperationBatch: Batch operation tracking with progress and rollback support
- ChannelContent: Channel content tracking with access control and engagement metrics
- AdminActionType/AdminActionStatus: Comprehensive enumerations for action categorization
- ChannelType/ContentType/ProtectionLevel: Enumerations for content classification and access control
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    Boolean,
    JSON,
    Text,
    ForeignKey,
    Enum,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
import enum
from .base import Base


class AdminActionType(enum.Enum):
    """Enumeration of administrative action types for categorization and reporting."""

    # User Management Actions
    USER_VIP_GRANTED = "user_vip_granted"
    USER_VIP_REVOKED = "user_vip_revoked"
    USER_VIP_EXTENDED = "user_vip_extended"
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"
    USER_ROLE_CHANGED = "user_role_changed"

    # Token Management Actions
    TOKEN_GENERATED = "token_generated"
    TOKEN_BATCH_GENERATED = "token_batch_generated"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_ACTIVATED = "token_activated"

    # Channel Management Actions
    CHANNEL_CREATED = "channel_created"
    CHANNEL_DELETED = "channel_deleted"
    CHANNEL_SETTINGS_UPDATED = "channel_settings_updated"
    CHANNEL_PERMISSIONS_UPDATED = "channel_permissions_updated"

    # Content Management Actions
    CONTENT_PUBLISHED = "content_published"
    CONTENT_DELETED = "content_deleted"
    CONTENT_PROTECTED = "content_protected"
    CONTENT_UNPROTECTED = "content_unprotected"

    # System Administration Actions
    SYSTEM_CONFIG_UPDATED = "system_config_updated"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    SYSTEM_MAINTENANCE = "system_maintenance"
    DATABASE_BACKUP = "database_backup"
    DATABASE_RESTORE = "database_restore"

    # Admin Permission Management Actions
    ADMIN_PERMISSIONS_GRANTED = "admin_permissions_granted"
    ADMIN_PERMISSIONS_REVOKED = "admin_permissions_revoked"

    # Automation Actions
    AUTOMATION_RULE_CREATED = "automation_rule_created"
    AUTOMATION_RULE_UPDATED = "automation_rule_updated"
    AUTOMATION_RULE_DELETED = "automation_rule_deleted"
    AUTOMATION_EXECUTED = "automation_executed"

    # Reporting and Analytics Actions
    REPORT_GENERATED = "report_generated"
    REVENUE_REPORT_GENERATED = "revenue_report_generated"
    DATA_EXPORTED = "data_exported"
    ANALYTICS_ACCESSED = "analytics_accessed"

    # Message Management Actions
    MESSAGE_CLEANUP = "message_cleanup"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_EDITED = "message_edited"

    # Security Actions
    SECURITY_BREACH_DETECTED = "security_breach_detected"
    ACCESS_DENIED = "access_denied"
    LOGIN_ATTEMPT = "login_attempt"
    SESSION_TERMINATED = "session_terminated"


class AdminActionStatus(enum.Enum):
    """Status enumeration for administrative actions."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class ChannelType(enum.Enum):
    """Enumeration of channel types for content access control."""

    FREE = "free"
    VIP = "vip"


class ContentType(enum.Enum):
    """Enumeration of content types for channel content tracking."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    POLL = "poll"
    DOCUMENT = "document"
    AUDIO = "audio"
    ANIMATION = "animation"
    STICKER = "sticker"


class ProtectionLevel(enum.Enum):
    """Enumeration of content protection levels for exclusive content."""

    NONE = "none"                    # No protection
    NO_FORWARD = "no_forward"        # Disable forwarding
    NO_DOWNLOAD = "no_download"      # Disable download/save
    FULL_PROTECTION = "full_protection"  # Both no forward and no download


class AdminActionLog(Base):
    """
    Comprehensive administrative action logging model for DianaBot.

    This model provides detailed audit trails, security monitoring, and compliance
    tracking for all administrative operations. It replaces and enhances the basic
    logging functionality with advanced features for the Channel Administration Module.

    Features:
    - Detailed action categorization with enum types
    - Hierarchical action relationships for complex operations
    - Performance tracking with execution times
    - Security monitoring with IP and session tracking
    - Batch operation support with correlation IDs
    - Compliance and regulatory information tracking
    - Error handling and recovery information
    """

    __tablename__ = "admin_action_logs_v2"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Administrative context
    admin_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(Enum(AdminActionType), nullable=False, index=True)
    action_status = Column(Enum(AdminActionStatus), default=AdminActionStatus.COMPLETED, index=True)

    # Target information (flexible to support different entity types)
    target_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)
    target_entity_type = Column(String(50), nullable=True, index=True)  # user, channel, token, content, etc.
    target_entity_id = Column(String(100), nullable=True, index=True)

    # Action details and metadata
    action_details = Column(JSON, nullable=True)  # Flexible storage for action-specific data
    action_summary = Column(Text, nullable=True)  # Human-readable action summary

    # Temporal information
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=True)  # For scheduled actions
    started_at = Column(DateTime, nullable=True)    # When action execution began
    completed_at = Column(DateTime, nullable=True)  # When action completed

    # Performance and execution tracking
    execution_time_ms = Column(Float, nullable=True)  # Execution time in milliseconds
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Error handling and recovery
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    error_stack_trace = Column(Text, nullable=True)
    recovery_actions = Column(JSON, nullable=True)  # Automated recovery steps taken

    # Security and audit information
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6 address
    user_agent = Column(Text, nullable=True)        # For web-based admin actions
    session_id = Column(String(100), nullable=True, index=True)

    # Hierarchical action relationships
    parent_action_id = Column(String, ForeignKey("admin_action_logs_v2.id"), nullable=True)
    root_action_id = Column(String, ForeignKey("admin_action_logs_v2.id"), nullable=True)

    # Impact and rollback information
    affected_records_count = Column(Integer, default=0)
    rollback_data = Column(JSON, nullable=True)  # Data needed for rollback
    is_reversible = Column(Boolean, default=True)

    # Compliance and regulatory information
    compliance_tags = Column(JSON, nullable=True)  # Tags for compliance tracking
    data_classification = Column(String(20), default="internal")  # public, internal, confidential, restricted
    retention_period_days = Column(Integer, default=2555)  # 7 years default retention

    # Additional metadata
    client_version = Column(String(50), nullable=True)  # Bot version when action was performed
    environment = Column(String(20), default="production")  # production, staging, development
    correlation_id = Column(String(100), nullable=True)  # For tracing related actions

    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id], lazy="selectin")
    target_user = relationship("User", foreign_keys=[target_user_id], lazy="selectin")
    parent_action = relationship("AdminActionLog", foreign_keys=[parent_action_id], remote_side=[id])
    child_actions = relationship("AdminActionLog", foreign_keys=[parent_action_id], cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<AdminActionLog(id='{self.id}', "
            f"admin_user_id={self.admin_user_id}, "
            f"action_type='{self.action_type.value}', "
            f"status='{self.action_status.value}', "
            f"timestamp='{self.timestamp}')>"
        )

    @property
    def is_completed(self) -> bool:
        """Check if the action is completed successfully."""
        return self.action_status == AdminActionStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if the action failed."""
        return self.action_status == AdminActionStatus.FAILED

    @property
    def needs_retry(self) -> bool:
        """Check if the action needs to be retried."""
        return (
            self.action_status == AdminActionStatus.FAILED and
            self.retry_count < self.max_retries
        )


class AdminSession(Base):
    """
    Administrative session tracking for security and audit purposes.

    This model tracks admin user sessions to provide security monitoring,
    concurrent session management, and detailed audit trails for administrative
    access patterns.
    """

    __tablename__ = "admin_sessions"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_token = Column(String(255), unique=True, nullable=False, index=True)

    # User and authentication context
    admin_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    authentication_method = Column(String(50), default="telegram")  # telegram, web, api

    # Session lifecycle
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    terminated_at = Column(DateTime, nullable=True)

    # Session status and security
    is_active = Column(Boolean, default=True, index=True)
    is_elevated = Column(Boolean, default=False)  # For high-privilege operations

    # Network and device information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    location_info = Column(JSON, nullable=True)

    # Security flags
    suspicious_activity_detected = Column(Boolean, default=False)
    failed_operation_count = Column(Integer, default=0)
    last_failed_operation_at = Column(DateTime, nullable=True)

    # Termination information
    termination_reason = Column(String(50), nullable=True)  # logout, timeout, security, forced
    terminated_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)

    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id], lazy="selectin")
    terminated_by = relationship("User", foreign_keys=[terminated_by_user_id])

    def __repr__(self):
        return (
            f"<AdminSession(id='{self.id}', "
            f"admin_user_id={self.admin_user_id}, "
            f"is_active={self.is_active}, "
            f"created_at='{self.created_at}')>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    @property
    def duration_minutes(self) -> float:
        """Calculate session duration in minutes."""
        end_time = self.terminated_at or self.last_activity_at
        return (end_time - self.created_at).total_seconds() / 60


class AdminOperationBatch(Base):
    """
    Batch operation tracking for administrative tasks.

    This model tracks batch operations like bulk token generation, mass user
    updates, or system-wide configuration changes to provide progress monitoring
    and rollback capabilities.
    """

    __tablename__ = "admin_operation_batches"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Operation context
    admin_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    operation_type = Column(String(100), nullable=False, index=True)
    operation_name = Column(String(255), nullable=False)
    operation_description = Column(Text, nullable=True)

    # Batch configuration
    total_items = Column(Integer, nullable=False)
    batch_size = Column(Integer, default=50)
    parallel_workers = Column(Integer, default=1)

    # Progress tracking
    processed_items = Column(Integer, default=0)
    successful_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    skipped_items = Column(Integer, default=0)

    # Status and timing
    status = Column(Enum(AdminActionStatus), default=AdminActionStatus.PENDING, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion_at = Column(DateTime, nullable=True)

    # Error handling
    continue_on_error = Column(Boolean, default=True)
    error_threshold_percent = Column(Float, default=10.0)  # Stop if error rate exceeds this

    # Results and metadata
    operation_results = Column(JSON, nullable=True)  # Detailed results per item
    performance_metrics = Column(JSON, nullable=True)  # Timing, throughput, etc.
    rollback_plan = Column(JSON, nullable=True)  # Plan for rolling back changes

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id], lazy="selectin")
    related_actions = relationship(
        lambda: AdminActionLog,
        primaryjoin="AdminOperationBatch.id == AdminActionLog.correlation_id",
        foreign_keys="[AdminActionLog.correlation_id]",
        viewonly=True
    )

    def __repr__(self):
        return (
            f"<AdminOperationBatch(id='{self.id}', "
            f"operation_type='{self.operation_type}', "
            f"status='{self.status.value}', "
            f"progress={self.processed_items}/{self.total_items})>"
        )

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.processed_items == 0:
            return 0.0
        return (self.successful_items / self.processed_items) * 100

    @property
    def is_complete(self) -> bool:
        """Check if the batch operation is complete."""
        return self.processed_items >= self.total_items


class ChannelContent(Base):
    """
    Channel content tracking model for the Channel Administration Module.

    This model provides comprehensive tracking of content published to channels,
    including access control, protection levels, and engagement metrics.
    It supports requirements 3.1 (channel content control) and 3.3 (exclusive
    content administration) from the modulo-admon specification.

    Features:
    - Channel type-based access control (FREE/VIP)
    - Content type classification with detailed metadata
    - Protection level enforcement for exclusive content
    - Engagement metrics tracking (views, reactions, etc.)
    - Administrative audit trail with publishing details
    - Flexible content storage with JSON metadata
    - Telegram message integration for content management
    """

    __tablename__ = "channel_content"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Channel and content classification
    channel_type = Column(Enum(ChannelType), nullable=False, index=True)
    content_type = Column(Enum(ContentType), nullable=False, index=True)
    protection_level = Column(Enum(ProtectionLevel), default=ProtectionLevel.NONE, index=True)

    # Content metadata and storage
    content_data = Column(JSON, nullable=False)  # Flexible storage for content details
    content_title = Column(String(255), nullable=True)  # Optional title for content
    content_description = Column(Text, nullable=True)   # Optional description

    # Telegram integration
    telegram_message_id = Column(BigInteger, nullable=True, index=True)  # Telegram message ID
    telegram_chat_id = Column(BigInteger, nullable=True, index=True)     # Telegram chat ID
    telegram_file_id = Column(String(255), nullable=True)               # Telegram file ID for media

    # Administrative context
    published_by_admin_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    approved_by_admin_id = Column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)

    # Temporal information
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    publish_date = Column(DateTime, default=func.now(), nullable=False, index=True)
    scheduled_date = Column(DateTime, nullable=True, index=True)  # For scheduled content
    expires_at = Column(DateTime, nullable=True, index=True)      # Content expiration

    # Status and lifecycle
    is_published = Column(Boolean, default=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)     # Featured content flag
    is_pinned = Column(Boolean, default=False, index=True)       # Pinned content flag

    # Engagement metrics (JSON field for flexibility)
    engagement_metrics = Column(JSON, default=dict)  # Views, reactions, shares, etc.
    view_count = Column(Integer, default=0)           # Quick access to view count
    reaction_count = Column(Integer, default=0)       # Quick access to reaction count

    # Content protection and access control
    access_restriction = Column(JSON, nullable=True)  # Additional access restrictions
    min_vip_level = Column(Integer, default=1)        # Minimum VIP level required
    required_achievements = Column(JSON, nullable=True)  # Required user achievements

    # Categorization and tagging
    tags = Column(JSON, default=list)                 # Content tags for categorization
    category = Column(String(100), nullable=True, index=True)  # Content category
    language = Column(String(10), default="es")       # Content language code

    # Analytics and performance
    performance_score = Column(Float, default=0.0)    # Calculated performance score
    quality_rating = Column(Float, nullable=True)     # Manual quality rating (1-5)
    last_engagement_at = Column(DateTime, nullable=True)  # Last user interaction

    # Moderation and compliance
    moderation_status = Column(String(20), default="approved")  # approved, pending, rejected
    compliance_flags = Column(JSON, nullable=True)    # Compliance tracking flags
    content_warnings = Column(JSON, nullable=True)    # Content warnings/labels

    # Relationships
    published_by = relationship(
        "User",
        foreign_keys=[published_by_admin_id],
        lazy="selectin"
    )
    approved_by = relationship(
        "User",
        foreign_keys=[approved_by_admin_id],
        lazy="selectin"
    )

    def __repr__(self):
        return (
            f"<ChannelContent(id='{self.id}', "
            f"channel_type='{self.channel_type.value}', "
            f"content_type='{self.content_type.value}', "
            f"protection_level='{self.protection_level.value}', "
            f"published_by={self.published_by_admin_id}, "
            f"publish_date='{self.publish_date}')>"
        )

    @property
    def is_protected(self) -> bool:
        """Check if content has any protection level."""
        return self.protection_level != ProtectionLevel.NONE

    @property
    def is_vip_only(self) -> bool:
        """Check if content is VIP-only."""
        return self.channel_type == ChannelType.VIP

    @property
    def is_expired(self) -> bool:
        """Check if content is expired."""
        if not self.expires_at:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    @property
    def is_scheduled(self) -> bool:
        """Check if content is scheduled for future publication."""
        if not self.scheduled_date:
            return False
        from datetime import datetime
        return datetime.utcnow() < self.scheduled_date

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate (reactions/views)."""
        if self.view_count == 0:
            return 0.0
        return (self.reaction_count / self.view_count) * 100

    def update_engagement_metrics(self, metric_type: str, value: int) -> None:
        """Update engagement metrics safely."""
        if not isinstance(self.engagement_metrics, dict):
            self.engagement_metrics = {}

        self.engagement_metrics[metric_type] = value

        # Update quick access fields
        if metric_type == "views":
            self.view_count = value
        elif metric_type == "reactions":
            self.reaction_count = value

    def add_tag(self, tag: str) -> None:
        """Add a tag to the content."""
        if not isinstance(self.tags, list):
            self.tags = []

        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the content."""
        if isinstance(self.tags, list) and tag in self.tags:
            self.tags.remove(tag)

    def can_user_access(self, user_vip_level: int = 0, user_achievements: list = None) -> bool:
        """
        Check if a user can access this content based on their VIP level and achievements.

        Args:
            user_vip_level: User's VIP level (0 for free users)
            user_achievements: List of user's achievements

        Returns:
            bool: True if user can access the content
        """
        # Check if content is expired
        if self.is_expired:
            return False

        # Check if content is active
        if not self.is_active:
            return False

        # Check channel type access
        if self.channel_type == ChannelType.VIP and user_vip_level == 0:
            return False

        # Check minimum VIP level
        if user_vip_level < self.min_vip_level:
            return False

        # Check required achievements
        if self.required_achievements and user_achievements:
            required_set = set(self.required_achievements)
            user_set = set(user_achievements or [])
            if not required_set.issubset(user_set):
                return False

        return True
