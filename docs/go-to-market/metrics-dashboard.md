# Go-to-Market Metrics & Success Dashboard

**Version:** 1.0
**Date:** 2025-12-16
**Purpose:** Track and measure GTM success for beta launch
**Owner:** Founder/Growth Lead

---

## Table of Contents

1. [North Star Metric](#north-star-metric)
2. [Key Performance Indicators (KPIs)](#key-performance-indicators-kpis)
3. [Metric Definitions](#metric-definitions)
4. [Weekly Dashboard](#weekly-dashboard)
5. [Monthly Business Review](#monthly-business-review)
6. [Cohort Analysis](#cohort-analysis)
7. [Partner Health Scoring](#partner-health-scoring)
8. [Data Collection & Tools](#data-collection--tools)

---

## North Star Metric

### Definition

**Weekly Active Design Partners Creating Experiments (WADPCE)**

A design partner is "weekly active" if they:
- Log in at least once in the past 7 days, AND
- Create at least one experiment OR track at least 100 events

### Why This Metric?

This single metric captures:
- **Acquisition:** How many partners have we signed?
- **Activation:** Have they set up and created their first experiment?
- **Engagement:** Are they using the product regularly?
- **Value Delivery:** Are they running experiments (core use case)?

### Targets

| Time Period | Target | Rationale |
|-------------|--------|-----------|
| Week 4 | 7 | 70% of 10 partners actively using |
| Week 8 | 18 | 72% of 25 partners actively using |
| Week 12 | 35 | 70% of 50 partners actively using |

### How to Improve

**If too low:**
- Improve onboarding (reduce time to first experiment)
- Increase engagement (email campaigns, office hours)
- Better partner selection (choose engaged partners)
- Address blockers (1-on-1 calls with inactive partners)

---

## Key Performance Indicators (KPIs)

### Acquisition Metrics

#### 1. Design Partners Signed

**Definition:** Total number of companies that signed design partner agreement

**Formula:** COUNT(partners WHERE status = 'active' AND agreement_signed = true)

**Targets:**

| Week | Target | Cumulative |
|------|--------|------------|
| 2 | 3 | 3 |
| 4 | 7 | 10 |
| 6 | 8 | 18 |
| 8 | 7 | 25 |
| 10 | 12 | 37 |
| 12 | 13 | 50 |

**Calculation Frequency:** Daily
**Reporting Frequency:** Weekly

---

#### 2. Total Signups

**Definition:** Number of users who created an account (includes partners and non-partners)

**Formula:** COUNT(users WHERE account_created_at >= period_start)

**Targets:**

| Week | Weekly Signups | Cumulative |
|------|----------------|------------|
| 2 | 10 | 10 |
| 4 | 20 | 30 |
| 8 | 70 | 100 |
| 12 | 100 | 200 |

**Benchmark:** 10-20% of signups become design partners
**Warning Threshold:** <5 signups per week
**Action Item:** Review marketing channels, improve messaging

---

#### 3. Demo Calls Booked

**Definition:** Number of calls scheduled via Calendly or manually

**Formula:** COUNT(calendar_events WHERE type = 'demo' AND status != 'cancelled')

**Targets:**

| Week | Target |
|------|--------|
| 2 | 5 |
| 4 | 15 |
| 8 | 40 |
| 12 | 80 |

**Conversion Funnel:**
```
100 Website Visitors
  → 10 Signups (10% conversion)
    → 5 Demo Requests (50% conversion)
      → 3 Demos Completed (60% show-up rate)
        → 2 Partners Signed (67% close rate)
```

**Warning Threshold:** <3 demos per week
**Action Item:** Increase outreach, improve value prop on website

---

#### 4. Website Traffic

**Definition:** Unique visitors to website (experimently.com)

**Formula:** COUNT(DISTINCT user_id) in Google Analytics

**Targets:**

| Week | Target | Source Breakdown |
|------|--------|------------------|
| 2 | 200 | 50% direct, 30% social, 20% organic |
| 4 | 500 | 40% direct, 30% social, 20% organic, 10% referral |
| 8 | 1,500 | 30% direct, 25% social, 25% organic, 20% referral |
| 12 | 3,000 | 25% direct, 25% social, 30% organic, 20% referral |

**Top Sources to Track:**
- Direct (type URL, bookmarks)
- Organic search (Google)
- Social (LinkedIn, Twitter, Reddit)
- Referral (blogs, HackerNews, communities)

**Warning Threshold:** <100 visitors per week
**Action Item:** Increase content marketing, community engagement

---

### Activation Metrics

#### 5. Activation Rate

**Definition:** Percentage of signups who create their first experiment within 7 days

**Formula:** (Users who created first experiment within 7 days / Total signups) × 100

**Target:** 70%+ (industry benchmark: 30-40%)

**Breakdown:**
- Day 1: 30% (immediate activation)
- Day 2-3: 25% (after first email nudge)
- Day 4-7: 15% (after onboarding call or follow-up)

**Warning Threshold:** <50% activation
**Action Item:** Improve onboarding flow, offer 1-on-1 onboarding calls

---

#### 6. Time to First Experiment

**Definition:** Median time from signup to first experiment created

**Formula:** MEDIAN(experiment_created_at - account_created_at)

**Target:** <30 minutes

**Distribution:**
- <10 min: 20% (power users)
- 10-30 min: 50% (following tutorial)
- 30-60 min: 20% (needed help)
- >60 min: 10% (struggled or dropped off)

**Warning Threshold:** >60 minutes median
**Action Item:** Simplify onboarding, improve docs, add in-app tutorial

---

#### 7. SDK Integration Rate

**Definition:** Percentage of partners who successfully integrated SDK

**Formula:** (Partners with first event tracked / Total partners) × 100

**Target:** 90%+

**Time to Integration:**
- Day 1-2: 40%
- Day 3-5: 30%
- Day 6-7: 20%
- Day 8+: 10%

**Warning Threshold:** <70% integration rate
**Action Item:** Simplify SDK, provide code examples, offer integration help

---

### Engagement Metrics

#### 8. Weekly Active Users (WAU)

**Definition:** Users who logged in at least once in the past 7 days

**Formula:** COUNT(DISTINCT user_id WHERE last_login >= NOW() - 7 days)

**Target:** 60%+ of total partners

**Cohort Breakdown:**
- Week 1 partners: 80% active
- Week 2-4 partners: 70% active
- Week 5-8 partners: 60% active
- Week 9+ partners: 50% active

**Warning Threshold:** <40% WAU
**Action Item:** Email re-engagement campaign, 1-on-1 outreach

---

#### 9. Experiments per Partner

**Definition:** Average number of experiments created per active partner

**Formula:** SUM(experiments) / COUNT(active_partners)

**Target:** 3+ experiments per partner

**Distribution:**
- 1 experiment: 20% (trying it out)
- 2-3 experiments: 40% (moderate usage)
- 4-10 experiments: 30% (active usage)
- 10+ experiments: 10% (power users)

**Warning Threshold:** <2 experiments per partner
**Action Item:** Share use case ideas, provide experiment templates

---

#### 10. Events Tracked per Partner

**Definition:** Average monthly events tracked per active partner

**Formula:** SUM(events_last_30_days) / COUNT(active_partners)

**Target:** 5,000+ events/month per partner

**Distribution:**
- <1K events: 20% (early stage / low traffic)
- 1K-10K events: 40% (typical usage)
- 10K-50K events: 30% (high usage)
- 50K+ events: 10% (very high usage)

**Warning Threshold:** <1,000 events/month per partner
**Action Item:** Check for integration issues, usage guidance

---

### Product Feedback Metrics

#### 11. Net Promoter Score (NPS)

**Definition:** Likelihood to recommend (0-10 scale)

**Formula:**
- Promoters (9-10): % who rated 9-10
- Detractors (0-6): % who rated 0-6
- NPS = % Promoters - % Detractors

**Target:** 40+ (considered excellent for early-stage product)

**Benchmark:**
- 40+: Excellent
- 20-40: Good
- 0-20: Needs improvement
- <0: Critical issues

**Survey Timing:** After 30 days of usage
**Frequency:** Monthly for each partner
**Sample Question:** "How likely are you to recommend Experimently to a colleague?"

---

#### 12. Product Feedback Sessions

**Definition:** Number of scheduled feedback calls completed

**Target:** 3+ per week

**Feedback Types:**
- Feature requests: LOG and categorize
- Bug reports: LOG and prioritize
- UX improvements: LOG and track
- General satisfaction: Capture NPS

**Warning Threshold:** <2 sessions per week
**Action Item:** Schedule more calls, send feedback survey

---

#### 13. Feature Requests Logged

**Definition:** Total number of unique feature requests from partners

**Target:** 50+ requests by Week 12

**Categorization:**
- Critical (blocking usage): Fix immediately
- High (major pain point): Prioritize for next sprint
- Medium (nice-to-have): Add to backlog
- Low (future consideration): Document for later

**Top Requests to Track:**
- [ ] Advanced targeting rules
- [ ] Multivariate testing
- [ ] Real-time dashboards
- [ ] Export functionality
- [ ] SSO/SAML integration

---

### Business Outcome Metrics

#### 14. Case Studies Published

**Definition:** Number of customer success stories published on website

**Target:** 3 by Week 12

**Requirements:**
- Written testimonial
- Quantified results (e.g., "50% cost savings")
- Company logo usage permission
- Quote from decision maker

**Timeline:**
- Identify candidate: Week 6-8
- Interview and draft: Week 8-10
- Review and approval: Week 10-12
- Publish: Week 12

---

#### 15. Testimonials Collected

**Definition:** Number of written or video testimonials

**Target:** 10 by Week 12

**Types:**
- Written (100-200 words)
- Video (30-60 seconds)
- LinkedIn recommendations
- G2/Capterra reviews (if applicable)

**Best Time to Ask:** After partner has achieved a win (first successful experiment, measurable result)

---

#### 16. Referrals Generated

**Definition:** Number of new signups from design partner referrals

**Target:** 15 by Week 12

**Tracking:**
- UTM parameter: ?ref=partner_name
- Referral code in signup form
- Ask in onboarding: "How did you hear about us?"

**Referral Rate:** 30% of partners make at least 1 referral

**Incentive:** 1 month free for each successful referral

---

#### 17. Paid Conversions

**Definition:** Number of design partners who converted to paid plan

**Target:** 5 by Week 12

**Conversion Triggers:**
- Hit free tier limit (10K events/month)
- Need advanced features (SSO, API access)
- Requested upgrade after seeing value

**Conversion Timeline:**
- <30 days: 10% (immediate need)
- 30-60 days: 20% (after seeing ROI)
- 60-90 days: 40% (end of free period)
- 90+ days: 30% (long-term users)

---

## Metric Definitions

### Activation

**Activated User:** Signed up AND created first experiment within 7 days

**Criteria:**
1. Account created
2. Email verified
3. First experiment created
4. First event tracked (optional but encouraged)

### Churn

**Churned Partner:** Inactive for 30+ days (no login, no events)

**Churn Rate:** (Churned partners / Total partners) × 100

**Target:** <10% monthly churn rate

**Churn Reasons to Track:**
- Product didn't fit needs
- Too complex / hard to use
- Went with competitor
- Budget constraints
- Company shut down / pivoted

### Engagement Tiers

**Tier 1 - Highly Engaged:**
- Login 5+ times per week
- Create 1+ experiment per week
- Track 10K+ events per month

**Tier 2 - Moderately Engaged:**
- Login 2-4 times per week
- Create 1 experiment per 2 weeks
- Track 1K-10K events per month

**Tier 3 - Low Engagement:**
- Login <2 times per week
- Create <1 experiment per month
- Track <1K events per month

**Tier 4 - At Risk:**
- No login in past 14 days
- No experiments created in past 30 days
- No events tracked in past 30 days

---

## Weekly Dashboard

### One-Page View (Update Every Monday)

```
╔══════════════════════════════════════════════════════════════════╗
║       EXPERIMENTLY - WEEKLY GTM DASHBOARD (Week X)              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  🎯 NORTH STAR METRIC                                           ║
║  Weekly Active Partners Creating Experiments: [25] / 35 target  ║
║  └─ Trend: ↑ +3 from last week                                  ║
║                                                                  ║
║  📊 ACQUISITION (This Week)                                     ║
║  • New Signups:             [15]     Target: 15    ✅           ║
║  • Design Partners Signed:  [3]      Target: 3     ✅           ║
║  • Demo Calls Booked:       [8]      Target: 10    ⚠️           ║
║  • Website Visitors:        [1,200]  Target: 1,500 ⚠️           ║
║                                                                  ║
║  ⚡ ACTIVATION                                                   ║
║  • Activation Rate:         [72%]    Target: 70%+  ✅           ║
║  • Time to First Exp:       [28 min] Target: <30   ✅           ║
║  • SDK Integration Rate:    [85%]    Target: 90%+  ⚠️           ║
║                                                                  ║
║  💪 ENGAGEMENT                                                   ║
║  • Weekly Active Users:     [25]     (60% of 42 total) ✅       ║
║  • Avg Experiments/Partner: [3.2]    Target: 3+    ✅           ║
║  • Avg Events/Partner:      [6.5K]   Target: 5K+   ✅           ║
║                                                                  ║
║  💬 FEEDBACK & PRODUCT                                          ║
║  • NPS Score:               [42]     Target: 40+   ✅           ║
║  • Feedback Sessions:       [4]      Target: 3+    ✅           ║
║  • Feature Requests:        [8 new]  (35 total)                 ║
║  • Critical Bugs:           [2]      (both fixed)               ║
║                                                                  ║
║  📈 BUSINESS OUTCOMES                                           ║
║  • Case Studies:            [1]      Target: 3     ⚠️           ║
║  • Testimonials:            [7]      Target: 10    ⚠️           ║
║  • Referrals:               [12]     Target: 15    ⚠️           ║
║  • Paid Conversions:        [3]      Target: 5     ⚠️           ║
║                                                                  ║
║  ⚠️  TOP 3 PRIORITIES THIS WEEK                                 ║
║  1. [ ] Complete 2 more case studies (interview partners)       ║
║  2. [ ] Increase demo bookings (launch LinkedIn campaign)       ║
║  3. [ ] Improve SDK integration rate (create video tutorial)    ║
║                                                                  ║
║  🎉 WINS THIS WEEK                                              ║
║  • Signed 3 new design partners (including [Notable Company])   ║
║  • NPS jumped from 38 to 42                                     ║
║  • Featured in AWS Community Slack #show-and-tell               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

### How to Create This Dashboard

**Tools (Free):**
- Google Sheets (manual updates)
- Notion (database + dashboard)
- Airtable (automated with Zapier)

**Data Sources:**
- Website: Google Analytics
- Product: PostHog/Mixpanel (self-hosted)
- CRM: Airtable/HubSpot
- Surveys: Typeform/Google Forms

**Update Frequency:** Every Monday morning (30-45 min)

---

## Monthly Business Review

### Format (First Monday of Month)

#### 1. Executive Summary (1 slide)

```
Month X Overview
─────────────────

🎯 Goal: Acquire 15 design partners
✅ Actual: 18 partners (+20% over goal)

💰 Spend: $150 (under $500 budget)
📊 CAC: $8.33 per partner ($150 / 18)

⭐ Top Win: Featured on HackerNews frontpage (5K visitors)
⚠️  Top Challenge: Activation rate dropped to 65% (from 75%)

Next Month Focus: Get to 35 total partners, publish 3 case studies
```

#### 2. Metrics Deep Dive (4 slides)

**Slide 1: Acquisition Funnel**
```
Month X Acquisition Funnel
──────────────────────────

10,000 Visitors
  ↓ 3% conversion
300 Signups
  ↓ 20% request demo
60 Demo Requests
  ↓ 70% show up
42 Demos Conducted
  ↓ 43% convert
18 Partners Signed

Insights:
• Top source: Reddit (r/aws) - 25% of traffic, 40% conversion
• Worst source: Twitter - 10% of traffic, 5% conversion
• Action: Double down on Reddit, pause Twitter ads
```

**Slide 2: Activation & Engagement**
```
Activation Performance
──────────────────────

✅ 65% activated (created first experiment within 7 days)
   - Week 1: 75% (good)
   - Week 2: 68% (acceptable)
   - Week 3: 58% (concerning)
   - Week 4: 60% (improved after onboarding changes)

Drop-off Points:
• 20% drop off at SDK integration (need better docs)
• 10% drop off at first experiment creation (UI confusion)
• 5% drop off at event tracking (technical issues)

Actions Taken:
✅ Created video tutorial for SDK integration
✅ Simplified experiment creation flow
✅ Added live chat support
```

**Slide 3: Product & Feedback**
```
Product Health
──────────────

NPS Trend: 35 → 38 → 42 → 45 (improving!)

Top Feature Requests (this month):
1. Advanced targeting (8 requests) → Planned for Q1
2. SSO/SAML login (6 requests) → Planned for Q2
3. Export to CSV (5 requests) → Shipped!
4. Real-time dashboards (4 requests) → Backlog

Bugs Fixed: 12 (avg resolution time: 36 hours)
```

**Slide 4: Business Outcomes**
```
Revenue & Growth Indicators
───────────────────────────

Paid Conversions: 3 (at $99/mo = $297 MRR)

Projected ARR (if all partners convert):
• 18 partners × $99/mo × 12 = $21,384 ARR
• Assumes 60% conversion rate = $12,830 ARR

Referrals: 12 new signups from partner referrals
Referral Rate: 22% of partners made at least 1 referral

Case Studies: 1 published, 2 in progress

Testimonials: 7 collected (4 written, 3 video)
```

#### 3. Next Month Plan (1 slide)

```
Month X+1 Goals & Strategy
──────────────────────────

🎯 PRIMARY GOAL: Reach 35 total design partners (+17 from current)

Key Initiatives:
1. Launch AWS Marketplace listing (10 new partners expected)
2. Publish 2 more case studies (increase credibility)
3. Host 2 webinars (50-100 attendees each)
4. Guest post on 3 high-traffic blogs

Metrics to Watch:
• Activation rate (get back to 70%+)
• Demo show-up rate (currently 70%, target 80%)
• Referral rate (currently 22%, target 30%)

Budget: $800 (AWS Marketplace listing + LinkedIn ads)
```

---

## Cohort Analysis

### Weekly Partner Cohorts

**Track Each Cohort:**

```
Cohort: Week 1 (Jan 1-7, 2026)
─────────────────────────────

Total Partners Signed: 10

WEEK 1 (Jan 1-7):
• Activated (first experiment): 8 (80%)
• Weekly Active: 9 (90%)
• Avg Experiments: 1.2
• Avg Events: 1,500

WEEK 2 (Jan 8-14):
• Weekly Active: 8 (80%)
• Avg Experiments: 2.5
• Avg Events: 4,200

WEEK 3 (Jan 15-21):
• Weekly Active: 7 (70%)
• Avg Experiments: 3.1
• Avg Events: 6,800

WEEK 4 (Jan 22-28):
• Weekly Active: 7 (70%)
• Avg Experiments: 3.8
• Avg Events: 8,500
• Paid Conversions: 2 (20%)

INSIGHTS:
✅ Strong activation (80%)
✅ Good retention (70% still active after 4 weeks)
⚠️  1 partner churned (inactive for 14+ days)
✅ Usage growing over time (good sign)
```

### Retention Curve

**Target Retention:**

| Week After Signup | Target Retention | Acceptable | Poor |
|-------------------|------------------|------------|------|
| Week 1 | 90%+ | 80-90% | <80% |
| Week 2 | 80%+ | 70-80% | <70% |
| Week 4 | 70%+ | 60-70% | <60% |
| Week 8 | 60%+ | 50-60% | <50% |
| Week 12 | 50%+ | 40-50% | <40% |

**Churn Prevention:**
- Email re-engagement at 7 days inactive
- Personal outreach at 14 days inactive
- "We miss you" campaign at 21 days inactive
- Mark as churned at 30 days inactive

---

## Partner Health Scoring

### Health Score Formula (0-100)

```
Health Score = (Usage × 40%) + (Engagement × 30%) + (Adoption × 20%) + (Advocacy × 10%)

USAGE (40 points):
• Weekly Active: 20 points (yes/no)
• Experiments Created: 10 points (1-2: 5pts, 3-5: 8pts, 5+: 10pts)
• Events Tracked: 10 points (<1K: 3pts, 1K-10K: 7pts, 10K+: 10pts)

ENGAGEMENT (30 points):
• Feedback Calls: 10 points (0: 0pts, 1-2: 5pts, 3+: 10pts)
• Response Rate: 10 points (responds <24hrs: 10pts, <48hrs: 7pts, >48hrs: 3pts)
• Feature Requests: 10 points (provided: 10pts, none: 0pts)

ADOPTION (20 points):
• Production Usage: 10 points (yes: 10pts, staging only: 5pts, no: 0pts)
• Team Size: 5 points (1 user: 2pts, 2-3: 4pts, 4+: 5pts)
• Advanced Features: 5 points (using targeting, multivariate, etc.)

ADVOCACY (10 points):
• Testimonial: 5 points (provided: 5pts, none: 0pts)
• Referrals: 5 points (1+: 5pts, none: 0pts)
```

### Health Tiers

**🟢 Healthy (80-100 points):**
- Highly engaged
- Production usage
- Likely to convert to paid
- **Action:** Ask for case study, referrals, testimonial

**🟡 At Risk (50-79 points):**
- Moderate engagement
- May need support
- Risk of churn
- **Action:** Schedule 1-on-1, understand blockers, provide help

**🔴 Churning (<50 points):**
- Low engagement
- Likely to drop off
- Not seeing value
- **Action:** Last-ditch effort (personalized email/call) or let go gracefully

### Partner Health Dashboard

```
╔══════════════════════════════════════════════════════════════╗
║  PARTNER HEALTH OVERVIEW (Week X)                            ║
╠══════════════════════════════════════════════════════════════╣
║  Total Partners: 42                                          ║
║                                                              ║
║  🟢 Healthy (80-100):    25 (60%)                           ║
║  🟡 At Risk (50-79):     12 (28%)                           ║
║  🔴 Churning (<50):      5 (12%)                            ║
║                                                              ║
║  📊 AVERAGE SCORES                                           ║
║  • Overall Health: 72 (🟡 Acceptable)                       ║
║  • Usage Score: 30/40                                       ║
║  • Engagement Score: 22/30                                  ║
║  • Adoption Score: 14/20                                    ║
║  • Advocacy Score: 6/10                                     ║
║                                                              ║
║  ⚠️  AT-RISK PARTNERS NEEDING ATTENTION                     ║
║  1. Acme Corp (Score: 52) - No login in 10 days            ║
║  2. Beta Inc (Score: 58) - Stuck on SDK integration        ║
║  3. Gamma LLC (Score: 61) - Not using in production        ║
║                                                              ║
║  🎉 TOP PERFORMING PARTNERS                                  ║
║  1. Delta Corp (Score: 95) - Heavy usage, 3 referrals      ║
║  2. Epsilon Inc (Score: 92) - Production, testimonial      ║
║  3. Zeta LLC (Score: 88) - 10+ experiments, engaged        ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Data Collection & Tools

### Free/Low-Cost Tool Stack

#### Product Analytics
**Tool:** PostHog (self-hosted, free)
**Tracks:**
- User signups
- First experiment created
- Events tracked
- Feature usage
- Time spent in app

**Setup:**
```javascript
// Frontend (Next.js)
import posthog from 'posthog-js';

posthog.init('API_KEY', {
  api_host: 'https://your-posthog-instance.com'
});

// Track events
posthog.capture('experiment_created', {
  experiment_id: id,
  type: 'ab_test'
});
```

#### Website Analytics
**Tool:** Google Analytics (free)
**Tracks:**
- Website visitors
- Traffic sources
- Conversion rates
- Bounce rates

**Setup:** Add GA tag to website

#### CRM
**Tool:** Airtable (free tier) or HubSpot (free tier)
**Tracks:**
- Partner contact info
- Outreach history
- Demo status
- Health scores

**Airtable Structure:**
```
Tables:
• Partners (name, email, status, health_score)
• Activities (calls, emails, feedback sessions)
• Metrics (weekly snapshots)
• Feature Requests
```

#### Feedback Collection
**Tool:** Typeform (free tier) or Google Forms
**Surveys:**
- NPS survey (monthly)
- Product feedback (after key milestones)
- Churn survey (when partner leaves)

#### Dashboards
**Tool:** Google Sheets or Notion (free)
**Update:** Manual weekly update (30-45 min)

**Google Sheets Template:**
- Tab 1: Weekly Dashboard
- Tab 2: Monthly Metrics
- Tab 3: Cohort Analysis
- Tab 4: Partner Health Scores
- Tab 5: Raw Data

---

## Metrics Automation (Optional)

### Zapier Workflows (Free Tier: 100 tasks/month)

**Workflow 1: New Signup → Slack**
- Trigger: New user in PostHog
- Action: Send Slack message to #growth channel

**Workflow 2: Demo Booked → CRM**
- Trigger: Calendly booking
- Action: Create row in Airtable

**Workflow 3: Partner Inactive → Email**
- Trigger: No login in 7 days (scheduled check)
- Action: Send re-engagement email via Mailchimp

### API Integrations

**Metrics API Endpoint:**
```python
# backend/app/api/v1/endpoints/metrics.py

@router.get("/metrics/weekly")
async def get_weekly_metrics():
    return {
        "north_star_metric": get_weekly_active_partners(),
        "acquisition": {
            "signups": get_signups_this_week(),
            "partners_signed": get_partners_signed_this_week(),
            "demos_booked": get_demos_this_week()
        },
        "activation": {
            "activation_rate": calculate_activation_rate(),
            "time_to_first_experiment": get_median_ttfe()
        },
        "engagement": {
            "wau": get_weekly_active_users(),
            "avg_experiments": get_avg_experiments_per_partner(),
            "avg_events": get_avg_events_per_partner()
        }
    }
```

**Dashboard Auto-Update:**
```python
# scripts/update_dashboard.py

import gspread
from metrics_api import get_weekly_metrics

# Connect to Google Sheets
gc = gspread.service_account()
sh = gc.open("GTM Dashboard")
worksheet = sh.worksheet("Weekly")

# Fetch metrics
metrics = get_weekly_metrics()

# Update cells
worksheet.update('B2', metrics['north_star_metric'])
worksheet.update('B4', metrics['acquisition']['signups'])
# ... etc
```

---

## Success Criteria

### By Week 12 (End of Beta Launch Phase)

**Acquisition:**
- ✅ 50+ design partners signed
- ✅ 200+ total signups
- ✅ <$1,000 total spend (CAC < $20)

**Activation:**
- ✅ 70%+ activation rate
- ✅ <30 min median time to first experiment
- ✅ 90%+ SDK integration rate

**Engagement:**
- ✅ 60%+ weekly active users
- ✅ 3+ experiments per active partner
- ✅ 5K+ events per partner per month

**Product:**
- ✅ NPS 40+
- ✅ <5 critical bugs open
- ✅ Top 10 feature requests documented

**Business Outcomes:**
- ✅ 3+ case studies published
- ✅ 10+ testimonials collected
- ✅ 15+ referrals generated
- ✅ 5+ paid conversions

**Overall Health:**
- ✅ 60%+ partners in "Healthy" tier (80-100 score)
- ✅ <15% churn rate
- ✅ Product-market fit validated (would be "very disappointed" if Experimently went away)

---

## Appendix: Metric Tracking Templates

### Weekly Metrics Spreadsheet

Download template: `docs/go-to-market/templates/weekly-metrics-template.xlsx` (to be created)

### Monthly Business Review Deck

Download template: `docs/go-to-market/templates/monthly-review-template.pptx` (to be created)

### Partner Health Score Calculator

Download template: `docs/go-to-market/templates/partner-health-calculator.xlsx` (to be created)

---

**Last Updated:** 2025-12-16
**Next Review:** Weekly (every Monday)
**Owner:** Founder/Growth Lead
