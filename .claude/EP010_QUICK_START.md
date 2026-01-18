# EP-010 Phase 4 Quick Start: Multi-Claude TDD Workflow

## 5-Minute Setup

### Step 1: Create Worktree (30 seconds)

```bash
./scripts/worktree-manager.sh create ep010-phase4-feature-flag-lambda
```

### Step 2: Open 5 Terminals

```
Terminal 1: PLANNER    → Main directory (for research)
Terminal 2: IMPLEMENTER → Worktree (for coding)
Terminal 3: TESTER     → Worktree (for testing)
Terminal 4: REVIEWER   → Main directory (for fresh review)
Terminal 5: REFACTORER → Worktree (for fixes)
```

---

## Copy-Paste Prompts

### Terminal 1: PLANNER (Start Here)

```bash
cd /Users/ashishmarkanday/github/experimentation-platform
claude
```

**Prompt**:
```
Plan EP-010 Phase 4: Feature Flag Lambda using TDD.

1. Search for existing Lambda code (event_processor, assignment)
2. Identify patterns for structure, testing, error handling
3. Create 8-day plan following TDD approach
4. Write plan to .claude/scratchpads/ep010-phase4-plan.md

Include: Days 1-2 (core logic), 3-4 (handler), 5-6 (performance), 7-8 (validation)
```

---

### Terminal 2: IMPLEMENTER (Days 1-2)

```bash
cd ../experimentation-platform-worktrees/ep010-phase4-feature-flag-lambda
claude
```

**Prompt**:
```
Implement EP-010 Phase 4 Days 1-2 (Core Evaluation Logic).

1. Read plan: .claude/scratchpads/ep010-phase4-plan.md
2. TDD: Write tests FIRST in lambda/feature_flags/tests/unit/test_evaluator.py
3. Then implement: lambda/feature_flags/src/evaluator.py
4. Log progress: .claude/scratchpads/implementation-log.md

DO NOT implement until tests exist.
```

---

### Terminal 3: TESTER (Continuous)

```bash
cd ../experimentation-platform-worktrees/ep010-phase4-feature-flag-lambda
claude
```

**Prompt**:
```
I'm the TESTER. Run continuous validation.

1. Activate venv: source venv/bin/activate
2. Set env: export APP_ENV=test TESTING=true
3. Run tests: python -m pytest lambda/feature_flags/tests/ -v
4. Report to: .claude/scratchpads/test-results.md

Include: timestamp, pass/fail counts, error details, suggestions.
```

---

### Terminal 4: REVIEWER (After Days 1-4)

```bash
cd /Users/ashishmarkanday/github/experimentation-platform
claude
```

**Prompt**:
```
Review EP-010 Phase 4 implementation (fresh context, haven't written code).

1. Read from worktree: lambda/feature_flags/src/
2. Compare with: lambda/event_processor/, lambda/assignment/
3. Check: consistency, performance, security, testing, quality
4. Write review: .claude/scratchpads/review.md (with file:line references)

Focus on issues and improvements.
```

---

### Terminal 5: REFACTORER (After Review)

```bash
cd ../experimentation-platform-worktrees/ep010-phase4-feature-flag-lambda
claude
```

**Prompt**:
```
Apply review feedback for EP-010 Phase 4.

1. Read: .claude/scratchpads/review.md
2. For each issue: update tests first, fix, verify, document
3. Log fixes: .claude/scratchpads/refactoring-log.md
4. Run: ./scripts/claude-lint.sh lambda/feature_flags/

Maintain TDD: test-first for any new functionality.
```

---

## Timeline (Days 1-8)

| Days  | Terminal 2 (IMPLEMENTER) | Terminal 3 (TESTER) | Other |
|-------|--------------------------|---------------------|-------|
| 1-2   | Core evaluation logic    | Continuous testing  | -     |
| 3-4   | Lambda handler           | Continuous testing  | -     |
| 4     | (pause)                  | -                   | T4: REVIEWER reviews |
| 5     | Apply feedback           | -                   | T5: REFACTORER fixes |
| 5-6   | Performance & caching    | Continuous testing  | -     |
| 7-8   | Error handling, docs     | Final validation    | T4: Final review |
| 8     | Commit & PR              | -                   | -     |

---

## Scratchpad Communication

| File                     | Writer      | Readers |
|--------------------------|-------------|---------|
| `ep010-phase4-plan.md`   | PLANNER     | ALL     |
| `implementation-log.md`  | IMPLEMENTER | ALL     |
| `test-results.md`        | TESTER      | IMPLEMENTER, REFACTORER |
| `review.md`              | REVIEWER    | REFACTORER |
| `refactoring-log.md`     | REFACTORER  | ALL     |
| `final-validation.md`    | TESTER      | REVIEWER |
| `final-review.md`        | REVIEWER    | IMPLEMENTER |

---

## Checkpoints

### After Days 1-2
- [ ] Tests exist for core evaluation logic
- [ ] Implementation passes all tests
- [ ] TESTER reports all green

### After Days 3-4
- [ ] Lambda handler tests exist
- [ ] Integration tests passing
- [ ] REVIEWER provides feedback

### After Refactoring
- [ ] All review issues addressed
- [ ] Tests still passing
- [ ] Linter clean

### After Days 5-6
- [ ] Performance targets met (>1000 ops/sec, <50ms p95)
- [ ] Caching implemented and tested

### Final (Days 7-8)
- [ ] Coverage > 80%
- [ ] All tests passing
- [ ] Final review GO decision
- [ ] PR created

---

## Key Commands

```bash
# Create worktree
./scripts/worktree-manager.sh create ep010-phase4-feature-flag-lambda

# List worktrees
./scripts/worktree-manager.sh status

# Run tests
source venv/bin/activate
export APP_ENV=test TESTING=true
python -m pytest lambda/feature_flags/tests/ -v --cov

# Run linter
./scripts/claude-lint.sh lambda/feature_flags/

# Cleanup when done
./scripts/worktree-manager.sh cleanup ep010-phase4-feature-flag-lambda
```

---

## Expected Results

- **Speed**: ~20 hours (vs 48 hours single-Claude)
- **Quality**: Fresh review, continuous testing, multiple perspectives
- **Coverage**: > 80% test coverage
- **Performance**: Meets high-volume, low-latency targets
- **Consistency**: Matches Phases 1-3 patterns

---

## Start Now

1. Run: `./scripts/worktree-manager.sh create ep010-phase4-feature-flag-lambda`
2. Open 5 terminals
3. Copy-paste Terminal 1 PLANNER prompt
4. Follow the plan

**Detailed guide**: See `.claude/EP010_PHASE4_EXECUTION_PLAN.md`
