# Design Partner Acquisition Playbook

**Version:** 1.0
**Date:** 2025-12-16
**Goal:** Acquire 10-50 design partners in 90 days
**Owner:** Founder/Growth Lead

---

## Table of Contents

1. [30-Day Sprint to First 10 Partners](#30-day-sprint-to-first-10-partners)
2. [Identifying Target Companies](#identifying-target-companies)
3. [Outreach Strategies & Templates](#outreach-strategies--templates)
4. [Discovery Call Framework](#discovery-call-framework)
5. [Design Partner Onboarding](#design-partner-onboarding)
6. [Engagement & Feedback Loop](#engagement--feedback-loop)
7. [Success Tracking](#success-tracking)

---

## 30-Day Sprint to First 10 Partners

### Week 1: Preparation & Pipeline Building

**Day 1-2: Build Target List (50-100 companies)**

- [ ] **LinkedIn Sales Navigator Search**
  - Filter: 10-500 employees, Computer Software industry
  - Job titles: VP Engineering, CTO, Engineering Manager
  - Keywords: "AWS", "A/B testing", "feature flags", "experimentation"
  - Export to CSV

- [ ] **YCombinator Directory**
  - Filter by: B2B SaaS, developer tools, infrastructure
  - Check LinkedIn for AWS mentions
  - Add to target list if AWS-heavy

- [ ] **AWS Community Research**
  - AWS subreddit active posters
  - AWS Community Slack members
  - Companies mentioned in AWS case studies
  - AWS Marketplace partners

- [ ] **GitHub Search**
  - Search: "feature flags" OR "feature toggles" in repositories
  - Filter: Companies with 10-100 stars, active development
  - Check company profiles for AWS usage

- [ ] **Competitor Research**
  - LaunchDarkly customers (check LinkedIn mentions)
  - Statsig users (Twitter, LinkedIn)
  - Split.io case studies
  - Target companies evaluating or unhappy with incumbents

**Output:** Airtable/spreadsheet with 50-100 companies
**Columns:** Company Name, Industry, Size, Contact (LinkedIn URL), Notes, Status

**Day 3-4: Research & Personalization**

For each target company, research:
- [ ] Recent funding rounds (Crunchbase)
- [ ] Tech stack (BuiltWith, job postings)
- [ ] AWS usage signals (job postings, blog posts)
- [ ] Current experimentation setup (blog mentions, job postings)
- [ ] Mutual connections (LinkedIn)
- [ ] Pain points (company blog, Glassdoor, Twitter)

**Create Personalized Snippets:**
```
Company: Acme Corp
Personalization: Recently raised Series A ($10M), hiring DevOps engineers,
building on AWS (5 Lambda engineers), using LaunchDarkly (mentioned in blog)
Hook: "Saw you're scaling on AWS and using LaunchDarkly—we've helped similar
companies reduce their experimentation costs by 50% while improving performance."
```

**Day 5-7: Warm Up Channels**

- [ ] **LinkedIn Optimization**
  - Update headline: "Building AWS-native experimentation platform | Helping teams ship faster"
  - Add recent posts about AWS, experimentation, product development
  - Engage with target companies' content (like, thoughtful comment)

- [ ] **Join Communities**
  - AWS Community Slack
  - DevOps Slack groups
  - YC Work at a Startup
  - Indie Hackers
  - Product Hunt Ship

- [ ] **Establish Credibility**
  - Publish 1 technical blog post ("AWS Lambda Performance Optimization")
  - Share on r/aws, AWS Slack, LinkedIn
  - Aim for 100+ views, 5+ comments

### Week 2: Outreach Blitz (Target: 5 Demo Calls, 3 Partners)

**Daily Routine:**

**Morning (9-11am): Outreach (10 messages/day)**
- 5 LinkedIn InMails (personalized)
- 5 Email outreach (highly researched)
- Track in CRM (Airtable/HubSpot)

**Midday (11am-12pm): Community Engagement**
- Answer 2-3 questions on r/aws, Stack Overflow
- Comment on 5 LinkedIn posts from target companies
- Share valuable content (not pitching)

**Afternoon (2-4pm): Follow-ups & Demo Calls**
- Follow up with non-responders (after 3-5 days)
- Conduct demo calls (30-45 min each)
- Send follow-up emails with next steps

**Evening (5-6pm): Content & Research**
- Write LinkedIn post (building in public, insights)
- Research next batch of companies
- Update tracking spreadsheet

**Week 2 Goals:**
- [ ] 70 outreach messages sent (10/day × 7 days)
- [ ] 5 demo calls booked
- [ ] 3 design partners signed
- [ ] 15% response rate minimum

### Week 3: Referrals & Scaling (Target: 7 More Partners = 10 Total)

**Leverage First Partners:**
- [ ] Ask each partner: "Who else do you know who might benefit from this?"
- [ ] Request LinkedIn introduction (make it easy with template)
- [ ] Offer incentive: "1 month free for each referral that becomes a partner"

**Expand Outreach Channels:**
- [ ] Post in AWS Community Slack (#general, #show-and-tell)
  - "Building AWS-native A/B testing platform, looking for beta partners"
- [ ] Reddit post on r/aws
  - "Show & Tell: Open Beta for AWS-Native Experimentation Platform"
- [ ] Twitter thread
  - Technical deep-dive with CTA for beta access
- [ ] Indie Hackers post
  - "Launching beta: AWS-native alternative to LaunchDarkly"

**Week 3 Goals:**
- [ ] 100 total outreach messages (cumulative)
- [ ] 3+ referrals from first partners
- [ ] 10 total design partners signed
- [ ] 1 LinkedIn post with 500+ impressions

### Week 4: Consolidation & Activation (Target: Maintain 10, Activate All)

**Focus on Activation:**
- [ ] 1-on-1 onboarding calls with inactive partners
- [ ] Weekly office hours (2× per week)
- [ ] Email campaign: "Getting Started with Experimently in 30 Minutes"
- [ ] Create video tutorials for common use cases

**Gather Testimonials:**
- [ ] Ask activated partners for quick quote
- [ ] Record 30-second video testimonials
- [ ] Get permission to use company logo

**Week 4 Goals:**
- [ ] 80%+ activation rate (8/10 partners with first experiment)
- [ ] 5 written testimonials
- [ ] 2 video testimonials
- [ ] 3 LinkedIn recommendations

---

## Identifying Target Companies

### Qualification Criteria (BANT Framework)

**Budget:**
- [ ] Currently paying for LaunchDarkly, Statsig, Optimizely, or Split.io
- [ ] OR allocating engineering time to maintain in-house solution
- [ ] OR budget for new experimentation tool ($0-$5K/month)

**Authority:**
- [ ] Contact is Engineering Manager, VP Eng, CTO, or PM with budget authority
- [ ] OR has strong influence on tooling decisions
- [ ] Can make decision within 30 days

**Need:**
- [ ] Experiencing pain with current solution (cost, performance, complexity)
- [ ] OR evaluating new experimentation tools
- [ ] OR running experiments manually without proper tooling

**Timeline:**
- [ ] Willing to start beta within 2 weeks
- [ ] Can commit to 60-90 day design partner engagement
- [ ] Available for weekly feedback calls

### Finding Companies

#### LinkedIn Sales Navigator Searches

**Search 1: AWS-Heavy Companies Using Competitors**
```
- Company size: 10-500 employees
- Industry: Computer Software, Internet, SaaS
- Keywords: "AWS" AND ("LaunchDarkly" OR "Statsig" OR "feature flags")
- Job title filter: VP Engineering, Director Engineering, CTO
```

**Search 2: Companies Hiring for Experimentation Roles**
```
- Job postings containing: "A/B testing" OR "experimentation" OR "feature flags"
- Posted in last 30 days
- Location: United States, Europe (if targeting)
- Company size: 10-500 employees
```

**Search 3: AWS Community Advocates**
```
- Posts containing: "AWS" AND ("Lambda" OR "serverless" OR "DynamoDB")
- Job title: Engineering Manager, CTO, VP Engineering, Staff Engineer
- Company size: 10-500 employees
- Posted in last 90 days
```

#### GitHub Search Strategies

**Search for Feature Flag Usage:**
```
language:JavaScript "feature-flag" OR "featureFlag" stars:10..1000
language:Python "feature_flag" OR "feature-flags" stars:10..1000
```

**Look for:**
- Active development (commits in last 30 days)
- Team size (multiple contributors)
- Professional setup (CI/CD, testing)
- AWS mentions in README or deployment docs

**Outreach via GitHub:**
- Star their repo
- Open a relevant issue or PR (add value first)
- Mention Experimently in context (not spammy)

#### YCombinator Directory

**Filter:**
- [ ] B2B Software
- [ ] Developer Tools
- [ ] Infrastructure
- [ ] Recently funded (last 12 months)

**Research Each Company:**
1. Visit company website → check for "Careers" or "Tech Stack" page
2. Look for AWS mentions (AWS logo, job postings, blog)
3. Check LinkedIn for engineering team size
4. Read blog posts for technical depth

**Prioritize:**
- YC current batch (highest priority)
- Series A/B companies (growing fast, need better tools)
- AWS Activate participants

#### AWS Community Engagement

**AWS Subreddit (r/aws):**
- [ ] Find users posting about Lambda, serverless, DynamoDB
- [ ] Check post history for company affiliation
- [ ] DM with value-first message: "Saw your Lambda performance post—here's how we optimized to <50ms..."

**AWS Community Slack:**
- [ ] Monitor #general, #serverless, #containers channels
- [ ] Engage in conversations (help first, pitch later)
- [ ] Build relationships over 2-3 weeks

**AWS Meetups (Virtual or Local):**
- [ ] Attend AWS meetups as participant
- [ ] Network with attendees
- [ ] Offer to give lightning talk about AWS architecture

#### Competitor Customer Research

**LaunchDarkly Customers:**
- Search LinkedIn: "LaunchDarkly" (filter by Engineering Manager, etc.)
- Check testimonials page for customer logos
- Research companies, note pain points

**Statsig Users:**
- Twitter search: "Statsig" OR "@statsig"
- Find users tweeting about Statsig
- Check LinkedIn profile, company

**Target Messaging:**
"Saw you're using [Competitor]. We've built an AWS-native alternative that's 50% cheaper with <50ms latency. Would love to show you a quick demo."

### Target Company List Template

Use Airtable or Google Sheets:

| Company | Industry | Size | Contact Name | Title | LinkedIn URL | Mutual Connections | Pain Point | Status | Next Action | Notes |
|---------|----------|------|--------------|-------|--------------|-------------------|------------|--------|-------------|-------|
| Acme Corp | Dev Tools | 50 | Jane Doe | VP Eng | linkedin.com/in/janedoe | John Smith | High LD costs | Researching | Draft email | Raised Series A |

**Status Values:**
- Researching
- Outreach Sent
- Follow-up Needed
- Demo Scheduled
- Demo Completed
- Design Partner (Signed!)
- Not Interested
- No Response

---

## Outreach Strategies & Templates

### Channel Priority

**Tier 1 (Warm Introductions):**
1. Mutual connection introduction
2. Existing community member (Slack, etc.)
3. Referral from design partner

**Tier 2 (Direct Outreach):**
1. LinkedIn InMail (personalized)
2. Email (researched)
3. Twitter DM (if active on Twitter)

**Tier 3 (Community Engagement):**
1. Comment on LinkedIn post → DM
2. Answer question on Reddit → DM
3. Engage in Slack → DM

### Email Templates

#### Template 1: Cold Email (AWS-Heavy Company)

**Subject:** AWS-native alternative to LaunchDarkly?

```
Hi [First Name],

Saw [Company Name] is [specific observation: hiring DevOps engineers / building
on AWS Lambda / mentioned in AWS case study]. Congrats on [recent achievement:
funding round / product launch / team growth]!

Quick question: are you using LaunchDarkly or Statsig for experimentation?

We're building Experimently, an AWS-native A/B testing platform that integrates
directly with your existing AWS infrastructure. We're seeing teams:

✅ Cut experimentation costs by 50% (vs. LaunchDarkly)
✅ Reduce latency to <50ms P99 (vs. 100-150ms with competitors)
✅ Integrate in 30 minutes (vs. 2-3 days)

We're looking for 10-15 design partners to help shape the product. In exchange
for feedback, you get:
• Free access for 6-12 months
• Direct input on roadmap
• Dedicated Slack channel with our team

Would a 20-minute call this week make sense to explore fit?

Best,
[Your Name]
Founder, Experimently
[Calendar Link]

P.S. Here's a 2-minute demo: [Loom Link]
```

**When to Use:** Cold outreach to AWS-heavy companies
**Expected Response Rate:** 5-10%
**Follow-up:** After 5 days if no response

#### Template 2: LinkedIn InMail (Warm-ish Introduction)

**Subject:** Fellow AWS builder—quick question

```
Hey [First Name],

Noticed we're both in [AWS Community Slack / attended AWS Summit / etc.].
I've been following [Company Name]'s work on [specific project/blog post]—
really impressive approach to [specific technical challenge].

I'm building an AWS-native experimentation platform (think LaunchDarkly,
but built specifically for AWS infrastructure). Currently looking for 5-10
design partners who:

• Are heavy AWS users (Lambda, DynamoDB, etc.)
• Need A/B testing / feature flags
• Want to influence product direction

In return: Free access + direct line to our engineering team.

Worth a quick chat? I promise to keep it to 15-20 minutes.

Cheers,
[Your Name]
[Calendar Link]
```

**When to Use:** Warm-ish connection, shared community
**Expected Response Rate:** 15-25%
**Follow-up:** After 4 days if no response

#### Template 3: Referral Request (For Existing Partners)

**Subject:** Quick favor: 1-2 intros?

```
Hi [Partner Name],

Hope the onboarding is going smoothly! Wanted to check in and see if you need
any help getting your first experiment up and running.

Quick ask: Do you know 1-2 other engineering leaders who might benefit from
Experimently? Ideally folks who:

• Are building on AWS
• Need A/B testing or feature flags
• Would give honest product feedback

Happy to make it easy—here's a template you can forward:

---
"Hey [Name],

I'm working with Experimently, an AWS-native A/B testing platform. They're
looking for design partners (free access in exchange for feedback).

Seems like a good fit for [Company Name] given your AWS infrastructure.

Worth a quick chat? Here's the founder's calendar: [Link]

Let me know if you want an intro."
---

Thanks for considering!

[Your Name]

P.S. For each referral that becomes a partner, you'll get 1 month free when
we launch paid tiers.
```

**When to Use:** After successful onboarding (Day 7-14)
**Expected Response Rate:** 30-50% provide intros
**Follow-up:** Thank immediately, update partner on referral status

#### Template 4: Community Post (AWS Subreddit / Slack)

**Subject:** [Show & Tell] AWS-Native A/B Testing Platform - Looking for Beta Partners

```
Hey AWS community!

I've been building Experimently, an A/B testing and feature flag platform
designed specifically for AWS infrastructure. After 6 months of development,
we're ready for beta partners.

**The problem we're solving:**
- LaunchDarkly / Statsig are expensive ($500-$2K/mo) and not AWS-native
- Building in-house experimentation is complex and time-consuming
- Existing tools don't integrate well with AWS services (Lambda, DynamoDB, etc.)

**What makes Experimently different:**
✅ Built on AWS primitives (Lambda, DynamoDB, Kinesis)
✅ <50ms P99 latency (vs. 100-150ms competitors)
✅ 30-minute integration
✅ 50% cheaper than LaunchDarkly/Statsig
✅ Full API access + SDKs (JS, Python)

**What we're looking for:**
10-15 design partners who:
• Are heavy AWS users
• Need A/B testing / feature flags
• Will provide candid feedback

**What you get:**
• Free access for 6-12 months
• Direct input on roadmap
• Dedicated support via Slack

**Tech stack:** FastAPI, PostgreSQL Aurora, Lambda, DynamoDB, Redis, Next.js

Interested? Drop a comment or DM me. Happy to share architecture details
if folks are curious!

Demo: [Link]
Docs: [Link]
```

**When to Use:** Week 2-3 of outreach, after some traction
**Expected Response Rate:** 2-5% of viewers engage
**Follow-up:** Respond to all comments within 1 hour

### Follow-Up Sequences

**Email Follow-up #1 (Day 5):**

```
Subject: Re: AWS-native alternative to LaunchDarkly?

Hi [Name],

Following up on my email from last week about Experimently (AWS-native
experimentation platform).

Totally understand if now's not the right time. If you are curious, here's
a 2-minute demo video that shows the core features: [Loom Link]

Happy to answer any questions!

Best,
[Your Name]
```

**Email Follow-up #2 (Day 12):**

```
Subject: Worth a conversation?

[Name],

Last attempt! We've signed 5 design partners in the past 2 weeks (including
[Notable Company if you have one]), and the feedback has been great.

If you're still interested in:
✅ Cutting experimentation costs by 50%
✅ Getting <50ms feature flag evaluation
✅ Integrating with AWS in 30 minutes

...let's chat for 15 minutes this week.

Here's my calendar: [Link]

If it's not a fit, no worries—I'll stop bugging you!

Cheers,
[Your Name]
```

**LinkedIn Follow-up (Day 7):**

```
[Name], circling back on my InMail about Experimently. We're helping AWS-heavy
companies like [Company X] reduce experimentation costs by 50%.

Worth a quick chat? Here's a 2-min demo: [Link]
```

### Response Handling

**Positive Response:**
```
Great to hear from you! Let's schedule a call. Here are a few times that work
for me this week:
- Tuesday 2-4pm PT
- Wednesday 10am-12pm PT
- Thursday 1-3pm PT

Or feel free to grab time directly on my calendar: [Calendly Link]

Looking forward to it!
```

**"Not Right Now" Response:**
```
Totally understand! When would be a better time to reconnect?

In the meantime, I'll add you to our monthly newsletter (you can unsubscribe
anytime) so you stay updated on our progress.

Thanks for your time!
```

**"Too Expensive" (even though it's free for partners):**
```
Just to clarify—design partners get free access for 6-12 months in exchange
for feedback. The goal is to learn from users like you and build the right product.

Once we launch paid tiers (in ~6 months), you'll get 50% off as a design partner.

Does that change things?
```

**"We Use LaunchDarkly / Statsig" Response:**
```
Great! We've actually helped several teams migrate from [LaunchDarkly/Statsig].

The main reasons they switched:
1. Cost (50% savings)
2. Performance (<50ms vs. 100-150ms)
3. AWS-native integration

Happy to show you a comparison in a quick 15-min call. We also have a migration
guide that makes switching easy.

Interested in seeing how we compare?
```

---

## Discovery Call Framework

### Pre-Call Preparation (5-10 minutes)

- [ ] Review company website, LinkedIn, blog
- [ ] Understand their AWS usage (job postings, blog posts)
- [ ] Research current experimentation setup (if mentioned publicly)
- [ ] Prepare 2-3 personalized questions
- [ ] Have demo environment ready
- [ ] Review design partner agreement

### Call Structure (30-45 minutes)

**1. Intro & Agenda (3 min)**

"Thanks for taking the time! Here's what I'd like to cover in the next 30 minutes:
1. Learn about your current experimentation setup and challenges (10 min)
2. Show you a quick demo of Experimently (10 min)
3. Discuss design partner program and next steps (10 min)

Sound good?"

**2. Discovery Questions (10 min)**

**Current Setup:**
- "How are you currently running A/B tests or managing feature flags?"
- "What tools are you using? (LaunchDarkly, Statsig, in-house, etc.)"
- "How long have you been using [current solution]?"

**Pain Points:**
- "What's working well with your current setup?"
- "What's not working well? What frustrates you?"
- "If you could wave a magic wand and fix one thing, what would it be?"

**AWS Usage:**
- "I noticed you're using AWS—what services are you using? (Lambda, ECS, etc.)"
- "How important is AWS integration for your tooling?"

**Decision Process:**
- "Who else would need to be involved in evaluating a new experimentation tool?"
- "What would a successful pilot look like for you?"
- "What's your timeline for making a decision?"

**Budget & Alternatives:**
- "What are you paying for [current tool] today?"
- "Have you evaluated other alternatives? What did you think?"

**3. Demo (10 min)**

**Focus on Pain Points:**
Based on discovery, tailor demo to address their specific challenges.

**Demo Flow:**
1. **Quick value prop (30 sec):** "Experimently is an AWS-native A/B testing platform..."
2. **Create experiment (2 min):** Show how easy it is to set up
3. **Targeting & segmentation (2 min):** Show advanced targeting
4. **SDK integration (2 min):** Show 30-minute integration
5. **Real-time analytics (2 min):** Show results dashboard
6. **Highlight AWS integration (1 min):** Lambda, DynamoDB, etc.
7. **Answer questions (2 min)**

**4. Design Partner Program Explanation (5 min)**

"We're looking for 10-15 design partners to help us build the right product. Here's how it works:

**What you get:**
• Free access for 6-12 months (worth $1,200-$2,400)
• Direct input on roadmap (we'll build what you need)
• Dedicated Slack channel with our team
• Priority support
• 50% discount when we launch paid tiers

**What we ask in return:**
• 30-minute onboarding call to get you set up
• Bi-weekly feedback calls for first 8 weeks (30 min each)
• Honest feedback on what's working and what's not
• Willingness to be a reference (case study / testimonial)

**Sound fair?**"

**5. Next Steps (5 min)**

**If interested:**
- [ ] Send design partner agreement via DocuSign
- [ ] Schedule onboarding call (within 7 days)
- [ ] Add to Slack channel
- [ ] Send welcome email with resources

**If needs to think about it:**
- [ ] "What questions can I answer to help you make a decision?"
- [ ] Set follow-up call (within 5-7 days)
- [ ] Send follow-up email with key points

**If not a fit:**
- [ ] "Totally understand. Can I ask what's holding you back?"
- [ ] "Anyone else you know who might be a better fit?"
- [ ] Add to newsletter for future updates

**6. Wrap-Up (2 min)**

"Thanks so much for your time! I'll send over [next steps] within 24 hours.

Any other questions before we wrap?"

### Post-Call Actions (Within 24 hours)

- [ ] Send thank you email
- [ ] Send design partner agreement (if interested)
- [ ] Schedule onboarding call
- [ ] Update CRM with notes and next steps
- [ ] Add to internal Slack (share feedback with team)
- [ ] Send calendar invite for onboarding

### Call Notes Template

```
Company: [Name]
Contact: [Name, Title]
Date: [Date]
Call Duration: [X min]

CURRENT SETUP:
- Using: [Tool or in-house]
- Team size: [X engineers, X PMs]
- AWS services: [Lambda, ECS, etc.]
- Monthly spend on experimentation: $[X]

PAIN POINTS:
1. [Pain point 1]
2. [Pain point 2]
3. [Pain point 3]

KEY OBJECTIONS / CONCERNS:
1. [Concern 1]
2. [Concern 2]

INTEREST LEVEL:
[High / Medium / Low]

DECISION TIMELINE:
[Immediate / 2-4 weeks / 1-3 months / No timeline]

NEXT STEPS:
- [ ] [Action item 1]
- [ ] [Action item 2]

NOTES:
[Any other relevant info]
```

---

## Design Partner Onboarding

### Onboarding Call Agenda (30-45 min)

**1. Welcome & Goals (5 min)**

"Thanks for becoming a design partner! Today's goal is to get you up and running
with your first experiment in the next 30 minutes.

Before we dive in, tell me: What's the first use case you want to test?"

**2. Account Setup (5 min)**

- [ ] Create account (if not already done)
- [ ] Set up organization/team
- [ ] Invite team members
- [ ] Set up permissions (RBAC)

**3. First Experiment Creation (15 min)**

**Live walkthrough:**
- [ ] Create experiment (guided tutorial)
- [ ] Set up treatment variants
- [ ] Configure targeting rules
- [ ] Define metrics
- [ ] Preview and activate

**4. SDK Integration (10 min)**

**JavaScript SDK:**
```javascript
// Install
npm install @experimently/sdk

// Initialize
import { ExperimentlyClient } from '@experimently/sdk';

const client = new ExperimentlyClient({
  apiKey: 'your-api-key'
});

// Get assignment
const variant = await client.getAssignment({
  experimentKey: 'homepage-hero-test',
  userId: user.id
});

// Track event
client.track({
  eventName: 'button_click',
  userId: user.id,
  properties: { buttonColor: variant.value }
});
```

**Test in browser console:**
- [ ] Verify SDK initialization
- [ ] Test assignment retrieval
- [ ] Track test event

**5. Results & Analytics (5 min)**

- [ ] Show real-time event dashboard
- [ ] Explain statistical significance
- [ ] Set up alerts and notifications

**6. Next Steps (5 min)**

- [ ] Add to design partner Slack channel
- [ ] Schedule first feedback call (in 7 days)
- [ ] Share resources:
  - Documentation
  - Video tutorials
  - Example implementations
  - FAQ

### Onboarding Email

**Subject:** Welcome to Experimently Design Partner Program!

```
Hey [Name],

Welcome to the Experimently Design Partner Program! 🎉

Here's everything you need to get started:

📚 RESOURCES:
• Documentation: [Link]
• API Reference: [Link]
• Video Tutorials: [Link]
• Example Code: [GitHub Link]

🔑 YOUR CREDENTIALS:
• Dashboard: [URL]
• API Key: [Key] (keep this secret!)
• Team ID: [ID]

💬 SUPPORT:
• Design Partner Slack: [Invite Link]
• Email: [Support Email]
• Office Hours: Tuesdays & Thursdays 2-3pm PT ([Calendly Link])

📅 UPCOMING:
• First Feedback Call: [Date/Time] ([Calendar Link])

QUICK START (30 minutes):
1. Log in to dashboard
2. Create your first experiment
3. Install SDK: npm install @experimently/sdk
4. Integrate and test
5. View results

Questions? Drop me a message on Slack or email. We're here to help!

Looking forward to working with you!

[Your Name]
Founder, Experimently
```

### Activation Checklist (First 7 Days)

- [ ] **Day 1:** Account created, onboarding call completed
- [ ] **Day 2:** First experiment created
- [ ] **Day 3:** SDK integrated in dev/staging environment
- [ ] **Day 4:** First event tracked
- [ ] **Day 5:** Experiment running in production
- [ ] **Day 6:** First 100+ events tracked
- [ ] **Day 7:** First result viewed, feedback call scheduled

**If not activated by Day 7:**
- [ ] Send nudge email with helpful resources
- [ ] Offer 1-on-1 support call
- [ ] Troubleshoot blockers

---

## Engagement & Feedback Loop

### Weekly Touchpoints

**Week 1-2: High-Touch Support**
- **Frequency:** Every 2-3 days
- **Channel:** Slack + Email
- **Focus:** Onboarding, troubleshooting, quick wins

**Week 3-8: Regular Feedback**
- **Frequency:** Bi-weekly calls (30 min)
- **Channel:** Zoom + Slack
- **Focus:** Feature feedback, use case exploration, roadmap input

**Week 9+: Maintenance**
- **Frequency:** Monthly check-ins
- **Channel:** Email + Slack
- **Focus:** Long-term success, case study development, testimonials

### Feedback Call Template

**1. How's it going? (5 min)**
- Overall satisfaction (1-10)
- Any blockers or issues?
- Wins or success stories?

**2. Usage review (5 min)**
- Number of experiments running
- Events tracked
- Team adoption
- Features being used

**3. Product feedback (15 min)**
- What's working well?
- What's frustrating or confusing?
- What features are you missing?
- If you had a magic wand, what would you change?

**4. Roadmap discussion (5 min)**
- Share upcoming features
- Get input on priorities
- Validate assumptions

**5. Next steps (5 min)**
- Any action items for us?
- Any action items for you?
- Schedule next call

### Feedback Tracking

**Use Airtable or Notion to track:**

| Date | Partner | Feedback Type | Category | Priority | Status | Notes |
|------|---------|---------------|----------|----------|--------|-------|
| 2025-12-01 | Acme Corp | Feature Request | Targeting | High | Planned | Need geo-targeting |
| 2025-12-02 | Beta Inc | Bug Report | SDK | Critical | Fixed | SDK crash on iOS |
| 2025-12-03 | Acme Corp | UX Feedback | Dashboard | Medium | Backlog | Results page confusing |

**Categories:**
- Feature Request
- Bug Report
- UX Feedback
- Performance Issue
- Documentation Gap

**Priority:**
- Critical (blocking usage)
- High (major pain point)
- Medium (nice-to-have)
- Low (future consideration)

---

## Success Tracking

### Partner Health Score

**Score each partner monthly (0-100):**

| Metric | Weight | Scoring |
|--------|--------|---------|
| **Usage** | 40% | Weekly active: 10, 2-3x/month: 5, <2x/month: 0 |
| **Engagement** | 30% | Feedback calls attended: 10, 1 missed: 7, 2+ missed: 0 |
| **Adoption** | 20% | Production usage: 10, Staging only: 5, Not integrated: 0 |
| **Advocacy** | 10% | Testimonial + referrals: 10, Testimonial: 7, Nothing: 0 |

**Health Tiers:**
- 🟢 **Healthy (80-100):** Highly engaged, great fit, likely to convert
- 🟡 **At Risk (50-79):** Moderate engagement, needs attention
- 🔴 **Churning (<50):** Low usage, may drop off

**Actions by Tier:**
- 🟢 Ask for case study, referrals, testimonial
- 🟡 Schedule 1-on-1 to understand blockers
- 🔴 Last-ditch effort or let go gracefully

### Key Milestones to Track

**Per Partner:**
- [ ] Signed design partner agreement
- [ ] Completed onboarding call
- [ ] Created first experiment
- [ ] Tracked first event
- [ ] Experiment running in production
- [ ] 1,000+ events tracked
- [ ] Attended 3+ feedback calls
- [ ] Provided testimonial
- [ ] Made 1+ referral
- [ ] Converted to paid (or committed to convert)

**Overall Program:**
- [ ] 10 design partners signed (Week 4)
- [ ] 25 design partners signed (Week 8)
- [ ] 50 design partners signed (Week 12)
- [ ] 80%+ activation rate
- [ ] 70%+ health score (avg across partners)
- [ ] 10+ testimonials collected
- [ ] 3+ case studies published
- [ ] 15+ referrals generated

---

## Appendix: Additional Resources

### Design Partner Agreement Template

See: `docs/go-to-market/design-partner-agreement-template.md`

### Feedback Survey Template

See: `docs/go-to-market/feedback-survey.md`

### Case Study Interview Guide

See: `docs/go-to-market/case-study-interview-guide.md`

---

**Last Updated:** 2025-12-16
**Next Review:** Every 30 days
**Owner:** Founder/Growth Lead
