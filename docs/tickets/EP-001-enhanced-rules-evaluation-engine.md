# EP-001: Enhanced Rules Evaluation Engine for Advanced Targeting

**Status:** 🔴 Not Started
**Priority:** 🔥 High
**Story Points:** 8
**Sprint:** Week 3-4 (Feature Flag Management)
**Assignee:** Backend Developer
**Created:** 2025-12-16
**Type:** Feature Enhancement

---

## 📋 Overview

### User Story
**As a** product manager
**I want** advanced targeting rules with high-performance evaluation
**So that** I can create sophisticated user segmentation for experiments and feature flags at scale

### Business Value
- **Capability:** Support enterprise-grade targeting scenarios
- **Performance:** Handle 100K+ evaluations/second
- **Flexibility:** Unlimited targeting complexity
- **Reliability:** 99.99% evaluation accuracy

---

## 🎯 Current State Analysis

### ✅ Already Implemented
- Basic rules engine in `backend/app/core/rules_engine.py`
- Targeting rule schemas in `backend/app/schemas/targeting_rule.py`
- Basic evaluation logic for feature flags
- Support for logical operators (AND, OR, NOT)
- Basic condition evaluation with multiple operators
- Rollout percentage support with deterministic hashing

### ❌ Missing/Needs Enhancement
- Advanced targeting scenarios (geographic, behavioral, temporal)
- Performance optimization for high-volume evaluations
- Caching layer for rule evaluation results
- Integration with experiment assignment service
- Advanced operators (regex, date ranges, array operations)
- Rule validation and testing framework
- Metrics and monitoring for rule evaluation performance

---

## 🔧 Technical Specifications

### Enhanced Operators to Implement

```python
# Current operators (basic)
class BasicOperators:
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    IN = "in"
    NOT_IN = "not_in"

# New operators to add
class AdvancedOperators:
    # Regex
    MATCH_REGEX = "match_regex"

    # Date operations
    BEFORE = "before"
    AFTER = "after"
    BETWEEN_DATES = "between_dates"

    # Array operations
    CONTAINS_ALL = "contains_all"
    CONTAINS_ANY = "contains_any"
    CONTAINS_NONE = "contains_none"

    # Numeric ranges
    BETWEEN = "between"

    # String operations
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    CONTAINS = "contains"
    CONTAINS_CASE_INSENSITIVE = "contains_i"

    # Semantic versioning
    SEMVER_EQ = "semver_eq"
    SEMVER_GT = "semver_gt"
    SEMVER_LT = "semver_lt"
```

### Architecture

```python
# Enhanced Rules Evaluation Service
class RulesEvaluationService:
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.metrics = MetricsCollector()
        self.compiled_rules_cache = {}

    async def evaluate_user_targeting(
        self,
        user_context: UserContext,
        targeting_rules: TargetingRules
    ) -> EvaluationResult:
        """
        Optimized evaluation with caching
        P99 latency target: < 10ms
        """
        # Check cache first
        cache_key = self._generate_cache_key(user_context, targeting_rules)
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            self.metrics.increment("rule_cache_hit")
            return cached_result

        # Compile rules if not cached
        compiled_rules = self._get_or_compile_rules(targeting_rules)

        # Evaluate with compiled rules
        start_time = time.time()
        result = self._evaluate_compiled_rules(user_context, compiled_rules)
        duration_ms = (time.time() - start_time) * 1000

        # Record metrics
        self.metrics.histogram("rule_evaluation_duration_ms", duration_ms)

        # Cache result (TTL: 5 minutes)
        await self.cache.set(cache_key, result, ttl=300)

        return result

    def compile_rules(self, rules: TargetingRules) -> CompiledRules:
        """
        Pre-compile rules for faster evaluation
        - Sort conditions by complexity (simple first)
        - Pre-compile regex patterns
        - Optimize boolean logic
        """
        pass
```

---

## 📝 Implementation Tasks

### Phase 1: Enhanced Operators (2 days)

- [ ] **Task 1.1:** Implement regex pattern matching
  ```python
  def evaluate_match_regex(value: str, pattern: str) -> bool:
      regex = re.compile(pattern)
      return bool(regex.match(value))
  ```

- [ ] **Task 1.2:** Add date range operations
  ```python
  def evaluate_between_dates(value: datetime, start: datetime, end: datetime) -> bool:
      return start <= value <= end
  ```

- [ ] **Task 1.3:** Support array operations
  ```python
  def evaluate_contains_all(values: List, required: List) -> bool:
      return all(item in values for item in required)
  ```

- [ ] **Task 1.4:** Add numeric range operations
- [ ] **Task 1.5:** Implement case-insensitive string operations

### Phase 2: Performance Optimization (2 days)

- [ ] **Task 2.1:** Implement rule compilation
  - Parse rules once, reuse compiled version
  - Pre-compile regex patterns
  - Optimize condition ordering

- [ ] **Task 2.2:** Add Redis caching layer
  - Cache evaluation results
  - Cache compiled rules
  - Implement cache invalidation

- [ ] **Task 2.3:** Optimize evaluation order
  - Evaluate simple conditions first
  - Short-circuit on false (AND) or true (OR)
  - Skip expensive operations when possible

- [ ] **Task 2.4:** Add batch evaluation support
  - Evaluate multiple users simultaneously
  - Share compiled rules across evaluations

### Phase 3: Advanced Targeting (2 days)

- [ ] **Task 3.1:** Geographic targeting
  - Country, region, city matching
  - IP geolocation support
  - Timezone-based rules

- [ ] **Task 3.2:** Behavioral targeting
  - User action history
  - Engagement level
  - Funnel stage

- [ ] **Task 3.3:** Temporal targeting
  - Time-of-day rules
  - Day-of-week rules
  - Date range targeting

- [ ] **Task 3.4:** Device/browser targeting
  - User-Agent parsing
  - Device type matching
  - OS version targeting

### Phase 4: Integration & Testing (3 days)

- [ ] **Task 4.1:** Integrate with assignment service
  - Share rule evaluation logic
  - Ensure consistency
  - Test integration

- [ ] **Task 4.2:** Unit tests (>95% coverage)
  - Test each operator
  - Test edge cases
  - Test performance

- [ ] **Task 4.3:** Integration tests
  - Complex rule scenarios
  - Multi-level nesting
  - Real-world use cases

- [ ] **Task 4.4:** Performance benchmarks
  - Measure P50, P95, P99 latency
  - Test with 10K, 100K evaluations
  - Compare with/without caching

### Phase 5: Monitoring & Documentation (1 day)

- [ ] **Task 5.1:** Add evaluation metrics
  - Latency tracking
  - Cache hit rate
  - Error rate
  - Complexity analysis

- [ ] **Task 5.2:** Create evaluation dashboard
  - Real-time metrics
  - Performance trends
  - Top rules by usage

- [ ] **Task 5.3:** Documentation
  - Operator reference
  - Performance guide
  - Best practices

---

## ✅ Acceptance Criteria

### Enhanced Operators
- [ ] Regex matching works correctly
- [ ] Date operations support ISO 8601 format
- [ ] Array operations handle edge cases
- [ ] Numeric ranges inclusive/exclusive options
- [ ] Case-insensitive operations work

### Performance
- [ ] Rule evaluation P99 < 10ms
- [ ] Support 100K+ evaluations/second
- [ ] Cache hit rate > 90%
- [ ] Memory usage < 100MB for compiled rules
- [ ] No memory leaks in sustained load

### Advanced Targeting
- [ ] Geographic targeting works with MaxMind GeoIP2
- [ ] Behavioral rules support 30-day history
- [ ] Temporal rules respect timezones
- [ ] Device targeting covers top 20 devices

### Integration
- [ ] Assignment service uses new engine
- [ ] Feature flag service migrated
- [ ] Backward compatible with existing rules
- [ ] Performance regression tests pass

### Monitoring
- [ ] Evaluation metrics in CloudWatch
- [ ] Dashboard created and functional
- [ ] Alerts configured for latency > 50ms P99
- [ ] Error tracking implemented

---

## ✔️ Definition of Done

- [ ] All operators implemented and tested
- [ ] Performance targets met
- [ ] Integration complete
- [ ] Unit tests > 95% coverage
- [ ] Integration tests passing
- [ ] Performance benchmarks documented
- [ ] Code reviewed
- [ ] Documentation complete
- [ ] Monitoring dashboard created
- [ ] Production deployment successful

---

## 📊 Dependencies

### Blocked By
- None

### Blocking
- EP-003: Advanced Targeting UI (needs backend API)
- EP-010: Lambda Functions (share rule logic)

### Related Tickets
- EP-002: Experiment Assignment Service Integration
- EP-004: Rule Performance Monitoring Dashboard
- EP-003: Advanced Targeting UI Components

---

## 🚨 Risks & Mitigation

**Risk:** Performance degradation with complex rules
**Mitigation:** Rule compilation, caching, optimization

**Risk:** Memory usage with large rule sets
**Mitigation:** Lazy loading, rule optimization

**Risk:** Cache invalidation complexity
**Mitigation:** TTL-based expiration, version-based invalidation

---

## 📈 Success Metrics

### Performance
- P99 latency < 10ms (target achieved)
- Throughput > 100K eval/sec (10x improvement)
- Cache hit rate > 90%

### Usage
- 50% of experiments use advanced targeting
- 80% of feature flags use targeting rules
- Zero production incidents related to rule evaluation

---

## 📚 Reference Materials

### Implementation References
- `backend/app/core/rules_engine.py` - Current implementation
- `backend/app/schemas/targeting_rule.py` - Rule schemas
- `backend/app/services/assignment_service.py` - Assignment logic

### External Resources
- [LaunchDarkly Targeting Rules](https://docs.launchdarkly.com/home/flags/targeting-rules)
- [Statsig Dynamic Config](https://docs.statsig.com/dynamic-config)
- [Optimizely Audiences](https://docs.developers.optimizely.com/experimentation/v4.0.0-full-stack/docs/define-audiences)

---

## 🧪 Test-Driven Development Plan

### TDD Approach

**Red → Green → Refactor Cycle**
1. Write failing test
2. Implement minimum code to pass
3. Refactor for performance/clarity
4. Repeat

### Current Implementation Analysis

**✅ Already Implemented Operators:**
- Basic: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`
- Collections: `in`, `not_in`
- Strings: `contains`, `not_contains`, `starts_with`, `ends_with`, `match_regex`
- Dates: `before`, `after`, `between`
- Arrays: `contains_all`, `contains_any`

**❌ Missing Operators (Need Implementation):**
- `semantic_version` - Semantic version comparison
- `geo_distance` - Geographic distance calculations
- `time_window` - Time-based targeting (business hours, etc.)
- `percentage_bucket` - Advanced bucketing beyond simple rollout
- `json_path` - JSON path extraction and comparison
- `array_length` - Array length comparison
- `contains_none` - Array contains none of elements

**🔧 Missing Features:**
- Rule compilation and caching
- Performance optimization layer
- RulesEvaluationService with metrics
- Advanced targeting contexts (geo, behavioral, temporal)

### Phase 1: Advanced Operators (Days 1-2)

#### Test Cases for Semantic Version Operator

**File:** `backend/tests/unit/core/test_rules_engine_semver.py`

```python
# Test cases to write:
1. test_semantic_version_equals()
   - "1.2.3" == "1.2.3" → True
   - "1.2.3" == "1.2.4" → False

2. test_semantic_version_greater_than()
   - "2.0.0" > "1.9.9" → True
   - "1.10.0" > "1.9.0" → True (test lexicographic)
   - "1.2.3" > "2.0.0" → False

3. test_semantic_version_less_than()
   - "1.2.3" < "2.0.0" → True
   - "1.0.0-alpha" < "1.0.0" → True

4. test_semantic_version_with_prerelease()
   - "1.0.0-beta.2" > "1.0.0-beta.1" → True
   - "1.0.0-rc.1" < "1.0.0" → True

5. test_semantic_version_invalid_format()
   - "1.2" → raises ValueError
   - "v1.2.3" → raises ValueError
```

#### Test Cases for Array Length Operator

```python
# Test cases to write:
1. test_array_length_equals()
   - [1,2,3] length == 3 → True
   - [] length == 0 → True

2. test_array_length_greater_than()
   - [1,2,3,4] length > 3 → True

3. test_array_length_between()
   - [1,2,3] length between [2, 5] → True
```

#### Test Cases for Geo Distance Operator

```python
# Test cases to write:
1. test_geo_distance_within_radius()
   - Point A within 10km of Point B → True
   - Uses Haversine formula

2. test_geo_distance_units()
   - Support km, miles, meters

3. test_geo_distance_invalid_coordinates()
   - Latitude > 90 → raises ValueError
   - Longitude > 180 → raises ValueError
```

#### Test Cases for Time Window Operator

```python
# Test cases to write:
1. test_time_window_business_hours()
   - 10:00 AM within [9:00 AM, 5:00 PM] → True
   - 8:00 PM within [9:00 AM, 5:00 PM] → False

2. test_time_window_timezone_aware()
   - Handle different timezones correctly

3. test_time_window_day_of_week()
   - Monday-Friday only
   - Weekends only
```

#### Test Cases for JSON Path Operator

```python
# Test cases to write:
1. test_json_path_simple_extraction()
   - Extract "$.user.name" from {"user": {"name": "Alice"}} → "Alice"

2. test_json_path_array_indexing()
   - Extract "$.items[0].id" → correct value

3. test_json_path_not_found()
   - Path doesn't exist → returns None or raises error
```

### Phase 2: Performance Optimization (Days 3-4)

#### Test Cases for Rule Compilation

**File:** `backend/tests/unit/services/test_rules_compilation.py`

```python
1. test_compile_simple_rule()
   - Rule compiles successfully
   - Compiled version is reusable

2. test_compile_regex_patterns()
   - Regex compiled once, reused many times
   - Performance improvement measurable

3. test_compile_nested_rules()
   - Complex nested rules compile correctly
   - Maintains logical structure

4. test_compiled_rule_equivalence()
   - Compiled rule produces same results as non-compiled
```

#### Test Cases for Caching Layer

**File:** `backend/tests/unit/services/test_rules_caching.py`

```python
1. test_cache_hit()
   - Same user + same rules → cache hit
   - Second evaluation faster than first

2. test_cache_miss()
   - Different user → cache miss
   - Evaluation performed

3. test_cache_invalidation()
   - Rules updated → cache invalidated
   - TTL expiration works

4. test_cache_key_generation()
   - Same context generates same key
   - Different context generates different key
```

#### Test Cases for Performance Benchmarks

```python
1. test_evaluation_latency_p99()
   - 10K evaluations, P99 < 10ms

2. test_throughput_100k_per_second()
   - Can handle 100K evaluations/second

3. test_memory_usage()
   - Compiled rules use < 100MB
   - No memory leaks

4. test_cache_performance_improvement()
   - Cache hit is 10x+ faster than cache miss
```

### Phase 3: Rules Evaluation Service (Days 5-6)

#### Test Cases for RulesEvaluationService

**File:** `backend/tests/unit/services/test_rules_evaluation_service.py`

```python
1. test_service_initialization()
   - Service initializes with cache
   - Metrics collector created

2. test_evaluate_with_caching()
   - First call: cache miss + evaluation
   - Second call: cache hit + fast return

3. test_metrics_collection()
   - Latency tracked
   - Cache hit/miss tracked
   - Error rate tracked

4. test_batch_evaluation()
   - Evaluate multiple users efficiently
   - Shared compiled rules

5. test_error_handling()
   - Invalid rules → graceful error
   - Missing attributes → default behavior
```

#### Test Cases for Advanced Targeting Contexts

```python
1. test_geographic_context()
   - Country, region, city detection
   - IP geolocation integration

2. test_temporal_context()
   - Time of day
   - Day of week
   - Timezone handling

3. test_behavioral_context()
   - User action history
   - Engagement level
   - Funnel stage
```

### Phase 4: Integration Tests (Days 7-8)

#### Test Cases for Complex Scenarios

**File:** `backend/tests/integration/test_rules_engine_integration.py`

```python
1. test_complex_nested_rules()
   - 3+ levels of nesting
   - Mixed AND/OR/NOT operators
   - Multiple condition types

2. test_real_world_targeting()
   - Premium users in US, active last 7 days
   - Mobile users on iOS 15+, in business hours
   - Geographic + behavioral + temporal

3. test_backward_compatibility()
   - Old rules still work
   - New operators don't break existing

4. test_assignment_service_integration()
   - Rules engine used by assignment service
   - Consistent results
```

### Phase 5: Monitoring & Documentation (Days 9-10)

#### Test Cases for Metrics Collection

```python
1. test_latency_metrics()
   - Histogram tracks P50, P95, P99

2. test_cache_metrics()
   - Hit rate calculated correctly
   - Cache size tracked

3. test_error_metrics()
   - Failed evaluations counted
   - Error types categorized
```

### Test Coverage Goals

**Target:** >95% coverage

**Critical Paths:**
- All operators: 100% coverage
- Rule evaluation logic: 100% coverage
- Caching layer: 95% coverage
- Service layer: 90% coverage

### Test File Structure

```
backend/tests/
├── unit/
│   ├── core/
│   │   ├── test_rules_engine.py (existing)
│   │   ├── test_rules_engine_semver.py (new)
│   │   ├── test_rules_engine_geo.py (new)
│   │   ├── test_rules_engine_advanced.py (new)
│   │   └── test_rule_compilation.py (new)
│   └── services/
│       ├── test_rules_evaluation_service.py (new)
│       ├── test_rules_caching.py (new)
│       └── test_rules_performance.py (new)
└── integration/
    └── test_rules_engine_integration.py (new)
```

### Performance Benchmarks to Achieve

```python
# backend/tests/performance/test_rules_benchmarks.py

1. Simple rule evaluation: < 1ms (P99)
2. Complex rule evaluation: < 5ms (P99)
3. Nested rules (3 levels): < 10ms (P99)
4. Batch evaluation (100 users): < 100ms total
5. Cache hit rate: > 90% in production simulation
6. Throughput: > 100K evaluations/second
```

### Implementation Order

**Day 1:**
1. Write tests for semantic_version operator
2. Implement semantic_version operator
3. Write tests for array_length operator
4. Implement array_length operator

**Day 2:**
1. Write tests for geo_distance operator
2. Implement geo_distance operator
3. Write tests for time_window operator
4. Implement time_window operator

**Day 3:**
1. Write tests for rule compilation
2. Implement rule compilation
3. Write performance benchmarks
4. Optimize compilation

**Day 4:**
1. Write tests for caching layer
2. Implement Redis caching
3. Write cache invalidation tests
4. Implement cache invalidation

**Day 5:**
1. Write tests for RulesEvaluationService
2. Implement service skeleton
3. Integrate compilation + caching
4. Add metrics collection

**Day 6:**
1. Write tests for advanced contexts
2. Implement geographic context
3. Implement temporal context
4. Implement behavioral context

**Day 7-8:**
1. Write integration tests
2. Test complex scenarios
3. Performance testing
4. Fix issues found

**Day 9-10:**
1. Add monitoring dashboards
2. Write documentation
3. Create operator reference
4. Final testing and validation

---

**Estimated Completion:** 10 working days (2 weeks)
**Target Sprint:** Q1 2026, Sprint 3-4
