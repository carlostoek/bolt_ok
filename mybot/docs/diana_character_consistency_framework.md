# Diana Character Consistency Validation Framework

## Overview

The Diana Character Consistency Validation Framework ensures that Diana Bot maintains her mysterious, seductive personality across all interactions with users. This framework is **critical for MVP success** as it guarantees that Diana's character remains compelling and consistent, achieving the required >95% consistency score.

## Table of Contents

- [Character Profile](#character-profile)
- [Framework Architecture](#framework-architecture)
- [Validation Components](#validation-components)
- [Testing Infrastructure](#testing-infrastructure)
- [CI/CD Integration](#cicd-integration)
- [Usage Guidelines](#usage-guidelines)
- [Performance Requirements](#performance-requirements)
- [Troubleshooting](#troubleshooting)

## Character Profile

Diana's personality consists of four core traits, each equally weighted (25 points each):

### 🎭 Mysterious (25 points)
- Never reveals too much, always maintains intrigue
- Uses ellipsis (...), indirect language, hints rather than direct statements
- Creates anticipation and curiosity
- **Indicators**: "secretos", "misterio", "susurra", "¿acaso sabes", "tal vez"

### 💋 Seductive (25 points)
- Subtle charm and allure in interactions
- Uses intimate language and emotional connection
- Creates magnetic attraction
- **Indicators**: "💋", "encanto", "mi querido", "fascinante", personal pronouns

### 💭 Emotionally Complex (25 points)
- Deep emotional layers, not simple responses
- Shows inner conflicts and vulnerability
- Complex emotional expressions
- **Indicators**: "mezcla de", "por un lado...por otro", "corazón", "alma"

### 🧠 Intellectually Engaging (25 points)
- Stimulates curiosity and thought
- Poses questions and invites reflection
- Offers deeper perspectives
- **Indicators**: "¿te has preguntado", "filosofía", "reflexiona", "dimensión"

## Framework Architecture

```
┌─────────────────────────────────────────────────┐
│            Content Creation                      │
│  (Narrative Fragments, Menu Text, etc.)        │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│         Diana Character Validator               │
│  • Pattern Recognition                          │
│  • Trait Scoring (0-25 each)                   │
│  • Violation Detection                          │
│  • Overall Score Calculation                   │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│      Narrative Character Integrity Service     │
│  • Fragment-specific Validation                │
│  • Database Integration                         │
│  • Improvement Suggestions                     │
│  • System-wide Reporting                       │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│             Quality Gate                        │
│  Score ≥ 95.0 → ✅ PASS                        │
│  Score < 95.0 → ❌ FAIL                        │
└─────────────────────────────────────────────────┘
```

## Validation Components

### Core Validator (`DianaCharacterValidator`)

**Location**: `services/diana_character_validator.py`

**Key Methods**:
- `validate_text(text, context=None)` - Main validation function
- `validate_narrative_fragment(fragment)` - Fragment-specific validation
- `batch_validate_content(content_list)` - Batch processing
- `generate_character_report(results)` - Comprehensive reporting

**Usage**:
```python
from services.diana_character_validator import DianaCharacterValidator

validator = DianaCharacterValidator(session)
result = await validator.validate_text(content, context="narrative_fragment")

if result.meets_threshold:
    print(f"✅ Content passed: {result.overall_score}/100")
else:
    print(f"❌ Content failed: {result.overall_score}/100")
    print(f"Violations: {result.violations}")
```

### Character Integrity Service (`NarrativeCharacterIntegrityService`)

**Location**: `services/narrative_character_integrity_service.py`

**Key Methods**:
- `validate_fragment_creation(fragment_data)` - Pre-creation validation
- `validate_all_active_fragments()` - System-wide validation
- `get_character_consistency_report()` - Detailed reporting
- `suggest_character_improvements(fragment_id)` - Improvement guidance

**Usage**:
```python
from services.narrative_character_integrity_service import NarrativeCharacterIntegrityService

integrity_service = NarrativeCharacterIntegrityService(session)
is_valid, result = await integrity_service.validate_fragment_creation(fragment_data)

if not is_valid:
    suggestions = await integrity_service.suggest_character_improvements(fragment_id)
    print(f"Improvements needed: {suggestions['specific_improvements']}")
```

## Testing Infrastructure

### Test Files

1. **`test_diana_character_consistency.py`** - Core validator tests
2. **`test_character_consistency_automation.py`** - Automation and performance tests  
3. **`test_narrative_fragment_character_validation.py`** - Fragment-specific tests
4. **`test_menu_system_character_validation.py`** - Menu system tests
5. **`test_character_consistency_ci_integration.py`** - CI/CD integration tests

### Running Tests

```bash
# Run all character consistency tests
python -m pytest tests/test_diana_character_consistency.py -v

# Run MVP critical tests only
python -m pytest tests/test_character_consistency_ci_integration.py::TestCIPipelineCharacterValidation::test_mvp_character_consistency_gate -v

# Run with coverage
python -m pytest tests/test_*character* --cov=services --cov-report=term-missing
```

### Test Categories

#### 1. MVP Critical Tests ⚠️
These tests **MUST PASS** for MVP release:
- Perfect narrative content achieves ≥95% consistency
- Menu systems maintain ≥85% consistency
- VIP content maintains ≥90% consistency
- Poor content is reliably rejected (<50%)

#### 2. Personality Trait Tests
- Individual trait validation (mysterious, seductive, etc.)
- Trait combination effectiveness
- Character violation detection

#### 3. Integration Tests
- Database fragment validation
- Menu system integration
- Error message consistency
- Performance under load

#### 4. Edge Case Tests
- Empty content handling
- Very long content
- Mixed language content
- Special characters

## CI/CD Integration

### Validation Script

**Location**: `scripts/validate_diana_character_consistency.py`

**Usage**:
```bash
# MVP validation (strict)
python scripts/validate_diana_character_consistency.py --mode mvp --ci

# Quick validation
python scripts/validate_diana_character_consistency.py --mode quick

# Full validation with reporting
python scripts/validate_diana_character_consistency.py --mode full --report-file report.json
```

### CI/CD Pipeline Integration

#### GitHub Actions Example

```yaml
name: Diana Character Consistency Check
on: [push, pull_request]

jobs:
  character-validation:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    
    - name: Run Character Validation
      run: |
        python scripts/validate_diana_character_consistency.py --mode mvp --ci
    
    - name: Upload validation report
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: character-validation-report
        path: diana_character_validation_report.json
```

#### Quality Gates

1. **MVP Gate**: All content samples must achieve ≥95% consistency
2. **Regression Gate**: Previously passing content must maintain quality
3. **Performance Gate**: Validation must complete within time limits
4. **System Health Gate**: All validation components must be operational

### Exit Codes

- `0`: All validations passed ✅
- `1`: Validation failures detected ❌  
- `2`: System error or configuration issue ⚠️

## Usage Guidelines

### For Content Creators

#### ✅ DO:
- Use Diana's signature elements: 💋, 🎭, ✨
- Include ellipsis (...) for mystery
- Show emotional complexity with "por un lado...por otro"
- Ask thought-provoking questions
- Use intimate, personal language

#### ❌ DON'T:
- Use technical language (sistema, configuración, error)
- Be too direct or obvious
- Use casual language (hola, genial, OK)
- Write simple, one-dimensional responses
- Break narrative immersion

### Content Quality Standards

| Score Range | Quality Level | Action Required |
|-------------|---------------|-----------------|
| 95-100 | Excellent ✅ | Ready for production |
| 85-94 | Good ⚠️ | Review and improve |
| 70-84 | Fair 🔄 | Significant revision needed |
| Below 70 | Poor ❌ | Rewrite required |

### Sample High-Quality Content

```
💋 Mi querido... ¿acaso estás preparado para adentrarte en los 
misterios más profundos que susurra mi alma?... Las sombras 
danzan a nuestro alrededor, creando una atmósfera de seducción 
y enigma que solo nosotros podemos comprender...

Siento una mezcla embriagadora de fascinación y anhelo cuando 
te observo... por un lado, mi corazón late con la emoción de 
compartir mis secretos más íntimos contigo, pero por otro, una 
deliciosa inquietud me abraza al contemplar la intensidad de 
esta conexión que crece entre nosotros...

¿Te has preguntado alguna vez qué filosofía subyace a esta danza 
de seducción que compartimos?
```
**Expected Score**: ≥95/100

## Performance Requirements

### Validation Performance

- **Single validation**: <100ms
- **Batch validation** (10 items): <500ms
- **System-wide validation**: <2 seconds
- **Memory usage**: <50MB for typical workloads

### Scalability

- Supports concurrent validation requests
- Database fragment validation scales to 1000+ fragments
- CI/CD pipeline validation completes within 30 seconds

## Troubleshooting

### Common Issues

#### Issue: Content scoring too low despite good quality

**Solution**:
1. Check for technical language violations
2. Ensure all four personality traits are represented
3. Use the improvement suggestions feature:
   ```python
   suggestions = await integrity_service.suggest_character_improvements(fragment_id)
   ```

#### Issue: Tests failing in CI/CD

**Solution**:
1. Verify test database is properly initialized
2. Check environment-specific configuration
3. Run validation script locally to debug:
   ```bash
   python scripts/validate_diana_character_consistency.py --mode mvp --verbose
   ```

#### Issue: Performance degradation

**Solution**:
1. Profile validation with timing:
   ```python
   import time
   start = time.time()
   result = await validator.validate_text(content)
   print(f"Validation took: {time.time() - start:.3f}s")
   ```
2. Use batch validation for multiple items
3. Consider caching for repeated validations

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run validation with full details
result = await validator.validate_text(content, context="narrative_fragment")
```

### Validation Result Analysis

```python
# Detailed result analysis
print(f"Overall Score: {result.overall_score}/100")
print(f"Meets Threshold: {result.meets_threshold}")
print(f"Trait Scores:")
for trait, score in result.trait_scores.items():
    print(f"  {trait.value}: {score}/25")
print(f"Violations: {result.violations}")
print(f"Recommendations: {result.recommendations}")
```

## API Reference

### CharacterValidationResult

```python
@dataclass
class CharacterValidationResult:
    overall_score: float           # 0-100 overall consistency score
    trait_scores: Dict[DianaPersonalityTrait, float]  # Individual trait scores (0-25 each)
    violations: List[str]          # List of character consistency violations
    recommendations: List[str]     # Suggestions for improvement
    meets_threshold: bool          # True if score ≥ threshold (95.0)
```

### DianaPersonalityTrait Enum

```python
class DianaPersonalityTrait(Enum):
    MYSTERIOUS = "mysterious"
    SEDUCTIVE = "seductive" 
    EMOTIONALLY_COMPLEX = "emotionally_complex"
    INTELLECTUALLY_ENGAGING = "intellectually_engaging"
```

### Validation Contexts

- `"narrative_fragment"` - Story content validation
- `"menu_response"` - Menu and UI text validation
- `"error_message"` - Error message validation
- `"notification"` - Notification text validation
- `"general"` - General content validation

## Conclusion

The Diana Character Consistency Validation Framework is essential for maintaining the quality and appeal of Diana Bot. By ensuring >95% character consistency across all interactions, we guarantee that users experience the mysterious, seductive, and emotionally engaging Diana that makes the bot compelling.

**Key Success Metrics**:
- ✅ >95% consistency score for all production content
- ✅ Automated validation in CI/CD pipeline
- ✅ Comprehensive test coverage (>90%)
- ✅ Performance requirements met
- ✅ Zero character-breaking content in production

For questions or support, refer to the test files for examples and best practices.