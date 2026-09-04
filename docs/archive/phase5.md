# PayResQ — Phase 5: Premium Product UI & Final Integration

## Objective

Build a polished, professional, production-quality frontend for PayResQ.

This is the primary user-facing layer of the hackathon project.

The UI must make the intelligence and autonomous recovery workflow from Phases 1–4 immediately understandable to a judge, developer, merchant, or operations user.

The frontend must NOT be a generic CRUD dashboard.

It should feel like a modern fintech + AI operations platform.

The visual quality is extremely important.

---

# 1. PRODUCT EXPERIENCE

The frontend should communicate:

"PayResQ detects failed payments, understands why they failed, predicts the best recovery strategy, safely orchestrates recovery, and shows the recovered revenue."

The experience should feel:

- premium
- modern
- trustworthy
- fintech-oriented
- AI-native
- professional
- clean
- responsive
- fast
- data-driven

Avoid excessive visual effects.

Do not make it look like a gaming dashboard.

Do not use a template that looks obviously copied or generic.

---

# 2. FRONTEND STACK

Inspect the repository before choosing technologies.

Prefer a modern React-based application.

Preferred:

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui or similarly polished component primitives
- Recharts or an appropriate charting library

Use the existing project conventions if a frontend already exists.

Do not unnecessarily replace an existing working frontend stack.

---

# 3. DESIGN DIRECTION

Design language:

Premium fintech control center.

Think:

- Stripe Dashboard
- Linear
- Vercel
- modern AI observability platforms
- enterprise fintech operations software

But do NOT copy any specific product.

The UI should have its own PayResQ identity.

Use a restrained visual system.

Prefer:

- neutral/slate backgrounds
- white/dark elevated surfaces depending on theme
- subtle borders
- excellent typography
- generous spacing
- clear hierarchy
- restrained accent color
- meaningful status colors only where appropriate

Avoid:

- rainbow gradients
- excessive glassmorphism
- giant glowing cards
- excessive rounded pills
- unnecessary animations
- excessive shadows
- cluttered dashboards

---

# 4. BRANDING

Product name:

PayResQ

Tagline:

Autonomous Payment Recovery

Create a simple professional PayResQ wordmark/logo treatment using CSS/SVG if appropriate.

Do not depend on external image assets for the core brand.

The navigation should clearly establish PayResQ as the product.

---

# 5. APPLICATION SHELL

Create a professional application shell.

Desktop:

┌───────────────────────────────────────────────────────────┐
│ PayResQ                                   System ● Online  │
├──────────────┬────────────────────────────────────────────┤
│              │                                            │
│ Overview     │                                            │
│ Payments     │              Main Content                  │
│ Recoveries   │                                            │
│ Intelligence│                                            │
│ Audit Log    │                                            │
│              │                                            │
│ Settings     │                                            │
└──────────────┴────────────────────────────────────────────┘

Navigation:

- Overview
- Payments
- Recoveries
- Intelligence
- Audit Log

Settings can be included if useful.

The sidebar should clearly show the active page.

On smaller screens, provide a responsive navigation solution.

---

# 6. OVERVIEW DASHBOARD

Create a premium executive dashboard.

Primary KPI cards:

### Revenue at Risk

Example:

₹18.4L

Show contextual change if available.

### Recovered Revenue

Example:

₹5.8L

### Recovery Rate

Example:

31.5%

### Failed Payments

Example:

1,284

Do NOT hardcode these values.

Use real backend data.

If aggregate APIs are not currently available, implement the minimum backend aggregation endpoints necessary.

Do not fabricate business metrics.

Clearly indicate when metrics are based on synthetic/demo data.

---

# 7. RECOVERY PERFORMANCE CHART

Create a polished chart showing recovery performance over time.

Possible:

- recovered revenue
- failed payment volume
- recovery rate

Allow useful time ranges if easy:

- 24h
- 7d
- 30d

Do not overcomplicate the chart.

Tooltips should be polished and readable.

---

# 8. PAYMENT RECOVERY QUEUE

Create a primary table/list showing recent failed and recovered transactions.

Columns:

- Transaction
- Amount
- Payment Method
- Bank
- Failure
- Root Cause
- AI Recommendation
- Status
- Time

Example:

TX-83921
₹7,500
CARD
ICICI
TIMEOUT
Bank degradation
CHANGE METHOD
RECOVERED

Use meaningful status indicators.

Statuses should be visually distinct but restrained.

---

# 9. TRANSACTION DETAILS PAGE

Clicking a transaction must open a detailed intelligence view.

This is one of the most important screens in the application.

Structure:

### Transaction header

Transaction ID

Amount

Status

Payment method

Bank

Customer

Created time

---

### Failure Analysis

Show:

Failure type:

TIMEOUT

Root cause:

TEMPORARY_BANK_DEGRADATION

Confidence:

89%

Evidence:

- recent timeout rate above baseline
- affected bank/method
- recent time-window anomaly

Clearly distinguish:

Observed data

from

AI/ML inference

---

# 10. XGBOOST PREDICTION PANEL

Create a visually strong prediction section.

Example:

Recovery strategy

RETRY NOW                 44%
RETRY AFTER DELAY         49%
SEND PAYMENT LINK         53%
CHANGE PAYMENT METHOD     67%

Use horizontal probability bars or another clean visualization.

Highlight the highest probability without making it visually overwhelming.

Show:

Model:
recovery_model

Version:
v1.0

Do not imply these probabilities are guaranteed outcomes.

Use language such as:

"Predicted recovery probability"

---

# 11. AI AGENT DECISION

Create a dedicated AI decision card.

Example:

AI RECOVERY DECISION

CHANGE PAYMENT METHOD

Confidence
67%

Reasoning:

"XGBoost predicts CHANGE_PAYMENT_METHOD with the highest recovery probability for the current payment context."

Display the decision in a trustworthy manner.

Clearly label it as an AI recommendation.

---

# 12. POLICY DECISION

Create a separate safety/policy section.

Example:

POLICY CHECK

✓ APPROVED

Policy version:
v1

Checks:

✓ Transaction not already successful
✓ Retry limit not exceeded
✓ Amount below automatic threshold
✓ Action not duplicated
✓ Action supported

This section should visually communicate:

AI recommendation ≠ authorization.

The policy engine authorizes the action.

---

# 13. RECOVERY TIMELINE

Create a beautiful event timeline.

Example:

10:31:02
Payment failed
TIMEOUT

10:31:03
Root cause identified
TEMPORARY_BANK_DEGRADATION

10:31:03
XGBoost prediction generated

10:31:04
AI agent selected
CHANGE_PAYMENT_METHOD

10:31:04
Policy approved

10:31:05
Recovery queued

10:31:06
Worker executed

10:31:07
Payment recovered

The timeline should update from actual backend state.

Do not hardcode the timeline.

---

# 14. RECOVERY EXECUTION EXPERIENCE

The UI should make the asynchronous recovery process understandable.

Show states such as:

ANALYZING
RECOMMENDED
POLICY_REVIEW
APPROVED
QUEUED
EXECUTING
COMPLETED
FAILED
CANCELLED
HUMAN_APPROVAL

Use appropriate status components.

If polling is necessary, implement lightweight polling.

Do not hammer the backend.

---

# 15. HUMAN APPROVAL

Create a clear UI for transactions requiring human approval.

Example:

┌────────────────────────────────────────────┐
│ HUMAN APPROVAL REQUIRED                    │
│                                            │
│ Transaction: TX-83923                      │
│ Amount: ₹75,000                            │
│                                            │
│ AI Recommendation: RETRY_AFTER_DELAY       │
│                                            │
│ Reason: Amount exceeds automatic threshold │
│                                            │
│ [ Approve Recovery ] [ Reject ]            │
└────────────────────────────────────────────┘

Approval must call the backend.

Do not implement frontend-only approval state.

---

# 16. INTELLIGENCE PAGE

Create a dedicated Intelligence page showing:

- model version
- training dataset size
- feature count
- ROC-AUC
- F1
- Log Loss
- recovery prediction distribution
- root-cause statistics

Clearly label these as:

Synthetic / Experimental

Do not present synthetic benchmark metrics as real production performance.

---

# 17. ROOT CAUSE ANALYSIS PAGE

Provide a useful view of failure patterns.

Examples:

Failure by bank

Failure by payment method

Failure by failure type

Recent degradation signals

Example:

ICICI + CARD
Recent timeout rate: 18%
Baseline: 5%
Ratio: 3.6×

Likely contributing factor:

Temporary bank degradation

Use charts only where they improve understanding.

---

# 18. RECOVERIES PAGE

Create a dedicated recovery operations page.

Show:

- pending recoveries
- executing recoveries
- successful recoveries
- failed recoveries
- human approval cases

Useful filters:

- status
- action
- date

Do not overbuild filtering.

---

# 19. AUDIT LOG PAGE

Create an audit interface showing:

Timestamp
Transaction
Actor
Event
Action
Result

Examples:

AI_AGENT
AGENT_DECISION

POLICY_ENGINE
POLICY_DECISION

SYSTEM
RECOVERY_EXECUTED

Clicking a record may reveal structured metadata.

Do not expose secrets.

---

# 20. REAL API INTEGRATION

The frontend must use actual Phase 1–4 APIs.

Do NOT create fake static dashboard data.

Create a clear API client layer.

For example:

frontend/src/api/

Possible clients:

- transactions
- intelligence
- recovery
- audit
- dashboard

Keep API calls separate from UI components.

---

# 21. BACKEND AGGREGATION ENDPOINTS

If the UI requires aggregate data that the existing backend does not expose, add minimal read-only endpoints.

Examples:

GET /api/v1/dashboard/summary

GET /api/v1/dashboard/recovery-trends

GET /api/v1/dashboard/failure-breakdown

Only add endpoints that are genuinely required.

Do not redesign the backend.

---

# 22. LOADING STATES

Every major data-driven component must have a polished loading state.

Use:

- skeletons
- subtle spinners
- placeholders

Avoid blank screens.

---

# 23. ERROR STATES

If the backend is unavailable:

show a useful error state.

Example:

Unable to connect to PayResQ API.

Retry

Do not crash the entire frontend.

---

# 24. EMPTY STATES

Handle:

- no failed payments
- no recoveries
- no audit logs
- no human approval cases

Create polished empty states rather than empty tables.

---

# 25. RESPONSIVENESS

The UI must work on:

- desktop
- laptop
- tablet
- mobile

The primary hackathon demo is desktop, but mobile/tablet must not break.

---

# 26. ACCESSIBILITY

Use:

- semantic HTML
- keyboard navigation
- accessible buttons
- appropriate contrast
- ARIA labels where necessary

Do not rely solely on color to communicate state.

---

# 27. ANIMATIONS

Use animation intentionally.

Good uses:

- page transitions
- status changes
- chart entrance
- recovery timeline updates
- subtle hover interactions

Avoid:

- constant motion
- distracting particle effects
- excessive animated gradients
- long animations

The product should feel fast.

---

# 28. DARK/LIGHT THEME

If practical, support both light and dark themes.

Default to the most professional theme for the demo.

Persist the user's choice locally.

Do not sacrifice polish for theme completeness.

---

# 29. DEMO MODE

Create a deterministic demo scenario that can be triggered from the UI.

Example:

"Run Recovery Demo"

It should allow the judge to observe:

FAILED
    ↓
ROOT CAUSE
    ↓
XGBOOST
    ↓
AI AGENT
    ↓
POLICY
    ↓
QUEUED
    ↓
EXECUTING
    ↓
RECOVERED

The demo must use the real Phase 4 backend flow.

Do NOT fake the animation in the frontend.

The backend state should actually change.

If a dedicated demo endpoint is needed, implement it safely and clearly mark it as demo/simulation functionality.

---

# 30. FRONTEND ARCHITECTURE

Prefer a clean structure such as:

frontend/
├── src/
│   ├── api/
│   ├── components/
│   │   ├── dashboard/
│   │   ├── payments/
│   │   ├── recovery/
│   │   ├── intelligence/
│   │   └── audit/
│   ├── pages/
│   ├── hooks/
│   ├── lib/
│   ├── types/
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── ...

Adapt this to the existing repository if necessary.

Avoid huge monolithic React components.

---

# 31. TYPE SAFETY

Use TypeScript types for API responses.

Do not use `any` throughout the application.

Define shared frontend types for:

- transaction
- prediction
- root cause
- agent decision
- policy decision
- recovery
- audit event
- dashboard metrics

Handle nullable/optional fields correctly.

---

# 32. SECURITY

Do not:

- expose secrets
- put API keys in frontend code
- trust frontend authorization
- bypass backend policy checks
- implement business rules only in the frontend

The backend remains the authority.

---

# 33. PERFORMANCE

Avoid unnecessary API calls.

Use sensible:

- caching
- memoization
- polling intervals
- pagination if needed

Do not poll every second indefinitely.

---

# 34. TESTING

Add frontend tests for critical behavior.

At minimum:

- dashboard renders
- transaction list renders
- transaction details render
- prediction visualization renders
- policy state renders
- recovery state changes render
- human approval action calls backend
- error state renders
- API failures are handled
- demo flow can be initiated

Do not require the real LLM during frontend tests.

---

# 35. PRODUCTION BUILD

Verify:

npm run build

(or the appropriate project command)

The production build must complete successfully.

Also verify:

- no TypeScript errors
- no obvious console errors
- no broken routes
- API integration works
- Docker setup remains functional if applicable

---

# 36. DO NOT IMPLEMENT

Do NOT introduce:

- Kubernetes
- Kafka
- microservices
- GraphQL
- CQRS
- event sourcing
- vector database
- unnecessary state-management frameworks
- unnecessary design patterns

Do not rewrite the existing backend architecture.

The frontend should consume the existing PayResQ system.

---

# 37. DEFINITION OF DONE

Phase 5 is complete when:

1. Professional frontend exists.
2. Application shell/navigation works.
3. Dashboard uses real backend data.
4. Payment/recovery list works.
5. Transaction detail page works.
6. XGBoost predictions are visualized.
7. Root-cause analysis is visible.
8. AI agent decision is visible.
9. Policy decision is visible.
10. Recovery timeline is visible.
11. Recovery status updates from backend.
12. Human approval workflow works.
13. Audit logs are visible.
14. Intelligence metrics are visible.
15. Demo recovery flow works through the real backend.
16. Loading/error/empty states are polished.
17. Responsive layout works.
18. Frontend tests pass.
19. Production build succeeds.
20. No fake business data is used for normal application views.
21. Synthetic/demo data is clearly labeled.

---

# 38. FINAL DEMO EXPERIENCE

The final judge experience should be:

Open PayResQ
    ↓
See dashboard
    ↓
See revenue at risk
    ↓
See failed payment
    ↓
Open transaction
    ↓
See why it failed
    ↓
See XGBoost probabilities
    ↓
See AI decision
    ↓
See policy approval
    ↓
Watch recovery timeline
    ↓
See worker execute
    ↓
See SUCCESS
    ↓
See recovered revenue
    ↓
Open audit trail
    ↓
Understand exactly what happened

The entire experience should feel like a real fintech operations product rather than a hackathon prototype.

---

# 39. STOP CONDITION

This is Phase 5 only.

Do not introduce unrelated infrastructure.

Do not rewrite completed Phase 1–4 functionality unless necessary for frontend integration.

After completion, report:

1. Final frontend architecture
2. Pages created
3. Components created
4. API integrations
5. New backend endpoints, if any
6. Demo flow
7. Responsive behavior
8. Accessibility considerations
9. Frontend tests
10. Production build result
11. Screenshots or descriptions of major screens
12. Any known limitations
13. Any remaining polish recommendations