# EP-003: Advanced Targeting UI Components

**Status:** 🔴 Not Started
**Priority:** 🟡 Medium
**Story Points:** 13
**Sprint:** Phase 4 - Frontend Development (Week 7-8)
**Assignee:** Frontend Team
**Created:** 2025-12-16
**Type:** Feature

---

## 📋 Overview

### User Story
**As a** product manager
**I want** to create complex targeting rules through an intuitive visual interface
**So that** I can easily configure advanced user segmentation without technical knowledge

### Business Value
- **Accessibility:** Enable non-technical users to create complex targeting
- **Productivity:** Reduce targeting setup time from hours to minutes
- **Accuracy:** Visual validation reduces configuration errors by 90%
- **Flexibility:** Support unlimited targeting complexity without code changes

---

## 🎯 Problem Statement

Currently, targeting rules must be configured manually through JSON/API calls, which:
1. Requires technical knowledge of rule syntax
2. Is error-prone with no real-time validation
3. Lacks preview/testing capabilities
4. Provides no visual feedback on rule complexity
5. Makes it difficult to understand existing rules

Users need a modern, intuitive UI that makes advanced targeting as easy as basic configuration.

---

## 🔧 Technical Specifications

### Component Architecture

```
src/components/targeting/
├── RuleBuilder/
│   ├── RuleBuilder.tsx          # Main orchestrator component
│   ├── RuleGroup.tsx             # Logical group (AND/OR)
│   ├── RuleCondition.tsx         # Individual condition
│   ├── RulePreview.tsx           # Live preview panel
│   └── RuleComplexity.tsx        # Complexity indicator
│
├── ConditionEditor/
│   ├── AttributeSelector.tsx     # Dropdown with autocomplete
│   ├── OperatorSelector.tsx      # Contextual operators
│   ├── ValueInput.tsx            # Smart input based on type
│   ├── DatePicker.tsx            # Temporal conditions
│   ├── MultiSelect.tsx           # Array operations
│   └── RegexBuilder.tsx          # Regex pattern helper
│
├── TargetingPreview/
│   ├── PreviewPanel.tsx          # Main preview container
│   ├── TestUsers.tsx             # Sample user testing
│   ├── RolloutCalculator.tsx    # Percentage calculator
│   ├── MetricsDisplay.tsx        # Rule performance
│   └── ConflictDetector.tsx     # Rule overlap detection
│
├── RuleLibrary/
│   ├── RuleList.tsx              # Browse saved rules
│   ├── RuleTemplates.tsx         # Common patterns
│   ├── RuleSearch.tsx            # Search & filter
│   ├── RuleVersioning.tsx        # Change tracking
│   └── RuleImportExport.tsx      # Import/export
│
└── AdvancedTargeting/
    ├── GeographicTargeting.tsx   # Map-based targeting
    ├── BehavioralTargeting.tsx   # User journey viz
    ├── DeviceTargeting.tsx       # Device/browser matrix
    ├── CustomAttributes.tsx      # Custom attr management
    └── AudienceBuilder.tsx       # A/B test audiences
```

### Key TypeScript Interfaces

```typescript
interface TargetingRules {
  operator: 'AND' | 'OR';
  conditions: Condition[];
  groups: RuleGroup[];
}

interface Condition {
  id: string;
  attribute: UserAttribute;
  operator: ConditionOperator;
  value: any;
}

interface RuleBuilderProps {
  initialRules?: TargetingRules;
  onRulesChange: (rules: TargetingRules) => void;
  availableAttributes: UserAttribute[];
  validationErrors?: ValidationError[];
}

interface TargetingPreviewProps {
  rules: TargetingRules;
  testUsers: TestUser[];
  onPreviewUpdate: (results: PreviewResult[]) => void;
}
```

---

## 📝 Implementation Tasks

### Phase 1: Core Rule Builder (4 days)

- [ ] **Task 1.1:** Create RuleBuilder component
  - Drag-and-drop interface
  - Add/remove rule groups
  - Nested group support (max 5 levels)
  - Visual hierarchy indicators

- [ ] **Task 1.2:** Implement RuleGroup component
  - AND/OR toggle
  - Group nesting
  - Collapse/expand functionality
  - Visual connectors between conditions

- [ ] **Task 1.3:** Build RuleCondition component
  - Inline editing
  - Delete with confirmation
  - Duplicate condition
  - Reorder via drag-and-drop

- [ ] **Task 1.4:** Add real-time validation
  - Syntax validation
  - Type checking
  - Required field validation
  - Error highlighting

- [ ] **Task 1.5:** Implement complexity indicator
  - Calculate rule complexity score
  - Visual gauge (simple/medium/complex)
  - Optimization suggestions
  - Performance warnings

### Phase 2: Condition Editors (3 days)

- [ ] **Task 2.1:** AttributeSelector with autocomplete
  - Search available attributes
  - Group by category
  - Show data type
  - Recent/favorites list

- [ ] **Task 2.2:** Contextual OperatorSelector
  - Filter operators by attribute type
  - Show operator descriptions
  - Common operators at top
  - Support for custom operators

- [ ] **Task 2.3:** Smart ValueInput
  - Type-aware input (string/number/boolean/date)
  - Autocomplete for enum values
  - Validation feedback
  - Multiple value support (arrays)

- [ ] **Task 2.4:** DatePicker for temporal conditions
  - Date range selection
  - Relative dates (last 7 days, etc.)
  - Time zone support
  - Calendar visualization

- [ ] **Task 2.5:** RegexBuilder helper
  - Common patterns library
  - Real-time regex validation
  - Test string input
  - Visual feedback on matches

### Phase 3: Targeting Preview (2 days)

- [ ] **Task 3.1:** Live preview panel
  - Real-time rule evaluation
  - Sample user scenarios
  - Match/no-match indicators
  - Evaluation explanation

- [ ] **Task 3.2:** Test user scenarios
  - Add custom test users
  - Import user profiles
  - Save test scenarios
  - Bulk testing (100+ users)

- [ ] **Task 3.3:** Rollout percentage calculator
  - Estimate affected users
  - Show percentage breakdown
  - Historical comparison
  - Confidence intervals

- [ ] **Task 3.4:** Rule performance metrics
  - Evaluation latency
  - Cache hit rate
  - Complexity score
  - Optimization tips

- [ ] **Task 3.5:** Conflict detection
  - Identify overlapping rules
  - Show rule intersections
  - Suggest consolidation
  - Priority management

### Phase 4: Rule Library (2 days)

- [ ] **Task 4.1:** Rule list and search
  - Browse all rules
  - Search by name/tags
  - Filter by status/type
  - Sort by usage/date

- [ ] **Task 4.2:** Rule templates
  - Pre-built common patterns
  - Industry-specific templates
  - Customizable templates
  - Template marketplace

- [ ] **Task 4.3:** Versioning and history
  - Track all changes
  - Compare versions
  - Rollback capability
  - Audit trail

- [ ] **Task 4.4:** Import/Export
  - Export as JSON
  - Import from JSON/CSV
  - Bulk operations
  - Validation on import

### Phase 5: Advanced Targeting (3 days)

- [ ] **Task 5.1:** Geographic targeting
  - Interactive map integration
  - Country/region/city selection
  - Radius-based targeting
  - IP geolocation support

- [ ] **Task 5.2:** Behavioral targeting
  - User journey visualization
  - Event-based conditions
  - Funnel stage targeting
  - Engagement scoring

- [ ] **Task 5.3:** Device/Browser targeting
  - Device type matrix
  - Browser compatibility view
  - OS version targeting
  - Screen size targeting

- [ ] **Task 5.4:** Custom attributes
  - Define custom attributes
  - Type validation
  - Default values
  - Documentation

### Phase 6: Polish & Testing (2 days)

- [ ] **Task 6.1:** Accessibility (WCAG 2.1 AA)
  - Keyboard navigation
  - Screen reader support
  - ARIA labels
  - Color contrast

- [ ] **Task 6.2:** Responsive design
  - Desktop (1920px+)
  - Laptop (1366px+)
  - Tablet (768px+)
  - Mobile (375px+)

- [ ] **Task 6.3:** Performance optimization
  - Component lazy loading
  - Virtual scrolling for large lists
  - Debounced validation
  - Optimistic updates

- [ ] **Task 6.4:** User testing
  - PM user testing
  - Non-technical user testing
  - Gather feedback
  - Iterate on UX

---

## ✅ Acceptance Criteria

### Functional Requirements

1. **Visual Rule Builder**
   - [ ] Drag-and-drop works smoothly (60fps)
   - [ ] Supports unlimited nesting (recommended max 5)
   - [ ] Real-time validation with clear error messages
   - [ ] Undo/redo functionality (10 levels)
   - [ ] Auto-save every 30 seconds

2. **Condition Editor**
   - [ ] Autocomplete works for 1000+ attributes
   - [ ] Operators update based on selected attribute type
   - [ ] Value input validates based on operator
   - [ ] Date picker supports relative and absolute dates
   - [ ] Regex builder validates patterns in real-time

3. **Targeting Preview**
   - [ ] Evaluates rules against test users in <200ms
   - [ ] Shows clear match/no-match reasons
   - [ ] Rollout calculator accurate within ±1%
   - [ ] Detects rule conflicts automatically
   - [ ] Performance metrics updated in real-time

4. **Rule Library**
   - [ ] Search returns results in <100ms
   - [ ] Templates are categorized and searchable
   - [ ] Versioning tracks all changes
   - [ ] Import/export works with valid JSON
   - [ ] Bulk operations handle 100+ rules

5. **Advanced Targeting**
   - [ ] Geographic map loads in <2 seconds
   - [ ] Behavioral journey shows last 30 days
   - [ ] Device matrix shows compatibility for top 20 devices
   - [ ] Custom attributes support all standard data types

### Performance Requirements

- [ ] Component load time < 500ms
- [ ] Rule validation < 100ms for complex rules
- [ ] Preview generation < 200ms for 1000 test users
- [ ] Memory usage < 50MB for large rule sets
- [ ] Bundle size < 200KB (gzipped)

### UX Requirements

- [ ] Intuitive for non-technical users (95% success rate in testing)
- [ ] Clear visual hierarchy
- [ ] Smooth animations (60fps)
- [ ] Helpful tooltips and guidance
- [ ] Error recovery without data loss

---

## ✔️ Definition of Done

### Implementation
- [ ] All components implemented and working
- [ ] TypeScript with strict mode
- [ ] No console errors or warnings
- [ ] All props properly typed

### Testing
- [ ] Unit tests for all components (>90% coverage)
- [ ] Integration tests for workflows
- [ ] User acceptance testing passed
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Mobile responsive testing

### Documentation
- [ ] Component documentation (Storybook)
- [ ] Usage examples
- [ ] Props documentation
- [ ] User guide for PMs

### Design & Accessibility
- [ ] Design review approved
- [ ] WCAG 2.1 AA compliance verified
- [ ] Color contrast meets standards
- [ ] Keyboard navigation works
- [ ] Screen reader compatible

### Performance
- [ ] Lighthouse score > 90
- [ ] Bundle size optimized
- [ ] Load time < 500ms
- [ ] No memory leaks

---

## 📊 Dependencies

### Blocked By
- EP-001: Advanced Rules Engine (backend API needed)

### Blocking
- None

### Related Tickets
- EP-001: Enhanced Rules Evaluation Engine
- EP-005: Rule Performance Monitoring Dashboard
- EP-006: Advanced Segmentation Analytics

---

## 🚨 Risks & Mitigation

### Risk 1: Complexity Overwhelms Users
**Impact:** High
**Probability:** Medium
**Mitigation:**
- Progressive disclosure (start simple, reveal complexity)
- Guided tours and onboarding
- Templates for common use cases
- Contextual help throughout

### Risk 2: Performance with Large Rule Sets
**Impact:** Medium
**Probability:** Medium
**Mitigation:**
- Virtual scrolling
- Lazy loading of components
- Optimize re-renders with React.memo
- Web workers for heavy computation

### Risk 3: Browser Compatibility
**Impact:** Low
**Probability:** Low
**Mitigation:**
- Target modern browsers only (last 2 versions)
- Polyfills for critical features
- Graceful degradation
- Clear browser requirements

---

## 📈 Success Metrics

### Technical Metrics
- Component load time < 500ms
- Rule validation < 100ms
- Preview generation < 200ms
- Zero accessibility violations

### User Metrics
- 95% task completion rate (user testing)
- < 2 minutes to create simple rule
- < 5 minutes to create complex rule
- 90% user satisfaction score

### Business Metrics
- 10x increase in users creating targeting rules
- 50% reduction in support tickets about targeting
- 80% of targeting done via UI (vs API)

---

## 📚 Reference Materials

### UI Libraries
- React DnD: Drag and drop
- React-Select: Advanced selects
- React-Datepicker: Date selection
- React-Map-GL: Geographic targeting

### Design Inspiration
- Segment: Audience builder
- Amplitude: Event targeting
- Optimizely: Targeting UI
- LaunchDarkly: Rule builder

---

## 🔄 Change Log

| Date       | Author | Change Description |
|------------|--------|-------------------|
| 2025-12-16 | Claude | Initial ticket creation |

---

**Estimated Completion:** 16 working days (3.2 weeks)
**Target Sprint:** Q1 2026, Sprint 7-8
