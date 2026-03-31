---
name: code-reviewer
description: "Use this skill whenever the user wants a code review, wants to review a pull request, needs help improving code quality, or asks for feedback on their code. Triggers include: any mention of 'code review', 'review my code', 'review this PR', 'pull request review', 'code quality', 'code smell', 'refactor', 'clean code', 'best practices', 'anti-pattern', 'code feedback', 'improve this code', 'what's wrong with this', 'is this good code', 'potential bugs', 'edge cases', 'error handling', 'naming conventions', 'code readability', 'SOLID principles', 'DRY', 'KISS', 'design patterns', 'tech debt assessment', or any request to look at code and provide constructive feedback. Also use when reviewing diffs, comparing implementations, auditing code for quality before merge, or when the user pastes code and asks 'what do you think?'. If someone shares code and seems to want feedback or improvement suggestions, use this skill."
---

# Code Reviewer Skill

## Overview

Systematic, constructive code review methodology. Covers what to look for, how to prioritize findings, language-specific patterns, and how to deliver feedback effectively. Use this when users request code reviews, pull request feedback, code quality assessments, or general code improvement suggestions.

## Review Process

### Before Reading Code

- **Understand context**: What problem does this code solve? Read the PR description or task.
- **Check scope**: Is this a bug fix, new feature, refactor, or performance improvement?
- **Set expectations**: A 10-line bug fix needs different review depth than a 500-line feature.

### Review Order (Most to Least Important)

1. **Correctness**: Does it actually work? Does it solve the stated problem?
2. **Security**: Vulnerabilities? Input validation? Auth checks? Injection risks?
3. **Edge cases**: Empty input, null values, huge data, concurrent access, boundary conditions?
4. **Error handling**: Errors caught, logged, handled gracefully? No silent failures?
5. **Architecture**: Is the approach sound? Right place for this code? Proper separation of concerns?
6. **Performance**: Obvious bottlenecks? N+1 queries? Unnecessary allocations? Missing indexes?
7. **Readability**: Can someone unfamiliar understand this in 5 minutes? Clear naming? Comments where needed?
8. **Style**: Consistent with codebase conventions? Formatting? Import organization?

### What NOT to Nitpick

- Formatting issues (linters/formatters should handle this)
- Personal style preferences that don't affect quality
- Minor naming alternatives where both are clear
- Approach differences when the chosen approach works fine
- Save review capital for things that matter

## Correctness Checks

### Logic Errors

- **Off-by-one errors**: Check loop bounds and range endpoints
- **Comparison operators**: Verify < vs <=, == vs ===, > vs >=
- **Short-circuit evaluation**: Ensure side effects occur in correct order
- **Null/undefined chains**: `a?.b?.c` or check before accessing `a.b.c`
- **Floating point comparison**: Never use == for floats; use epsilon comparisons
- **Integer overflow**: Check arithmetic in languages without automatic bounds checking

Example: `for (let i = 0; i <= array.length; i++)` accesses array[array.length] which is undefined.

### State Management

- **Race conditions**: Concurrent code accessing shared mutable state without synchronization
- **Stale closures**: Variables captured at wrong time in loops or async code
- **Memory leaks**: Event listeners, subscriptions, timers not cleaned up
- **Resource leaks**: Files, database connections, sockets not closed in error paths

Example: Event listener added in useEffect but never removed = memory leak on unmount.

### Data Flow

- **Validate external input**: User input, API responses, file content, environment variables
- **Check transformations**: map/filter/reduce producing expected shape
- **Verify consistency**: When updating related data (A and B), update together atomically

## Security Review Checklist

### Input Handling

- **SQL injection**: Only parameterized queries, never string interpolation. `cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))`
- **XSS**: Sanitize user content before HTML rendering; use framework auto-escaping
- **Command injection**: Never pass user input to shell; use subprocess with array args, not strings
- **Path traversal**: Validate file paths, reject `../`, use allowlists
- **Deserialization**: Never deserialize untrusted data (pickle, eval, unsafe YAML)

### Authentication & Authorization

- Every endpoint enforces auth (no accidental public routes)
- Authorization at resource level, not just route level
- Tokens/sessions expire appropriately
- Sensitive operations require re-authentication or confirmation

### Secrets

- No hardcoded credentials, API keys, tokens, or secrets in code
- Secrets loaded from environment variables or secret management systems
- .env files in .gitignore; .env.example committed without secrets
- Logs don't leak sensitive data (mask passwords, tokens, PII)

## Error Handling Review

### Patterns to Flag

- **Empty catch blocks**: `catch (e) {}` silently swallows errors
- **Generic catches**: Catching all exceptions when specific types should be handled differently
- **Error strings instead of types**: `if (error.message.includes("not found"))` is brittle
- **Missing propagation**: Catching errors but not re-throwing or handling
- **No cleanup on error**: Resources opened but not closed on exception

### Good Error Handling

- Catch specific error types; let unexpected errors bubble up
- Log with context (what operation, what input, correlation ID)
- Return meaningful error messages to callers without leaking internals
- Use finally/defer/try-finally for cleanup regardless of success/failure
- Fail fast: validate early, return early, don't propagate bad data

## Language-Specific Patterns

### Python

- Type hints present and accurate in function signatures and returns
- Files, connections, locks use `with` statement (context managers)
- f-strings preferred over .format() for readability (Python 3.6+)
- Nested list comprehensions difficult to read? Use a loop instead
- Mutable default arguments: `def f(items=[])` is a classic bug; use `None` and check
- Imports: stdlib → third-party → local, alphabetical within groups

### JavaScript/TypeScript

- TypeScript strict mode enabled; any `any` types that could be narrowed?
- Optional chaining `a?.b?.c` instead of nested null checks
- All promises awaited or .catch()'d; no unhandled rejections
- Strict equality `===` vs loose `==` (use === unless you have a specific reason)
- Closure scope: variables captured as expected? (common issue in loops)
- Module imports tree-shakeable? Importing entire library for one function?

### Go

- Every error checked; no `_ = err` discards without reason
- Resources: defer close immediately after open
- Goroutine leaks: every goroutine has an exit path
- Receiver types consistent (pointer vs value) for interface compliance

### Bash/Shell

- Variables quoted: `"$var"` not `$var` to handle spaces/special chars
- Error handling: `set -euo pipefail` at the top of scripts
- Portability: bash-specific features vs POSIX sh compatibility
- Meaningful exit codes returned from functions

## Performance Review

### Database Queries

- **N+1 queries**: Fetching related records in a loop instead of a join/eager load
- **Missing indexes**: Queries filtering/sorting on non-indexed columns
- **SELECT \***: Fetching all columns when you need three
- **Unbounded queries**: No LIMIT on potentially large result sets
- **Connection pool exhaustion**: Connections not returned to pool

### General Performance

- Unnecessary work in loops; move invariants outside
- Repeated computation; cache or memoize if called multiple times
- Large objects copied instead of passed by reference
- Synchronous I/O blocking event loop (Node.js, Python asyncio)
- Missing pagination for list endpoints

## Delivering Feedback

### Tone

- Be constructive, not critical; suggest improvements, don't just point out flaws
- Ask questions instead of commands: "What if we..." vs "You should..."
- Acknowledge good work; point out things done well, not just problems
- Distinguish blocking from suggestions: prefix with [BLOCKING], [SUGGESTION], [NIT]

### Feedback Format

```
[BLOCKING] SQL injection risk in user search
Line 42: User input interpolated directly into SQL query.
Use parameterized queries instead:
- Current: f"SELECT * FROM users WHERE name = '{name}'"
- Suggested: cursor.execute("SELECT * FROM users WHERE name = %s", (name,))

[SUGGESTION] Extract validation logic
Lines 15-35 validate users; same logic repeated in create_user().
Extract to shared validate_user_input() to reduce duplication.

[NIT] Naming: data → user_profile
More descriptive since this dict contains user profile data.
```

### Prioritization

- A review with 30 comments is overwhelming; group and prioritize
- Lead with the 2-3 most important issues
- Batch minor issues: "a few naming suggestions throughout:"
- If the PR is fundamentally flawed in approach, say so early; don't nitpick details on code that needs rewriting

## Quick Review Checklist

Walk through mentally:
- [ ] Does it solve the stated problem?
- [ ] Are there tests for new/changed behavior?
- [ ] Edge cases handled (null, empty, large, concurrent)?
- [ ] Errors caught, logged, handled gracefully?
- [ ] Input validated and sanitized?
- [ ] No hardcoded secrets or credentials?
- [ ] No obvious performance issues (N+1, unbounded queries, memory leaks)?
- [ ] Would I understand this code in 6 months?
- [ ] Follows existing codebase patterns and conventions?
