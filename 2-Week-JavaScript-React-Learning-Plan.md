# 📅 2-Week JavaScript & React Learning Plan - Detailed Daily Schedule

## **Week 1: JavaScript Fundamentals + React Basics**

### **Day 1: Master JS Variables & Functions**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **JavaScript Core Concepts** | • [JavaScript.info - Variables](https://javascript.info/variables)<br>• [MDN - Data Types](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Data_structures)<br>• [JavaScript Crash Course - Traversy Media](https://www.youtube.com/watch?v=hdI2bqOjy3c) (0-45 min) | • Read JavaScript.info chapters 2.1-2.4 (variables, data types)<br>• Practice: Declare 20 different variables with meaningful names<br>• Exercise: Create variables for experiment data (name, status, participants)<br>• Quiz: Test yourself on let vs const vs var<br>• Setup: Install VS Code and JavaScript extensions |
| **Break** | 12:00-12:15 | Rest | | • Step away from computer<br>• Review mental notes from morning |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **Functions & Objects** | • [JavaScript.info - Functions](https://javascript.info/function-basics)<br>• [MDN - Functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions)<br>• [Object Basics](https://javascript.info/object) | • Read JavaScript.info chapters 2.9-2.11 (functions)<br>• Build: 5 functions that calculate experiment metrics<br>• Practice: Create objects representing experiments and feature flags<br>• Exercise: Write function to filter experiments by status<br>• Challenge: Build a simple conversion rate calculator |

### **Day 2: Async JavaScript & Modern Syntax**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **Arrays & Modern JavaScript** | • [JavaScript.info - Arrays](https://javascript.info/array)<br>• [Array Methods](https://javascript.info/array-methods)<br>• [Destructuring Assignment](https://javascript.info/destructuring-assignment) | • Master array methods: map, filter, find, reduce<br>• Practice: Transform experiment data arrays 10 different ways<br>• Learn: Destructuring objects and arrays<br>• Exercise: Extract data from nested experiment objects<br>• Build: Function to group experiments by status |
| **Break** | 12:00-12:15 | Rest | | • Quick walk or stretch<br>• Review array method cheat sheet |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **Promises & Async/Await** | • [JavaScript.info - Promises](https://javascript.info/promise-basics)<br>• [MDN - Async/Await](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)<br>• [Fetch API Tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch) | • Complete promises tutorial with 5 practical examples<br>• Practice: Convert 3 promise chains to async/await<br>• Build: Mock API calls for experiment data<br>• Exercise: Handle API errors gracefully<br>• Challenge: Implement retry logic for failed requests |

### **Day 3: React Components & JSX**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **React Setup & First Components** | • [React.dev - Installation](https://react.dev/learn/installation)<br>• [Your First Component](https://react.dev/learn/your-first-component)<br>• [Writing Markup with JSX](https://react.dev/learn/writing-markup-with-jsx) | • Setup: Create React app with `npx create-react-app experiment-dashboard`<br>• Read: React.dev tutorial sections 1-2<br>• Build: Hello World component<br>• Practice: Convert 5 HTML snippets to JSX<br>• Create: Basic ExperimentCard component structure |
| **Break** | 12:00-12:15 | Rest | | • Install React DevTools extension<br>• Review JSX vs HTML differences |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **Props & Component Composition** | • [Passing Props](https://react.dev/learn/passing-props-to-a-component)<br>• [Conditional Rendering](https://react.dev/learn/conditional-rendering)<br>• [Rendering Lists](https://react.dev/learn/rendering-lists) | • Build: ExperimentCard component that accepts props<br>• Create: ExperimentList component that maps over data<br>• Practice: Conditional rendering for experiment status<br>• Exercise: Build StatusBadge component with different styles<br>• Challenge: Create nested component structure |

### **Day 4: State Management & Events**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **useState Hook** | • [Adding Interactivity](https://react.dev/learn/adding-interactivity)<br>• [useState Reference](https://react.dev/reference/react/useState)<br>• [State vs Props](https://react.dev/learn/passing-props-to-a-component#how-props-change-over-time) | • Complete useState tutorial with 3 examples<br>• Build: Counter component to understand state updates<br>• Practice: Toggle component for feature flag status<br>• Exercise: Manage form input state<br>• Create: Experiment filter component with search state |
| **Break** | 12:00-12:15 | Rest | | • Review state update patterns<br>• Check React DevTools state inspection |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **Event Handling & Forms** | • [Responding to Events](https://react.dev/learn/responding-to-events)<br>• [State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)<br>• [Controlled Components](https://react.dev/reference/react-dom/components/input) | • Build: Click handlers for experiment actions<br>• Create: Form component with controlled inputs<br>• Practice: Form validation and error states<br>• Exercise: Multi-step form for experiment creation<br>• Challenge: Implement search and filter functionality |

### **Day 5: Effects & Data Fetching**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **useEffect Hook** | • [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)<br>• [useEffect Reference](https://react.dev/reference/react/useEffect)<br>• [Effect Dependencies](https://react.dev/learn/lifecycle-of-reactive-effects) | • Complete useEffect tutorial with lifecycle examples<br>• Build: Component that fetches data on mount<br>• Practice: Cleanup functions for subscriptions<br>• Exercise: Effect dependencies and when they run<br>• Create: Timer component with useEffect |
| **Break** | 12:00-12:15 | Rest | | • Review effect cleanup patterns<br>• Test component mounting/unmounting |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **Data Fetching Patterns** | • [Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks)<br>• [Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)<br>• [Loading States](https://react.dev/learn/managing-state) | • Build: useExperiments custom hook<br>• Create: Loading spinner and error handling<br>• Practice: Retry failed API calls<br>• Exercise: Optimistic updates for better UX<br>• Challenge: Implement data caching with useEffect |

### **Day 6: Integration & Practice**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **React DevTools & Debugging** | • [React Developer Tools](https://react.dev/learn/react-developer-tools)<br>• [Common Bugs](https://react.dev/learn/troubleshooting)<br>• Review your project's frontend files | • Master React DevTools: inspect props, state, hooks<br>• Debug: Intentionally break 3 components and fix them<br>• Practice: Performance profiling with DevTools<br>• Study: 3 components from your actual project<br>• Document: Patterns you recognize in the codebase |
| **Break** | 12:00-12:15 | Rest | | • Review debugging checklist<br>• Plan afternoon build session |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **Mini Dashboard Build** | • [CodeSandbox React Template](https://codesandbox.io/s/new)<br>• [CSS-in-JS or CSS Modules](https://create-react-app.dev/docs/adding-a-css-modules-stylesheet/)<br>• Your project's styling approach | • Build: Complete experiment dashboard with list and details<br>• Implement: Search, filter, and sort functionality<br>• Style: Make it look professional with CSS<br>• Test: All interactive features work correctly<br>• Deploy: Push to GitHub and deploy to Netlify/Vercel |

### **Day 7: Week 1 Assessment**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **Knowledge Assessment** | • [React Quiz - W3Schools](https://www.w3schools.com/react/react_quiz.asp)<br>• [JavaScript Assessment - MDN](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/First_steps/A_first_splash)<br>• [freeCodeCamp React Challenges](https://www.freecodecamp.org/learn/front-end-development-libraries/) | • Take: JavaScript fundamentals quiz (score >80%)<br>• Complete: React concepts assessment<br>• Build: Feature flag toggle component from scratch<br>• Code Review: Analyze your week's code for improvements<br>• Document: Create README with your learning progress |
| **Break** | 12:00-13:00 | Extended Break | | • Lunch break<br>• Mental reset for afternoon |
| **Afternoon** | 13:00-18:00<br>(5 hours) | **Portfolio Project** | • [GitHub Pages](https://pages.github.com/)<br>• [Netlify Deployment](https://docs.netlify.com/site-deploys/create-deploys/)<br>• Plan Week 2 focus areas | • Build: Complete experiment management interface<br>• Features: List, create, edit, delete experiments<br>• Polish: Professional styling and responsive design<br>• Deploy: Live demo on GitHub Pages or Netlify<br>• Plan: Identify Week 2 learning priorities and gaps |

---

## **Week 2: Next.js + Advanced React + TypeScript**

### **Day 8: Next.js Routing & Pages**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **Next.js Setup & File-based Routing** | • [Next.js Tutorial](https://nextjs.org/learn/basics/create-nextjs-app)<br>• [Pages and Routing](https://nextjs.org/docs/basic-features/pages)<br>• [Link Component](https://nextjs.org/docs/api-reference/next/link) | • Setup: Create Next.js app with TypeScript template<br>• Study: File-based routing system<br>• Build: pages/experiments/index.tsx matching your project<br>• Create: Navigation component with Next.js Link<br>• Practice: 5 different page structures |
| **Break** | 12:00-12:15 | Rest | | • Review Next.js vs React differences<br>• Check file structure matches conventions |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **Dynamic Routes & Navigation** | • [Dynamic Routes](https://nextjs.org/docs/routing/dynamic-routes)<br>• [useRouter Hook](https://nextjs.org/docs/api-reference/next/router)<br>• [Programmatic Navigation](https://nextjs.org/docs/routing/imperatively) | • Build: pages/experiments/[id].tsx for experiment details<br>• Implement: useRouter for accessing route parameters<br>• Create: Breadcrumb navigation component<br>• Practice: Programmatic navigation after form submission<br>• Challenge: Nested routing for experiment sections |

### **Day 9: Forms & CRUD Operations**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **Advanced Form Handling** | • [Form Best Practices](https://web.dev/learn/forms/)<br>• [React Hook Form](https://react-hook-form.com/get-started)<br>• [Form Validation](https://developer.mozilla.org/en-US/docs/Learn/Forms/Form_validation) | • Install: React Hook Form for better form management<br>• Build: Multi-step experiment creation form<br>• Implement: Real-time validation with error messages<br>• Create: Form components matching your project's style<br>• Practice: Different input types and validation rules |
| **Break** | 12:00-12:15 | Rest | | • Review form patterns from your project<br>• Test form accessibility features |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **API Integration & CRUD** | • [Next.js API Routes](https://nextjs.org/docs/api-routes/introduction)<br>• [HTTP Methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)<br>• [Error Handling](https://nextjs.org/docs/api-routes/response-helpers) | • Create: API route handlers for experiments<br>• Implement: POST, PUT, DELETE operations<br>• Build: Error handling and success notifications<br>• Practice: Optimistic updates for better UX<br>• Test: All CRUD operations work correctly |

### **Day 10: Context API & Global State**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **React Context Setup** | • [Context API Deep Dive](https://react.dev/learn/passing-data-deeply-with-context)<br>• [Context Performance](https://kentcdodds.com/blog/how-to-optimize-your-context-value)<br>• [When to Use Context](https://react.dev/learn/passing-data-deeply-with-context#before-you-use-context) | • Create: ExperimentContext with Provider<br>• Build: useExperiments hook for consuming context<br>• Implement: Global loading and error states<br>• Practice: Context composition with multiple providers<br>• Optimize: Prevent unnecessary re-renders |
| **Break** | 12:00-12:15 | Rest | | • Review context patterns in your project<br>• Plan global state architecture |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **Authentication Context** | • [Auth Context Pattern](https://kentcdodds.com/blog/authentication-in-react-applications)<br>• [JWT Handling](https://jwt.io/introduction)<br>• Study your project's auth implementation | • Build: AuthContext for user management<br>• Create: Protected route components<br>• Implement: Login/logout functionality<br>• Practice: Role-based access control<br>• Integrate: Auth state with experiment permissions |

### **Day 11: Component Patterns & Best Practices**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **Advanced React Patterns** | • [React Patterns](https://reactpatterns.com/)<br>• [Compound Components](https://kentcdodds.com/blog/compound-components-with-react-hooks)<br>• [Render Props](https://reactjs.org/docs/render-props.html) | • Build: Compound components for experiment cards<br>• Create: Reusable modal with render props<br>• Practice: Higher-order components for common logic<br>• Implement: Custom hooks for shared behavior<br>• Study: Patterns used in your project codebase |
| **Break** | 12:00-12:15 | Rest | | • Review component architecture decisions<br>• Plan reusable component library |
| **Afternoon** | 12:15-15:15<br>(3 hours) | **Performance & Optimization** | • [React Performance](https://react.dev/learn/render-and-commit)<br>• [useMemo and useCallback](https://react.dev/reference/react/useMemo)<br>• [Code Splitting](https://nextjs.org/docs/advanced-features/dynamic-import) | • Optimize: Components with React.memo<br>• Implement: useMemo for expensive calculations<br>• Practice: useCallback for stable function references<br>• Add: Lazy loading for heavy components<br>• Measure: Performance with React DevTools Profiler |

### **Day 12: Mini Platform Build Day**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-13:00<br>(4 hours) | **Feature Implementation** | • [Tailwind CSS](https://tailwindcss.com/docs/installation)<br>• [CSS Grid/Flexbox](https://css-tricks.com/snippets/css/complete-guide-grid/)<br>• Study your project's component library | • Build: Complete experiment management dashboard<br>• Implement: Real-time experiment status updates<br>• Create: Feature flag toggle interface<br>• Add: Bulk operations for multiple experiments<br>• Style: Professional UI matching your project's design |
| **Break** | 13:00-14:00 | Extended Break | | • Lunch and mental reset<br>• Review morning's code |
| **Afternoon** | 14:00-18:00<br>(4 hours) | **Advanced Features** | • [WebSocket Integration](https://nextjs.org/docs/api-routes/introduction)<br>• [Data Visualization](https://recharts.org/en-US/)<br>• [Accessibility](https://web.dev/accessibility/) | • Build: Audit log viewer with pagination<br>• Add: Real-time notifications for experiment changes<br>• Create: Basic charts for experiment metrics<br>• Implement: Keyboard navigation and screen reader support<br>• Test: All features work on mobile devices |

### **Day 13: TypeScript Integration**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **TypeScript Fundamentals** | • [TypeScript Handbook](https://www.typescriptlang.org/docs/)<br>• [TypeScript in 5 Minutes](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html)<br>• [Basic Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html) | • Learn: TypeScript basic types and interfaces<br>• Practice: Type 10 JavaScript functions<br>• Create: Type definitions for experiment data structures<br>• Convert: 3 JavaScript files to TypeScript<br>• Fix: All type errors in converted files |
| **Break** | 12:00-12:15 | Rest | | • Review TypeScript compiler errors<br>• Plan component conversion strategy |
| **Afternoon** | 12:15-17:15<br>(5 hours) | **React + TypeScript** | • [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)<br>• [Typing Components](https://react-typescript-cheatsheet.netlify.app/docs/basic/getting-started/basic_type_example)<br>• [Generic Components](https://react-typescript-cheatsheet.netlify.app/docs/advanced/patterns_by_usecase) | • Convert: All React components to TypeScript<br>• Type: All props interfaces and component states<br>• Create: Generic components with proper typing<br>• Fix: All TypeScript compilation errors<br>• Validate: Type safety with strict mode enabled |

### **Day 14: Real Project Integration**
| Session | Time | Focus | Resources | Specific Action Items |
|---------|------|-------|-----------|----------------------|
| **Morning** | 9:00-12:00<br>(3 hours) | **Codebase Analysis** | • Your project's entire frontend codebase<br>• [Git Best Practices](https://www.atlassian.com/git/tutorials/comparing-workflows)<br>• [Code Review Guidelines](https://google.github.io/eng-practices/review/) | • Study: Read through all components in your project<br>• Analyze: File structure and naming conventions<br>• Document: 10 patterns you now understand<br>• Identify: 5 potential improvement areas<br>• Create: Issue list for potential contributions |
| **Break** | 12:00-13:00 | Extended Break | | • Lunch and reflection on learning journey<br>• Prepare for first contribution |
| **Afternoon** | 13:00-18:00<br>(5 hours) | **First Contribution** | • [Contributing Guidelines](https://opensource.guide/how-to-contribute/)<br>• [Pull Request Best Practices](https://github.blog/2015-01-21-how-to-write-the-perfect-pull-request/)<br>• Your project's specific contribution guide | • Choose: Simple first contribution (documentation, small bug fix, or new component)<br>• Implement: Your contribution following project conventions<br>• Test: Ensure your changes work correctly<br>• Submit: Pull request with clear description<br>• Plan: Next 2-4 weeks of continued learning and contributions |

## **📚 Essential Bookmarks**

| Category | Resource | URL | Use Case |
|----------|----------|-----|----------|
| **JavaScript** | MDN Web Docs | https://developer.mozilla.org/en-US/docs/Web/JavaScript | Reference and tutorials |
| **JavaScript** | JavaScript.info | https://javascript.info/ | Comprehensive learning |
| **React** | React Documentation | https://react.dev/ | Official React guide |
| **React** | React DevTools | Chrome Extension Store | Debugging components |
| **Next.js** | Next.js Documentation | https://nextjs.org/docs | Framework reference |
| **TypeScript** | TypeScript Handbook | https://www.typescriptlang.org/docs/ | Type system learning |
| **Practice** | CodeSandbox | https://codesandbox.io/ | Online React playground |
| **Practice** | CodePen | https://codepen.io/ | Quick experiments |
| **Styling** | Tailwind CSS | https://tailwindcss.com/ | CSS framework |
| **Tools** | Can I Use | https://caniuse.com/ | Browser compatibility |

## **📋 Session Success Metrics**

### **Morning Session Goals:**
- [ ] Complete all theory/reading within time limit
- [ ] Understand concepts before moving to practice
- [ ] Take notes on key concepts and patterns
- [ ] Ask questions (research or note for later)

### **Afternoon Session Goals:**
- [ ] Build working code examples
- [ ] Apply morning concepts practically
- [ ] Commit code to version control
- [ ] Document challenges and solutions

### **Daily Wrap-up (15 minutes):**
- [ ] Review what was accomplished
- [ ] Note areas needing more practice
- [ ] Plan next day's priorities
- [ ] Update learning journal

## **🎯 Final Project Milestones**

| Milestone | Completion Criteria | Validation |
|-----------|-------------------|------------|
| **Week 1 Complete** | Built interactive React components with state management | Can create and modify experiment list component |
| **JavaScript Mastery** | Comfortable with async operations and modern syntax | Can write API integration functions independently |
| **React Proficiency** | Understands component lifecycle and data flow | Can debug React issues using DevTools |
| **Next.js Integration** | Can build full pages with routing and data fetching | Created working experiment management interface |
| **TypeScript Ready** | Can type React components and handle type errors | Converted existing components to TypeScript |
| **Project Contribution** | Made first meaningful contribution to actual project | Submitted pull request with new feature or improvement |

## **🚀 Quick Reference Commands**

| Task | Command | When to Use |
|------|---------|-------------|
| Create React App | `npx create-next-app@latest my-app --typescript --tailwind --eslint` | Starting new practice project |
| Start Development | `npm run dev` | Daily development work |
| Install React DevTools | Chrome Extension Store | Day 3 setup |
| TypeScript Check | `npx tsc --noEmit` | Day 13 type checking |
| Git Commit | `git add . && git commit -m "Day X: [accomplishment]"` | Daily progress tracking |

## **📈 Progress Tracking Template**

### **Daily Log Format:**
```
## Day X - [Date]
### Morning Session:
- **Completed**: [List achievements]
- **Challenges**: [Note difficulties]
- **Key Learnings**: [Important concepts]

### Afternoon Session:
- **Built**: [What you created]
- **Skills Practiced**: [Specific abilities]
- **Next Steps**: [Tomorrow's priorities]

### Code Committed:
- Repository: [Link]
- Files Changed: [List]
- Features Added: [Description]
```

### **Weekly Review Format:**
```
## Week X Review
### Goals Achieved:
- [ ] [List completed objectives]

### Skills Developed:
- [ ] [Technical abilities gained]

### Projects Built:
- [ ] [Working applications created]

### Areas for Improvement:
- [ ] [Skills needing more practice]

### Next Week Focus:
- [ ] [Priorities for upcoming week]
```

This comprehensive plan ensures you have specific, actionable tasks for every part of each day while building toward your goal of contributing to the experimentation platform!
