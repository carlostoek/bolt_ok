# Tests for DianaBot

This directory contains tests for the DianaBot system.

## Running Tests

To run all tests:
```bash
python -m unittest discover -s tests
```

To run a specific test:
```bash
python -m unittest tests.services.test_reaction_system
```

## Test Structure

- `services/`: Tests for service components
  - `test_reaction_system.py`: Tests for the reaction system, verifying the different behavior between inline and native reactions

## Adding New Tests

When adding new tests:
1. Create a new test file in the appropriate subdirectory
2. Import the necessary modules and mock dependencies
3. Use the unittest framework to create test cases
4. Add the test to the appropriate test suite