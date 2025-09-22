# 📚 Daily Frontend Learning Guide (4 Weeks)

---

## Week 1: Web Fundamentals + Git

### **Day 1 – HTML Structure & Semantics**
**Resources**
- [MDN HTML Basics](https://developer.mozilla.org/en-US/docs/Learn/HTML/Introduction_to_HTML)
- [HTML5 Semantic Elements](https://developer.mozilla.org/en-US/docs/Glossary/Semantics)
- [A11y Project: Accessibility Basics](https://www.a11yproject.com/checklist/)

**Exercises**
- [ ] Create dashboard layout with `<header>`, `<nav>`, `<main>`, `<footer>`
- [ ] Build experiment creation form (text, number, date, select)
- [ ] Build data table for experiment results
- [ ] Add accessible navigation with semantic tags

**Deliverable**: Semantic HTML-only skeleton of experiment dashboard  

**Knowledge Log**
- ✅ Key Concepts Learned  
- 🛠️ Code Snippets  
- ⚡ Errors & Fixes  
- 🎯 Deliverables Completed  
- 🔍 Reflection  
- 📌 Resources for Review  

---

### **Day 2 – CSS Layouts & Responsive Design**
**Resources**
- [CSS Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [CSS Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Web.dev Responsive Design](https://web.dev/learn/design/)

**Exercises**
- [ ] Create dashboard grid layout with CSS Grid
- [ ] Build experiment cards with Flexbox
- [ ] Add mobile responsiveness with media queries
- [ ] Define CSS variables for colors/spacing

**Deliverable**: Styled, responsive dashboard  

**Knowledge Log** (same structure as Day 1)

---

### **Day 3 – JavaScript Fundamentals**
**Resources**
- [JavaScript.info: Variables & Functions](https://javascript.info/variables)
- [MDN DOM Intro](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model/Introduction)
- [MDN Events](https://developer.mozilla.org/en-US/docs/Web/Events)

**Exercises**
- [ ] Write functions to calculate experiment success rates
- [ ] Select and manipulate DOM elements (querySelector)
- [ ] Add event listeners for buttons/forms
- [ ] Create simple array of experiments and display them

**Deliverable**: Interactive experiment list (add/remove/search)  

**Knowledge Log**

---

### **Day 4 – Modern JavaScript (ES6+)**
**Resources**
- [JavaScript.info: ES6+ Features](https://javascript.info/es6)
- [MDN Async/Await](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)

**Exercises**
- [ ] Convert functions → arrow functions
- [ ] Use destructuring for experiment objects
- [ ] Build template literals for HTML snippets
- [ ] Fetch mock experiment data with async/await

**Deliverable**: API client fetching and displaying experiment data  

**Knowledge Log**

---

### **Day 5 – API Integration**
**Resources**
- [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [REST API Overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview)

**Exercises**
- [ ] Make GET/POST/PUT/DELETE calls to mock API
- [ ] Parse and render JSON responses
- [ ] Implement error handling + loading states
- [ ] Handle API authentication token (mock)

**Deliverable**: Feature flag CRUD dashboard  

**Knowledge Log**

---

### **Day 6 – Git & Collaboration**
**Resources**
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

**Exercises**
- [ ] Initialize Git repo, commit code, push to GitHub
- [ ] Create branch → make changes → open PR
- [ ] Practice merging and resolving conflicts

**Deliverable**: Week 1 project version-controlled on GitHub  

**Knowledge Log**

---

### **Day 7 – Review & Assessment**
**Checklist**
- [ ] Can build semantic HTML pages
- [ ] Can style with Flexbox/Grid + responsive design
- [ ] Can fetch API data and handle errors
- [ ] Can use Git & PR workflow

**Project**: Mini Experiment Manager (HTML/CSS/JS, API integration)  

**Knowledge Log**

---

## Week 2: React + Next.js

### **Day 8 – React Components & JSX**
**Resources**
- [React Tutorial](https://react.dev/learn/tutorial-tic-tac-toe)
- [React Components](https://react.dev/learn/your-first-component)

**Exercises**
- [ ] Convert HTML → React components
- [ ] Build `ExperimentCard`, `StatusBadge`, `Button`
- [ ] Pass props into components

**Deliverable**: Experiment dashboard in React  

**Knowledge Log**

---

### **Day 9 – React State (useState)**
**Resources**
- [Managing State](https://react.dev/learn/managing-state)
- [useState Hook](https://react.dev/reference/react/useState)

**Exercises**
- [ ] Add controlled inputs to forms
- [ ] Create search/filter for experiments
- [ ] Add feature flag toggle with state

**Deliverable**: Interactive experiment form with validation  

**Knowledge Log**

---

### **Day 10 – Effects & Data Fetching (useEffect)**
**Resources**
- [useEffect Hook](https://react.dev/reference/react/useEffect)
- [Synchronizing Effects](https://react.dev/learn/synchronizing-with-effects)

**Exercises**
- [ ] Fetch data on component mount
- [ ] Show loading + error states
- [ ] Add refresh button to reload experiments

**Deliverable**: API-powered experiment list  

**Knowledge Log**

---

### **Day 11 – Custom Hooks & Context**
**Resources**
- [Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks)
- [React Context](https://react.dev/learn/passing-data-deeply-with-context)

**Exercises**
- [ ] Create `useExperiments` hook for API
- [ ] Add `useAuth` hook for authentication
- [ ] Use Context for global auth state

**Deliverable**: Dashboard with hooks + global state  

**Knowledge Log**

---

### **Day 12 – Next.js Basics**
**Resources**
- [Next.js Tutorial](https://nextjs.org/learn)
- [Next.js Routing](https://nextjs.org/docs/routing/introduction)

**Exercises**
- [ ] Create Next.js project
- [ ] Build `/experiments` and `/experiments/[id]`
- [ ] Add shared layout (header/nav/footer)

**Deliverable**: Next.js app with routing  

**Knowledge Log**

---

### **Day 13 – Next.js API Routes**
**Resources**
- [Next.js API Routes](https://nextjs.org/docs/api-routes/introduction)
- [Next.js Data Fetching](https://nextjs.org/docs/basic-features/data-fetching)

**Exercises**
- [ ] Build API routes for experiments
- [ ] Use `getServerSideProps` / `getStaticProps`
- [ ] Integrate backend API calls

**Deliverable**: CRUD with Next.js API routes  

**Knowledge Log**

---

### **Day 14 – Accessibility Review**
**Resources**
- [Web.dev Accessibility](https://web.dev/accessibility/)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)

**Exercises**
- [ ] Add aria-labels to buttons/forms
- [ ] Test keyboard navigation
- [ ] Check color contrast

**Deliverable**: Accessible experiment dashboard  

**Knowledge Log**

---

## Week 3: TypeScript + Testing

### **Day 15 – TypeScript Basics**
**Resources**
- [TS Handbook Basics](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)
- [React + TS Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

**Exercises**
- [ ] Add types to props
- [ ] Define experiment interface

**Deliverable**: Components with TS props  

**Knowledge Log**

---

### **Day 16 – Advanced TS in React**
**Resources**
- [TypeScript Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)

**Exercises**
- [ ] Add types to hooks + API functions
- [ ] Handle optional/nullable types

**Deliverable**: Typed API client + hooks  

**Knowledge Log**

---

### **Day 17 – Testing Basics**
**Resources**
- [Jest Docs](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

**Exercises**
- [ ] Write test for `ExperimentCard`
- [ ] Test props rendering

**Deliverable**: Unit-tested component  

**Knowledge Log**

---

### **Day 18 – Testing Async & Forms**
**Resources**
- [Testing Async](https://testing-library.com/docs/example-react-hooks/)

**Exercises**
- [ ] Test API call hooks with mocked fetch
- [ ] Test form validation

**Deliverable**: Tested form + API hooks  

**Knowledge Log**

---

### **Day 19 – Advanced State**
**Resources**
- [useReducer](https://react.dev/reference/react/useReducer)

**Exercises**
- [ ] Refactor experiment state into reducer
- [ ] Manage complex state transitions

**Deliverable**: Reducer-driven experiment management  

**Knowledge Log**

---

### **Day 20 – Performance**
**Resources**
- [React.memo](https://react.dev/reference/react/memo)
- [useCallback/useMemo](https://react.dev/reference/react/useCallback)

**Exercises**
- [ ] Optimize large experiment lists
- [ ] Profile renders with React DevTools

**Deliverable**: Optimized experiment dashboard  

**Knowledge Log**

---

### **Day 21 – Mini Project**
**Deliverable**
- TypeScript + tested experiment manager
- CRUD + forms + API + accessibility  

**Knowledge Log**

---

## Week 4: Project Integration

### **Day 22 – Study Codebase**
- [ ] Clone repo
- [ ] Review folder structure
- [ ] Explore routing + state patterns

**Knowledge Log**

---

### **Day 23 – First Contribution**
- [ ] Fix bug or add small UI feature
- [ ] Open PR → go through review  

**Knowledge Log**

---

### **Day 24 – Experiment Form Feature**
- [ ] Controlled form with validation + API integration  

**Knowledge Log**

---

### **Day 25 – Feature Flag Dashboard**
- [ ] Toggle UI with API integration + tests  

**Knowledge Log**

---

### **Day 26 – Data Visualization**
**Resources**
- [Recharts](https://recharts.org/en-US/examples)
- [Chart.js](https://www.chartjs.org/docs/latest/)

**Exercises**
- [ ] Display experiment results (conversion rates chart)  

**Knowledge Log**

---

### **Day 27 – Polish**
- [ ] Add accessibility fixes
- [ ] Refactor code
- [ ] Optimize rendering  

**Knowledge Log**

---

### **Day 28 – PR & Wrap-up**
- [ ] Submit feature PR
- [ ] Review feedback + apply changes
- [ ] Document learnings + gaps  

**Knowledge Log**

---

## 🛠️ Daily Checklist
- [ ] Complete readings & exercises
- [ ] Build working code examples
- [ ] Test across browsers
- [ ] Commit code to GitHub
- [ ] Document learnings
- [ ] Prep for tomorrow

