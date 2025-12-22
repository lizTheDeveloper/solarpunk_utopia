## Description

<!-- Describe what this PR does and why -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Architecture Constraints Checklist

This PR complies with our [Architecture Constraints](../openspec/ARCHITECTURE_CONSTRAINTS.md):

- [ ] **Old phones**: Works on Android 8+, 2GB RAM (no heavy frameworks)
- [ ] **Fully distributed**: No central server dependency
- [ ] **Works offline**: Functions without internet (mesh sync)
- [ ] **No big tech**: No OAuth, cloud storage, or platform dependencies
- [ ] **Seizure resistant**: Compartmentalized data, auto-deletion
- [ ] **Understandable**: Clear UI, no technical jargon
- [ ] **No surveillance capitalism**: No individual tracking, no gamification
- [ ] **Harm reduction**: Graceful degradation, limited blast radius

## Testing Checklist

- [ ] All existing tests pass locally
- [ ] New tests added for new functionality
- [ ] E2E tests added/updated if user-facing flow changed
- [ ] Tests follow existing patterns (see tests/e2e/README.md)
- [ ] No placeholders or mock implementations in production code

## Test Results

<!-- Paste test output or link to CI run -->

```
# Example:
pytest tests/e2e/ -v
# ... test output ...
```

## Related Issues

<!-- Link to issues this PR addresses -->

Closes #
Related to #

## Screenshots (if UI changes)

<!-- Add screenshots for UI changes -->

## Security Considerations

<!-- Does this PR touch security-critical code? -->

- [ ] Panic features / duress codes
- [ ] Web of Trust / vouching
- [ ] Sanctuary network / high-trust resources
- [ ] Encryption / key management
- [ ] DTN bundle propagation
- [ ] None - not security-critical

## Deployment Notes

<!-- Any special steps needed for deployment? -->

- [ ] Database migration required
- [ ] Environment variables added/changed
- [ ] APK rebuild required
- [ ] No special deployment steps

## Reviewer Checklist

For reviewers:

- [ ] Code follows project style and conventions
- [ ] Tests are comprehensive and meaningful
- [ ] No hardcoded values or magic numbers
- [ ] Error handling is appropriate
- [ ] Architecture constraints verified
- [ ] Security implications considered
- [ ] Documentation updated if needed

---

**Workshop Readiness**: Lives depend on these systems working correctly. If you're touching safety-critical flows (rapid response, sanctuary, panic features), double-check your tests.
