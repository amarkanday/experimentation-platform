# Experimentation Platform Wireframes

## Page Layout Structures

### Common Page Structure
```
+-------------------------------------------------------+
|  HEADER [Logo] [Search]        [Notifications] [User] |
+-------------------------------------------------------+
|        |                                              |
|        |                                              |
|        |                                              |
|        |                                              |
| N      |             MAIN CONTENT AREA                |
| A      |                                              |
| V      |                                              |
|        |                                              |
| M      |                                              |
| E      |                                              |
| N      |                                              |
| U      |                                              |
|        |                                              |
+-------------------------------------------------------+
|                       FOOTER                          |
+-------------------------------------------------------+
```

### Dashboard Layout
```
+-------------------------------------------------------+
|  HEADER [Logo] [Search]        [Notifications] [User] |
+-------------------------------------------------------+
|        |  [Active Exp] [Feature Flags] [Conversions]  |
|        |  +----------+ +------------+ +------------+  |
|        |  |          | |            | |            |  |
| N      |  +----------+ +------------+ +------------+  |
| A      |                                              |
| V      |  +-------------------+ +-------------------+ |
|        |  |                   | |                   | |
| M      |  |  Performance      | |  Experiment       | |
| E      |  |  Chart            | |  Status Summary   | |
| N      |  |                   | |                   | |
| U      |  +-------------------+ +-------------------+ |
|        |                                              |
|        |  +-------------------------------------------+|
|        |  |             Recent Activity Feed          ||
|        |  +-------------------------------------------+|
+-------------------------------------------------------+
|                       FOOTER                          |
+-------------------------------------------------------+
```

### Experiments List Layout
```
+-------------------------------------------------------+
|  HEADER [Logo] [Search]        [Notifications] [User] |
+-------------------------------------------------------+
|        |  [Search/Filter Bar]       [Create Experiment]|
|        |  +-------------------------------------------+|
|        |  | Name | Status | Type | Metrics | Date | ⚙ ||
| N      |  +-------------------------------------------+|
| A      |  | Exp 1 | Active | A/B  | +12%    | 1/1  | ⚙ ||
| V      |  +-------------------------------------------+|
|        |  | Exp 2 | Draft  | MVT  | --      | 1/2  | ⚙ ||
| M      |  +-------------------------------------------+|
| E      |  | Exp 3 | Paused | A/B  | -2%     | 1/3  | ⚙ ||
| N      |  +-------------------------------------------+|
| U      |  | Exp 4 | Comp.  | Flag | +5%     | 1/4  | ⚙ ||
|        |  +-------------------------------------------+|
|        |                                              |
|        |  [< 1 2 3 ... >]  [Items per page: 10 ▼]     |
+-------------------------------------------------------+
|                       FOOTER                          |
+-------------------------------------------------------+
```

### Experiment Detail Layout
```
+-------------------------------------------------------+
|  HEADER [Logo] [Search]        [Notifications] [User] |
+-------------------------------------------------------+
|        |  Experiment: Test Name       [Status: Active] |
|        |  +-------------------------------------------+|
|        |  | Overview | Variants | Results | Logs | ⚙ | |
| N      |  +-------------------------------------------+|
| A      |  |                                           ||
| V      |  |  [Experiment Summary Card]                ||
|        |  |  +---------------------------------------+||
| M      |  |  | Description:                          |||
| E      |  |  | Hypothesis:                           |||
| N      |  |  | Created: 1/1/2023                     |||
| U      |  |  +---------------------------------------+||
|        |  |                                           ||
|        |  |  [Primary Metrics]      [Secondary Metrics]|
|        |  |  +----------------+     +----------------+||
|        |  |  | Conversion: 5% |     | Bounce: -2%    |||
|        |  |  +----------------+     +----------------+||
|        |  |                                           ||
|        |  |  [Actions]                                ||
|        |  |  [Edit] [Stop] [Restart] [Archive]        ||
+-------------------------------------------------------+
|                       FOOTER                          |
+-------------------------------------------------------+
```

### Feature Flags List Layout
```
+-------------------------------------------------------+
|  HEADER [Logo] [Search]        [Notifications] [User] |
+-------------------------------------------------------+
|        |  [Search/Filter Bar]       [Create Flag]     |
|        |  +-------------------------------------------+|
|        |  | Name | Status | Env | Desc | Date | ⚙     ||
| N      |  +-------------------------------------------+|
| A      |  | Flag1 | [ON]  | All | New UI | 1/1 | ⚙    ||
| V      |  +-------------------------------------------+|
|        |  | Flag2 | [OFF] | Dev | Beta   | 1/2 | ⚙    ||
| M      |  +-------------------------------------------+|
| E      |  | Flag3 | [ON]  | Prod| Search | 1/3 | ⚙    ||
| N      |  +-------------------------------------------+|
| U      |  | Flag4 | [OFF] | Stg | Theme  | 1/4 | ⚙    ||
|        |  +-------------------------------------------+|
|        |                                              |
|        |  [< 1 2 3 ... >]  [Items per page: 10 ▼]     |
+-------------------------------------------------------+
|                       FOOTER                          |
+-------------------------------------------------------+
```

### User Management Layout
```
+-------------------------------------------------------+
|  HEADER [Logo] [Search]        [Notifications] [User] |
+-------------------------------------------------------+
|        |  [Search/Filter Bar]       [Create User]     |
|        |  +-------------------------------------------+|
|        |  | Name | Email | Role | Status | Last | ⚙   ||
| N      |  +-------------------------------------------+|
| A      |  | User1 | u1@ex | Admin | Active | 1h  | ⚙  ||
| V      |  +-------------------------------------------+|
|        |  | User2 | u2@ex | Editor| Active | 1d  | ⚙  ||
| M      |  +-------------------------------------------+|
| E      |  | User3 | u3@ex | Viewer| Inact. | 7d  | ⚙  ||
| N      |  +-------------------------------------------+|
| U      |  | User4 | u4@ex | Editor| Active | 3h  | ⚙  ||
|        |  +-------------------------------------------+|
|        |                                              |
|        |  [< 1 2 3 ... >]  [Items per page: 10 ▼]     |
+-------------------------------------------------------+
|                       FOOTER                          |
+-------------------------------------------------------+
```

### User Edit Modal
```
+------------------------------------------+
|  Edit User                           [X] |
+------------------------------------------+
|  User Information                        |
|  Name: [John Doe                     ]   |
|  Email: [john.doe@example.com        ]   |
|                                          |
|  Role: [Admin ▼]                         |
|                                          |
|  Permissions:                            |
|  • Create/Edit/Delete Experiments        |
|  • Create/Edit/Delete Feature Flags      |
|  • Manage Users                          |
|  • Access Analytics                      |
|                                          |
|  Status: [Active ▼]                      |
|                                          |
|  [Cancel]                [Save Changes]  |
+------------------------------------------+
```

### Mobile Dashboard Layout
```
+-------------------------------+
| [☰] Exp Platform    [👤] [🔔] |
+-------------------------------+
| [🔍 Search...]               |
+-------------------------------+
| [Active Experiments]         |
| 15                           |
+-------------------------------+
| [Feature Flags]              |
| 23                           |
+-------------------------------+
| [Total Conversions]          |
| 48,239                       |
+-------------------------------+
|                              |
| [Performance Chart]          |
|                              |
|                              |
+-------------------------------+
|                              |
| [Recent Activity]            |
| • User1 created Exp1         |
| • User2 updated Flag3        |
| • User3 archived Exp5        |
+-------------------------------+
| [HOME] [EXPS] [FLAGS] [MORE] |
+-------------------------------+
```

## Main Dashboard

### Layout
- **Header**: Platform logo, search bar, notifications icon, user profile menu with role indicator
- **Sidebar**: Navigation menu with role-based visibility
- **Main Content Area**: Dashboard widgets and metrics

### Dashboard Widgets
- **Active Experiments Card**: Count and list of active experiments
- **Feature Flags Card**: Count and list of active feature flags
- **Total Conversions Card**: Aggregate conversion metrics
- **Recent Activity Feed**: Timeline of recent platform actions
- **Performance Chart**: Key metrics over time
- **Experiments Status Summary**: Pie chart showing experiment status distribution

## Experiments Section

### Experiments List View
- **Create Experiment Button**: Top-right position with role-based access
- **Filters**: Status, type, date range, search
- **Experiments Table**:
  - Columns: Name, Status, Type, Key Metrics, Created Date, Actions
  - Actions: View, Edit, Archive (role-based)
- **Pagination Controls**: Page navigation and items per page selector

### Experiment Creation/Edit
- **Multi-step Form**:
  1. Basic Info: Name, Description, Hypothesis
  2. Metrics: Primary, Secondary metrics selection
  3. Audience: Targeting criteria
  4. Variants: Configuration for each variant
  5. Schedule: Start/end dates, sampling rate
- **Preview Panel**: Live preview of experiment configuration
- **Save/Cancel Controls**: Bottom of form

### Experiment Detail View
- **Header**: Experiment name, status badge, created date
- **Tabs**:
  - Overview: Description, hypothesis, key metrics
  - Variants: List of variants with configuration
  - Results: Performance metrics and statistical analysis
  - Logs: Experiment activity history
  - Settings: Configuration options
- **Action Buttons**: Edit, Stop, Restart, Archive (role-based)

### Experiment Variants Section
- **Variants List**:
  - Control variant
  - Test variants
  - Traffic allocation percentages
  - Variant configuration details
- **Add Variant Button**: With role-based permissions

### Experiment Results View
- **Results Summary Card**: Overall experiment performance
- **Primary Metric Charts**: Conversion rates with confidence intervals
- **Secondary Metrics Table**: Metrics by variant
- **Statistical Significance Indicators**: Visual indicators of statistical confidence
- **Download Results Button**: Export options (CSV, PDF)

## Feature Flags Section

### Feature Flags List View
- **Create Feature Flag Button**: Top-right position with role-based access
- **Filters**: Status, environment, search
- **Feature Flags Table**:
  - Columns: Name, Status, Environments, Description, Created Date, Actions
  - Toggle switches for quick enable/disable
  - Actions: View, Edit, Delete (role-based)
- **Pagination Controls**

### Feature Flag Creation/Edit
- **Form Fields**:
  - Name, Key, Description
  - Environments: Dev, Staging, Production toggles
  - Targeting Rules: User segments, percentage rollouts
  - Default values per environment
- **JSON Configuration View**: Advanced configuration option
- **Save/Cancel Controls**

### Feature Flag Detail View
- **Header**: Feature flag name, status toggles per environment
- **Tabs**:
  - Overview: Description, key, environments
  - Targeting: Rules and conditions
  - History: Change log and activity
  - Settings: Configuration options
- **Action Buttons**: Edit, Delete (role-based)

## Analytics Section

### Analytics Dashboard
- **Date Range Selector**: Custom date range filtering
- **Metrics Overview Cards**:
  - Total experiments run
  - Average conversion rates
  - Top performing variants
- **Experiments Performance Table**: Sortable metrics across experiments
- **Feature Flags Usage Chart**: Activation counts over time
- **Custom Reports Section**: Saved and recent reports

### Custom Report Builder
- **Metrics Selection**: Drag-and-drop interface for metrics
- **Dimension Selection**: Group by options (date, experiment, variant, etc.)
- **Visualization Options**: Chart types, table views
- **Export and Save Options**: Download or save to dashboard

## User Management Section (Admin Only)

### Users List View
- **Create User Button**: Admin-only access
- **Filters**: Role, status, search
- **Users Table**:
  - Columns: Name, Email, Role, Status, Last Active, Actions
  - Actions: Edit, Deactivate, Delete (admin-only)
- **Pagination Controls**

### User Edit/Role Assignment Modal
- **User Information**: Name, email, contact details
- **Role Dropdown**: Select user role (Admin, Editor, Viewer)
- **Permissions Overview**: List of permissions based on selected role
- **Save/Cancel Controls**

## Settings & Integrations

### Account Settings
- **Organization Profile**: Name, logo, timezone
- **API Keys**: View, generate, revoke API keys
- **User Preferences**: Theme, notifications, language

### Integrations Panel
- **Available Integrations**: Analytics, CRM, etc.
- **Connected Services**: Status and configuration
- **Add Integration Button**: With configuration modal

## Mobile View Examples

### Mobile Dashboard
- **Simplified metrics cards**: Stacked vertically
- **Collapsible navigation menu**: Hamburger icon
- **Responsive charts**: Optimized for smaller screens

### Mobile Experiments List
- **Card-based layout** instead of table
- **Swipe actions**: Quick access to view/edit
- **Filtered view selector**: Tabs for different statuses

## Role-Based Elements

### Role Indicators
- **User Profile Menu**: Shows current user role
- **Action Buttons**: Disabled or hidden based on permissions
- **Navigation Items**: Visible only to authorized roles

### Permission Denied Messages
- **Modal Format**: Clear explanation of required permissions
- **Contact Admin Option**: Direct link to request access

## System Notifications

### Notification Types
- **Success Messages**: Green toast notifications for completed actions
- **Warning Alerts**: Yellow banners for important notices
- **Error Messages**: Red modal dialogs for critical issues
- **Information Cards**: Blue cards for tips and guidance

### Notification Placement
- **Toast Notifications**: Top-right corner
- **System Alerts**: Top center banner
- **Inline Validation**: Next to form fields
