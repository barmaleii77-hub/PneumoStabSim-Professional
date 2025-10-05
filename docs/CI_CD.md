# CI/CD Configuration for PneumoStabSim

This document describes the Continuous Integration and Continuous Deployment (CI/CD) setup for the project.

## ?? Automated Workflows

### GitHub Actions

The project uses GitHub Actions for automated testing and quality checks.

**Workflow File:** `.github/workflows/ci-cd.yml`

## ?? Test Pipeline

### On Every Push/PR

1. **Unit Tests**
   - Run on Ubuntu, Windows, macOS
   - Python versions: 3.11, 3.12, 3.13
   - Coverage reports uploaded to Codecov

2. **Integration Tests**
   - Test component interactions
   - Verify Python?QML communication

3. **Code Quality Checks**
   - **flake8:** Code linting
   - **black:** Code formatting
   - **mypy:** Type checking

### Test Matrix

```
OS: [Ubuntu, Windows, macOS]  
Python: [3.11, 3.12, 3.13]  
Total Combinations: 9
```

## ?? Coverage Reports

- **Target Coverage:** 80%+
- **Current Coverage:** Will be tracked via Codecov
- **Reports:** Available in PR comments and workflow artifacts

## ?? Local Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Run Specific Test Suite
```bash
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/system/         # System tests
```

### Run Quality Checks
```bash
flake8 src/
black --check src/
mypy src/
```

## ?? Deployment Pipeline

### On Master Branch Push

1. ? All tests pass
2. ? Code quality checks pass
3. ? Documentation builds
4. ??? Tag created (manual release)

### Release Process

1. Merge to `master` branch
2. CI/CD runs full test suite
3. If all passes, create release tag
4. Build distribution packages
5. Update documentation

## ?? Branch Protection

### Master Branch

- ? Require PR reviews
- ? Require status checks to pass
- ? Require up-to-date branches
- ? Include administrators

### Develop Branch

- ? Require status checks to pass
- ?? PR reviews recommended

## ?? Troubleshooting CI/CD

### Tests Failing Locally But Pass in CI

- Check Python version
- Verify all dependencies installed
- Check environment variables

### Tests Pass Locally But Fail in CI

- Different OS/Python version
- Missing test dependencies
- Environment-specific issues

### Coverage Below Target

- Add more unit tests
- Test edge cases
- Remove unused code

## ?? Dependencies Management

### Production Dependencies
```
requirements.txt
```

### Development Dependencies
```
requirements-dev.txt
```

### Automatic Dependency Updates

- Dependabot configured (future)
- Weekly security checks
- Auto-update minor versions

## ?? Security Scanning

### Planned Integrations

- **Bandit:** Python security linting
- **Safety:** Dependency vulnerability checking
- **CodeQL:** Advanced code scanning

## ?? Metrics Tracking

### CI/CD Metrics

- Build success rate
- Average build time
- Test pass rate
- Coverage trends

### Quality Metrics

- Code complexity
- Technical debt
- Documentation coverage

## ?? Future Improvements

1. **Performance Benchmarks**
   - Track simulation speed
   - Monitor memory usage
   - Regression detection

2. **Visual Regression Testing**
   - Screenshot comparison
   - QML rendering tests

3. **Automated Releases**
   - Semantic versioning
   - Changelog generation
   - Package publishing

---

**Last Updated:** 2025-01-05  
**CI/CD Platform:** GitHub Actions  
**Status:** ? Configured and Ready
