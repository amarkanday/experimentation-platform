# EP-010 Phase 4 Execution Plan: Feature Flag Lambda with Multi-Claude Workflow

## Overview

Build the Feature Flag Lambda using Phase 4 multi-Claude patterns to achieve:
- **3x faster development** - Parallel planning, implementation, and testing
- **Higher quality** - Dedicated Claudes for writing, reviewing, and testing
- **TDD compliance** - Maintain the successful test-first approach from Phases 1-3

---

## Multi-Claude Workflow Strategy

### Claude Instances (5 Terminals)

```
┌─────────────────────────────────────────────────────────────┐
│ Terminal 1: PLANNER Claude (Main Worktree)                  │
│ - Reads prior phases, creates detailed plan                 │
│ - Writes plan to .claude/scratchpads/ep010-phase4-plan.md  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Terminal 2: IMPLEMENTER Claude (EP-010 Worktree)            │
│ - Reads plan, writes tests first (TDD)                      │
│ - Implements Lambda handler and core logic                  │
│ - Writes to .claude/scratchpads/implementation-log.md       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Terminal 3: TESTER Claude (EP-010 Worktree)                 │
│ - Runs tests continuously                                   │
│ - Reports failures to scratchpad                            │
│ - Validates TDD compliance                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Terminal 4: REVIEWER Claude (Fresh Context)                 │
│ - Reviews code for performance, security, patterns          │
│ - Compares with Phases 1-3 consistency                      │
│ - Writes feedback to .claude/scratchpads/review.md          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Terminal 5: REFACTORER Claude (EP-010 Worktree)             │
│ - Reads review feedback                                     │
│ - Applies improvements                                      │
│ - Runs final validation                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Execution Steps

### Phase 1: Planning (Terminal 1 - PLANNER Claude)

**Goal**: Create comprehensive plan based on Phases 1-3 patterns

```bash
# Stay in main worktree
cd /Users/ashishmarkanday/github/experimentation-platform

# Start fresh Claude
claude
```

**Prompt for PLANNER Claude**:
```
I need to plan EP-010 Phase 4: Feature Flag Lambda implementation.

Context:
- Phase 1: Event Processor Lambda (completed)
- Phase 2: Assignment Lambda Days 1-2 (completed)
- Phase 3: Assignment Lambda complete (completed)
- Phase 4: Feature Flag Lambda (THIS TASK)

Requirements:
1. Read prior Lambda implementations to understand patterns
2. Use TDD approach (test-first) like previous phases
3. High-volume, low-latency feature flag evaluation
4. Real-time Lambda service

Tasks:
1. Search for Event Processor Lambda and Assignment Lambda code
2. Identify common patterns (structure, testing, error handling)
3. Create detailed 8-day implementation plan following TDD
4. Write plan to .claude/scratchpads/ep010-phase4-plan.md

Include in plan:
- Day 1-2: Core feature flag evaluation logic + tests
- Day 3-4: Lambda handler and integration + tests
- Day 5-6: Performance optimization and caching + tests
- Day 7-8: Error handling, monitoring, final validation

Start by exploring existing Lambda code in the repository.
```

**Expected Output**: Detailed plan file at `.claude/scratchpads/ep010-phase4-plan.md`

---

### Phase 2: Setup Parallel Environment (Terminal 2)

**Goal**: Create isolated worktree for implementation

```bash
# Create dedicated worktree for EP-010 Phase 4
./scripts/worktree-manager.sh create ep010-phase4-feature-flag-lambda

# Verify creation
./scripts/worktree-manager.sh status

# Navigate to new worktree
cd ../experimentation-platform-worktrees/ep010-phase4-feature-flag-lambda

# Verify we're on the right branch
git branch --show-current
# Expected: feature/ep010-phase4-feature-flag-lambda
```

---

### Phase 3: Implementation - Day 1-2 (Terminal 2 - IMPLEMENTER Claude)

**Goal**: Write tests first, then implement core evaluation logic

```bash
# In worktree directory
cd ../experimentation-platform-worktrees/ep010-phase4-feature-flag-lambda

# Start fresh Claude
claude
```

**Prompt for IMPLEMENTER Claude**:
```
I'm implementing EP-010 Phase 4: Feature Flag Lambda (Days 1-2).

Setup:
1. Read the plan from .claude/scratchpads/ep010-phase4-plan.md
2. Read existing Event Processor and Assignment Lambda code for patterns

TDD Approach (Days 1-2):
1. FIRST: Write comprehensive tests for feature flag evaluation
   - Test file: lambda/feature_flags/tests/unit/test_feature_flag_evaluator.py
   - Cover: basic evaluation, targeting rules, rollout percentages
   - Cover: user context, attribute matching, default values

2. SECOND: Implement the evaluator to pass tests
   - Implementation: lambda/feature_flags/src/evaluator.py
   - Use rules engine from backend (import if possible)
   - Handle edge cases identified in tests

3. Log progress to .claude/scratchpads/implementation-log.md

Start with test file creation. Do NOT implement logic until tests exist.
```

---

### Phase 4: Continuous Testing (Terminal 3 - TESTER Claude)

**Goal**: Run tests continuously, report failures

```bash
# In worktree directory
cd ../experimentation-platform-worktrees/ep010-phase4-feature-flag-lambda

# Start fresh Claude
/clear
claude
```

**Prompt for TESTER Claude**:
```
I'm the TESTER for EP-010 Phase 4. My job is continuous validation.

Setup:
1. Activate virtualenv: source venv/bin/activate
2. Set test environment: export APP_ENV=test TESTING=true

Continuous Testing Loop:
1. Watch for new test files in lambda/feature_flags/tests/
2. Run tests: python -m pytest lambda/feature_flags/tests/unit/ -v
3. Report results to .claude/scratchpads/test-results.md with:
   - Timestamp
   - Pass/fail counts
   - Failed test details with error messages
   - Suggestions for fixes

4. Wait for changes, then re-run (manual trigger with "run tests again")

TDD Validation:
- Verify tests exist BEFORE implementation
- Track test coverage metrics
- Flag any untested code paths

Start by running current tests and establishing baseline.
```

---

### Phase 5: Implementation - Day 3-4 (Terminal 2 - IMPLEMENTER Claude)

**Continue in same Terminal 2**

**Prompt**:
```
Continue EP-010 Phase 4: Days 3-4 (Lambda Handler)

Read:
1. Implementation log from Days 1-2
2. Test results from TESTER Claude
3. Plan for Days 3-4

TDD Approach (Days 3-4):
1. FIRST: Write Lambda handler tests
   - Test file: lambda/feature_flags/tests/unit/test_handler.py
   - Cover: event parsing, evaluation flow, response format
   - Cover: error scenarios, invalid requests, timeouts

2. SECOND: Implement Lambda handler
   - File: lambda/feature_flags/src/handler.py
   - Integration with evaluator from Days 1-2
   - Event validation and error handling
   - Response formatting (API Gateway compatible)

3. THIRD: Integration tests
   - Test file: lambda/feature_flags/tests/integration/test_end_to_end.py
   - Full event → response flow
   - Database integration (if needed)

Update implementation log with progress.
```

---

### Phase 6: Code Review (Terminal 4 - REVIEWER Claude)

**Goal**: Fresh-context review for quality and consistency

```bash
# NEW terminal - do NOT navigate to worktree
# Stay in main directory for comparison
cd /Users/ashishmarkanday/github/experimentation-platform

# Start completely fresh Claude
/clear
claude
```

**Prompt for REVIEWER Claude**:
```
I'm reviewing EP-010 Phase 4 implementation (Days 1-4 complete).

My role: Fresh-context code review (I have NOT written this code).

Review Tasks:
1. Read implementation from worktree:
   - lambda/feature_flags/src/evaluator.py
   - lambda/feature_flags/src/handler.py
   - lambda/feature_flags/tests/unit/test_*.py

2. Compare with prior Lambda implementations:
   - lambda/event_processor/ (Phase 1)
   - lambda/assignment/ (Phases 2-3)

3. Check for:
   - **Consistency**: Same patterns as Phases 1-3?
   - **Performance**: Efficient for high-volume, low-latency?
   - **Security**: Input validation, injection prevention?
   - **Error Handling**: Comprehensive coverage?
   - **Testing**: TDD compliance, good coverage?
   - **Code Quality**: Clean, maintainable, documented?

4. Write detailed review to .claude/scratchpads/review.md with:
   - Issues found (categorized by severity)
   - Specific file:line references
   - Suggested improvements
   - What's done well (positive feedback)

Start by reading existing Lambda code to understand expected patterns.
```

---

### Phase 7: Apply Feedback (Terminal 5 - REFACTORER Claude)

**Goal**: Apply review feedback while maintaining TDD

```bash
# In worktree directory
cd ../experimentation-platform-worktrees/ep010-phase4-feature-flag-lambda

# Start fresh Claude
/clear
claude
```

**Prompt for REFACTORER Claude**:
```
I'm applying review feedback for EP-010 Phase 4.

Process:
1. Read review feedback: .claude/scratchpads/review.md
2. Prioritize critical and high-severity issues
3. For each issue:
   a. Update tests FIRST if behavior changes
   b. Apply the fix
   c. Run tests to verify
   d. Document fix in .claude/scratchpads/refactoring-log.md

4. After all fixes:
   - Run full test suite
   - Run linter: ./scripts/claude-lint.sh lambda/feature_flags/
   - Update implementation log

Maintain TDD: If review suggests new functionality, write test first.

Start by reading and categorizing the review feedback.
```

---

### Phase 8: Performance Optimization (Terminal 2 - IMPLEMENTER Claude)

**Continue Days 5-6 in Terminal 2**

**Prompt**:
```
Continue EP-010 Phase 4: Days 5-6 (Performance & Caching)

Read refactoring log and current state.

TDD Approach (Days 5-6):
1. FIRST: Write performance tests
   - Test file: lambda/feature_flags/tests/performance/test_throughput.py
   - Target: > 1000 evaluations/second
   - Target: < 50ms p95 latency
   - Batch evaluation support

2. SECOND: Implement optimizations
   - Caching layer (Redis integration?)
   - Rule compilation caching
   - Batch evaluation support
   - Connection pooling

3. THIRD: Benchmark and validate
   - Run performance tests
   - Compare with Assignment Lambda performance
   - Document results

Update implementation log with performance metrics.
```

---

### Phase 9: Final Validation (Terminal 3 - TESTER Claude)

**Goal**: Comprehensive final testing

```bash
# Same TESTER terminal
# In worktree
```

**Prompt**:
```
Final validation for EP-010 Phase 4 (Days 7-8).

Comprehensive Test Suite:
1. Run all unit tests:
   python -m pytest lambda/feature_flags/tests/unit/ -v --cov

2. Run all integration tests:
   python -m pytest lambda/feature_flags/tests/integration/ -v

3. Run performance tests:
   python -m pytest lambda/feature_flags/tests/performance/ -v

4. Validate TDD compliance:
   - Check test coverage (target: > 80%)
   - Verify all code paths tested
   - Check for untested edge cases

5. Create final report: .claude/scratchpads/final-validation.md
   - Test counts (unit, integration, performance)
   - Coverage metrics
   - Performance benchmarks
   - Any remaining issues
   - Sign-off checklist

Run comprehensive validation now.
```

---

### Phase 10: Final Review & Merge (Terminal 4 - REVIEWER Claude)

**Goal**: Final approval before merge

```bash
# Same REVIEWER terminal (fresh context)
```

**Prompt**:
```
Final review for EP-010 Phase 4 before merge.

Pre-Merge Checklist:
1. Read final validation report
2. Review all implementation files
3. Compare with Phase 1-3 quality standards
4. Check for:
   - [ ] All tests passing
   - [ ] Coverage > 80%
   - [ ] Performance targets met
   - [ ] Documentation complete
   - [ ] No security vulnerabilities
   - [ ] Consistent with prior phases
   - [ ] Error handling comprehensive
   - [ ] Monitoring/logging in place

5. Run linter one more time:
   ./scripts/claude-lint.sh lambda/feature_flags/

6. Write approval/concerns to .claude/scratchpads/final-review.md

Provide GO/NO-GO decision for merge.
```

---

### Phase 11: Commit & PR (Terminal 2 - IMPLEMENTER Claude)

**Goal**: Clean commit and PR creation

```bash
# In worktree
cd ../experimentation-platform-worktrees/ep010-phase4-feature-flag-lambda
```

**Prompt**:
```
Create commit and PR for EP-010 Phase 4.

Process:
1. Review all changes: git status, git diff
2. Stage files: git add lambda/feature_flags/
3. Create detailed commit following pattern from Phases 1-3
4. Push to remote
5. Create PR with:
   - Summary of implementation
   - Test coverage metrics
   - Performance benchmarks
   - Link to final validation report
   - Comparison with Phases 1-3

Commit message format:
EP-010 Phase 4: Feature Flag Lambda Implementation (Days 1-8)

Implemented high-performance feature flag evaluation Lambda with TDD:

**Core Components**:
- Feature flag evaluator with targeting rules
- Lambda handler with API Gateway integration
- Caching layer for low-latency responses
- Comprehensive error handling and monitoring

**Test Coverage**:
- Unit tests: X tests, Y% coverage
- Integration tests: Z tests
- Performance tests: Target metrics met

**Performance Metrics**:
- Throughput: X evaluations/second
- Latency: p50=Xms, p95=Yms, p99=Zms

**TDD Compliance**:
- All functionality test-first
- X tests written before implementation
- Full test suite passing

Follows patterns from Event Processor (Phase 1) and Assignment Lambda (Phases 2-3).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### Phase 12: Cleanup (Terminal - Any)

**Goal**: Remove worktree and scratchpads

```bash
# Back to main directory
cd /Users/ashishmarkanday/github/experimentation-platform

# After PR is merged, cleanup worktree
./scripts/worktree-manager.sh cleanup ep010-phase4-feature-flag-lambda

# Archive scratchpads
mkdir -p .claude/archive/ep010-phase4
mv .claude/scratchpads/ep010-* .claude/archive/ep010-phase4/
mv .claude/scratchpads/*-log.md .claude/archive/ep010-phase4/
mv .claude/scratchpads/review.md .claude/archive/ep010-phase4/
mv .claude/scratchpads/final-*.md .claude/archive/ep010-phase4/

# Commit archive
git add .claude/archive/ep010-phase4/
git commit -m "Archive EP-010 Phase 4 scratchpads"
git push origin main
```

---

## Communication Between Claudes

### Scratchpad Files (in `.claude/scratchpads/`)

```
ep010-phase4-plan.md          ← PLANNER writes
implementation-log.md          ← IMPLEMENTER writes (Days 1-8)
test-results.md               ← TESTER writes (continuous)
review.md                     ← REVIEWER writes (after Days 1-4)
refactoring-log.md            ← REFACTORER writes
final-validation.md           ← TESTER writes (final)
final-review.md               ← REVIEWER writes (final)
```

### Read/Write Matrix

| Claude        | Reads                                    | Writes                   |
|---------------|------------------------------------------|--------------------------|
| PLANNER       | Prior Lambda code                        | plan.md                  |
| IMPLEMENTER   | plan.md, test-results.md, review.md      | implementation-log.md    |
| TESTER        | All test files                           | test-results.md, final-validation.md |
| REVIEWER      | All implementation files, prior Lambdas  | review.md, final-review.md |
| REFACTORER    | review.md, implementation-log.md         | refactoring-log.md       |

---

## Benefits of This Approach

### Speed
- ✅ **3x faster**: 5 Claudes working in parallel vs 1 sequential
- ✅ **No context pollution**: Each Claude focused on one role
- ✅ **Continuous testing**: Immediate feedback on failures

### Quality
- ✅ **Fresh review context**: Reviewer hasn't written the code
- ✅ **TDD enforced**: Dedicated tester validates test-first approach
- ✅ **Consistency**: Reviewer compares with Phases 1-3
- ✅ **Multiple perspectives**: Planner, implementer, tester, reviewer

### Process
- ✅ **Isolated environment**: Worktree doesn't affect main branch
- ✅ **Documented decisions**: All scratchpads archived
- ✅ **Automated quality**: Linter runs before merge
- ✅ **Clear handoffs**: Each Claude knows exactly what to read/write

---

## Timeline Estimate

### Traditional Single-Claude Approach
- Days 1-8: Implementation (sequential)
- 8 days × 6 hours = **48 hours**

### Multi-Claude Phase 4 Approach
- Planning: 1 hour (PLANNER)
- Days 1-2: 4 hours (IMPLEMENTER + TESTER parallel)
- Days 3-4: 4 hours (IMPLEMENTER + TESTER parallel)
- Review: 2 hours (REVIEWER, independent)
- Refactoring: 2 hours (REFACTORER + TESTER parallel)
- Days 5-6: 4 hours (IMPLEMENTER + TESTER parallel)
- Final validation: 2 hours (TESTER + REVIEWER parallel)
- Commit/PR: 1 hour
- **Total: ~20 hours** (2.4x faster)

---

## Success Metrics

Track these throughout implementation:

- [ ] **Test Coverage**: > 80% for all Lambda code
- [ ] **Performance**: > 1000 evaluations/second, < 50ms p95 latency
- [ ] **TDD Compliance**: 100% of functionality test-first
- [ ] **Code Quality**: Linter reports 0 critical issues
- [ ] **Consistency**: Matches Phases 1-3 patterns
- [ ] **Documentation**: All public APIs documented
- [ ] **Error Handling**: All error scenarios covered
- [ ] **Review Approval**: GO decision from REVIEWER Claude

---

## Emergency Procedures

### If Worktree Gets Corrupted
```bash
# Prune and recreate
git worktree prune
./scripts/worktree-manager.sh cleanup ep010-phase4-feature-flag-lambda
./scripts/worktree-manager.sh create ep010-phase4-feature-flag-lambda
```

### If Tests Keep Failing
```bash
# TESTER Claude creates detailed failure report
# IMPLEMENTER reads report and fixes issues
# Don't proceed to next phase until tests pass
```

### If Review Finds Critical Issues
```bash
# REFACTORER addresses all critical issues
# TESTER re-runs full suite
# REVIEWER does second review
# Only merge after clean review
```

---

## Ready to Start?

**Step 1**: Create worktree
```bash
./scripts/worktree-manager.sh create ep010-phase4-feature-flag-lambda
```

**Step 2**: Open 5 terminals and assign roles

**Step 3**: Start with PLANNER Claude in Terminal 1

**Step 4**: Follow this plan sequentially through all phases

---

**Expected Outcome**: Complete, high-quality Feature Flag Lambda implementation in ~20 hours with superior quality through multi-Claude collaboration.
