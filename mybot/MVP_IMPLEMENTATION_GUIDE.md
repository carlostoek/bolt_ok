# Diana Bot MVP - Tactical Implementation Guide

## Phase 1 Implementation Tasks (Days 1-5)

### Day 1-3: Database Migration Critical Path

#### Task 1.1: Model Migration Analysis
**Duration**: 4 hours  
**Owner**: Backend Lead

```bash
# Command to identify all deprecated model usage
grep -r "narrative_models" --include="*.py" . > deprecated_usage.txt
grep -r "NarrativeFragment" --exclude="*unified*" --include="*.py" . >> deprecated_usage.txt

# Estimated files to update: ~95 service files
find . -name "*.py" -exec grep -l "from.*narrative_models" {} \;
```

**Validation Checklist**:
- [ ] All imports mapped to unified models
- [ ] Field name compatibility verified
- [ ] Relationship mappings documented
- [ ] Migration script created with rollback

#### Task 1.2: Data Migration Script
**Duration**: 8 hours  
**Owner**: Backend Developer

```python
# /scripts/migrate_to_unified_models.py
async def migrate_narrative_data():
    """
    Critical: Migrate narrative data with integrity checks
    """
    # 1. Backup existing data
    # 2. Transform data structure
    # 3. Validate relationships
    # 4. Test rollback procedure
    pass
```

**Validation Criteria**:
- [ ] Zero data loss during migration
- [ ] All relationships maintained
- [ ] Rollback tested and verified
- [ ] Performance benchmarks maintained

#### Task 1.3: Service Layer Updates
**Duration**: 12 hours  
**Owner**: 2 Backend Developers (parallel work)

**Files requiring updates** (priority order):
1. `/services/narrative_service.py` - Core narrative engine
2. `/services/coordinador_central.py` - Central coordinator
3. `/services/diana_menu_system.py` - Menu interface
4. `/handlers/*/*.py` - All handler modules

**Code Pattern**:
```python
# OLD (deprecated)
from database.narrative_models import NarrativeFragment

# NEW (unified)
from database.narrative_unified import NarrativeFragment
```

### Day 4-5: Test Coverage Remediation

#### Task 1.4: Fix Critical Test Failures
**Duration**: 10 hours  
**Owner**: QA Specialist + Backend Developer

**Priority Test Fixes**:
```bash
# Run tests to identify failures
python -m pytest tests/services/test_narrative_service.py -v
python -m pytest tests/services/test_coordinador_central.py -v
python -m pytest tests/integration/ -v

# Expected failure patterns:
# - AsyncMock context manager issues
# - Deprecated model references in fixtures
# - Database session lifecycle problems
```

**Critical Tests to Fix**:
1. `test_narrative_progression` - Core user journey
2. `test_points_calculation` - Economic system
3. `test_diana_menu_navigation` - Menu system
4. `test_user_registration_flow` - User onboarding

#### Task 1.5: Test Infrastructure Update
**Duration**: 6 hours  
**Owner**: QA Specialist

```python
# /tests/conftest.py updates needed
@pytest_asyncio.fixture
async def unified_narrative_session():
    """Updated fixture for unified models"""
    # Configure AsyncSession with new models
    # Set up proper mock relationships
    pass
```

## Phase 2 Implementation Tasks (Days 6-10)

### Day 6-7: User System & Diana Menu

#### Task 2.1: User Registration Enhancement
**Duration**: 8 hours  
**Owner**: Backend Developer

**Implementation Focus**:
```python
# /services/user_service.py enhancements
async def enhanced_user_registration(user_data: dict, session: AsyncSession):
    """
    Enhanced registration with Diana character introduction
    """
    # 1. Create user record
    # 2. Initialize Diana relationship state
    # 3. Set initial narrative position
    # 4. Award welcome besitos
    # 5. Trigger introduction sequence
```

**Validation Requirements**:
- [ ] 99%+ registration success rate
- [ ] Diana introduction triggers correctly
- [ ] Initial besitos awarded properly
- [ ] User state properly initialized

#### Task 2.2: Diana Menu Unification
**Duration**: 12 hours  
**Owner**: Backend Developer + UX Review

**Menu Structure Implementation**:
```
/diana
├── 💋 Continuar Historia (narrative progression)
├── 🌟 Mis Besitos (points & level)
├── 🎯 Misiones (active missions)
├── 🏆 Logros (achievements)
├── 💎 VIP (subscription features)
└── ⚙️ Configuración (settings)
```

### Day 8-10: Basic Narrative Engine

#### Task 2.3: Narrative Fragment Creation
**Duration**: 16 hours  
**Owner**: Narrative Designer + Backend Developer

**Fragment Requirements**:
- 15 narrative fragments minimum for MVP
- Each fragment must pass Diana character consistency validation
- Decision points with meaningful consequences
- Integration with besitos reward system

**Fragment Validation Framework**:
```python
# /services/character_consistency_validator.py
class DianaConsistencyValidator:
    async def validate_fragment(self, fragment: NarrativeFragment) -> ConsistencyScore:
        """
        Validate Diana's character consistency in narrative content
        Scoring criteria:
        - Mysterious tone (0-25 points)
        - Seductive undertones (0-25 points) 
        - Emotional complexity (0-25 points)
        - Intellectual engagement (0-25 points)
        
        Required score: >90/100 for approval
        """
```

#### Task 2.4: Decision Tree Implementation
**Duration**: 8 hours  
**Owner**: Backend Developer

**Technical Implementation**:
- Decision validation logic
- State persistence between choices
- Consequence tracking system
- Integration with achievement triggers

## Phase 3 Implementation Tasks (Days 11-15)

### Day 11-12: Besitos Economy System

#### Task 3.1: Points Calculation Engine
**Duration**: 10 hours  
**Owner**: Backend Developer

**Economic Rules** (MVP baseline):
```python
POINTS_CONFIG = {
    'story_fragment_completion': 10,
    'decision_made': 5,
    'daily_login': 15,
    'mission_completed': 25,
    'achievement_unlocked': 50,
    'channel_reaction': 2,
    'vip_bonus_multiplier': 1.5
}
```

#### Task 3.2: Level Progression System
**Duration**: 6 hours  
**Owner**: Backend Developer

**Level Thresholds**:
- Level 1-5: 100 besitos per level
- Level 6-10: 200 besitos per level
- Level 11+: 500 besitos per level

### Day 13-15: Missions & Achievements

#### Task 3.3: Mission System Implementation
**Duration**: 12 hours  
**Owner**: Gamification Specialist

**MVP Missions**:
1. "Primera Conversación" - Complete 3 narrative fragments
2. "Exploradora Curiosa" - Make 5 decisions in story
3. "Devotion Daily" - Login 3 consecutive days
4. "Social Butterfly" - React to 10 channel posts
5. "VIP Experience" - Upgrade to VIP status
6. "Achievement Hunter" - Unlock 3 achievements
7. "Story Enthusiast" - Complete 10 narrative fragments
8. "Community Member" - Join 2 channels
9. "Besitos Collector" - Earn 500 besitos total
10. "Diana's Favorite" - Reach level 5

#### Task 3.4: Achievement System Implementation
**Duration**: 8 hours  
**Owner**: Gamification Specialist

**MVP Achievements** (15 required):
1. "First Steps" - Complete registration
2. "Diana's Interest" - Complete first story fragment
3. "Decision Maker" - Make first narrative choice
4. "Point Collector" - Earn first 100 besitos
5. "Level Up" - Reach level 2
6. "Daily Devotion" - Login 7 consecutive days
7. "Story Explorer" - Complete 5 story fragments
8. "Choice Master" - Make 20 narrative decisions
9. "Community Member" - React to first channel post
10. "Mission Accomplished" - Complete first mission
11. "VIP Access" - Subscribe to VIP
12. "Besitos Millionaire" - Earn 1000 besitos
13. "High Achiever" - Unlock 10 achievements
14. "Diana's Confidant" - Reach level 10
15. "Ultimate Explorer" - Complete all available content

## Phase 4 Implementation Tasks (Days 16-20)

### Day 16-17: Performance Optimization

#### Task 4.1: Database Query Optimization
**Duration**: 8 hours  
**Owner**: Backend Lead

**Critical Queries to Optimize**:
```sql
-- User narrative progress query (most frequent)
SELECT nf.*, up.progress_data 
FROM narrative_fragments_unified nf 
LEFT JOIN user_progress up ON up.fragment_id = nf.id 
WHERE up.user_id = ? AND nf.is_active = true;

-- Mission progress aggregation
SELECT m.*, COUNT(ump.id) as completed_count
FROM missions m 
LEFT JOIN user_mission_progress ump ON ump.mission_id = m.id
WHERE ump.user_id = ?;
```

#### Task 4.2: Caching Layer Implementation
**Duration**: 8 hours  
**Owner**: Backend Developer

**Caching Strategy**:
- Redis for session state and user progress
- In-memory cache for narrative fragments
- Database connection pooling optimization

### Day 18-20: Production Deployment Prep

#### Task 4.3: Monitoring Setup
**Duration**: 6 hours  
**Owner**: DevOps Engineer

**Monitoring Requirements**:
- Response time tracking (<2s requirement)
- Error rate monitoring (<0.1% target)
- Diana character consistency alerts
- Database performance metrics

#### Task 4.4: Security Audit
**Duration**: 8 hours  
**Owner**: Security Specialist + Backend Lead

**Security Checklist**:
- [ ] SQL injection prevention validated
- [ ] User data encryption verified
- [ ] API rate limiting implemented
- [ ] Token validation secure
- [ ] No sensitive data in logs

## Validation Procedures

### Daily Validation Checklist

**Phase 1 Validation**:
```bash
# Database integrity check
python scripts/validate_database_integrity.py

# Test coverage report
python -m pytest --cov=. --cov-report=term-missing

# Performance baseline
python scripts/performance_benchmark.py
```

**Phase 2 Validation**:
```bash
# Character consistency validation
python scripts/validate_diana_consistency.py

# User journey testing
python scripts/test_complete_user_journey.py

# Menu navigation testing
python scripts/test_diana_menu_navigation.py
```

**Phase 3 Validation**:
```bash
# Economic system validation
python scripts/validate_besitos_economy.py

# Mission completion testing
python scripts/test_mission_system.py

# Achievement unlock validation
python scripts/test_achievement_system.py
```

**Phase 4 Validation**:
```bash
# Load testing
python scripts/load_test.py --users=1000 --duration=300

# Production readiness check
python scripts/production_readiness_check.py

# Security scan
python scripts/security_audit.py
```

## Emergency Procedures

### Rollback Procedures

**Database Rollback** (if migration fails):
```bash
# Automated rollback within 30 minutes
python scripts/emergency_rollback.py --phase=database

# Validation after rollback
python scripts/validate_rollback_integrity.py
```

**Feature Rollback** (if major issues found):
```bash
# Feature flag disable
python scripts/disable_feature.py --feature=narrative_unified

# Graceful degradation to previous version
python scripts/graceful_degradation.py
```

### Escalation Procedures

**Severity 1** (System down):
- Immediate rollback within 15 minutes
- All hands notification
- CEO notification within 30 minutes

**Severity 2** (Diana character issues):
- Narrative designer immediate notification
- Character consistency review within 2 hours
- Fix or rollback within 24 hours

**Severity 3** (Performance degradation):
- Performance optimization within 48 hours
- User notification if >5s response times
- Infrastructure scaling if needed

## Success Metrics Tracking

### Real-time Dashboards Required

**Technical Metrics**:
- Response time distribution (target: 95% <2s)
- Error rate by endpoint (target: <0.1%)
- Database query performance
- Memory and CPU utilization

**Business Metrics**:
- User registration rate
- Story progression completion rate
- Mission completion statistics
- VIP conversion funnel

**Character Consistency Metrics**:
- Diana personality consistency score
- User satisfaction with interactions
- Narrative flow completion rates
- Emotional transition smoothness

This tactical guide provides the detailed implementation steps needed to transform the current Diana Bot system into a production-ready MVP while maintaining the character integrity that makes Diana compelling to users.