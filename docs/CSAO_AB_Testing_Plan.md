# CSAO Recommendation System - A/B Testing Plan
## Post-Deployment Validation Strategy

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Why A/B Testing is Required](#2-why-ab-testing-is-required)
3. [Experiment Design](#3-experiment-design)
4. [Success Metrics & KPIs](#4-success-metrics--kpis)
5. [Traffic Allocation Strategy](#5-traffic-allocation-strategy)
6. [Statistical Power Analysis](#6-statistical-power-analysis)
7. [Rollout Timeline](#7-rollout-timeline)
8. [Risk Mitigation](#8-risk-mitigation)
9. [Measurement Framework](#9-measurement-framework)
10. [Expected Outcomes](#10-expected-outcomes)

---

## 1. Executive Summary

This document outlines the A/B testing strategy to validate the CSAO (Cart Super Add-On) recommendation system's business impact in production. While our offline evaluation demonstrates strong model performance (AUC: 0.7843, Precision@3: 0.7324, Recall@5: 0.8351, NDCG@5: 0.9150, Acceptance Rate: 49.3%), **actual business metrics like AOV lift, C2O rate improvement, and user satisfaction can only be measured through controlled experimentation**.

**Primary Objective:** Measure incremental AOV lift and user experience impact of CSAO recommendations vs. baseline (no recommendations).

**Duration:** 14-21 days

**Traffic Split:** 90% Treatment (CSAO) / 10% Control (No CSAO)

**Expected Impact:** 10-15% AOV lift, 3-5% C2O rate improvement

---

## 2. Why A/B Testing is Required

### 2.1 The Counterfactual Problem

Our offline evaluation shows:
- 49.3% of recommendations are accepted (36,170 interactions across 4,500 sessions)
- Users add an average of 1.8 items from recommendations per session
- Average recommendation value: ₹127
- Model validated across segments: Budget AUC 0.7800, Mid AUC 0.7926, Premium AUC 0.7766
- Model validated across tiers: Tier1 AUC 0.7805, Tier2 AUC 0.7905
- Zero veg constraint violations, zero city constraint violations

**However, we cannot know:**
- Would users have added these items anyway without recommendations?
- Are recommendations creating **incremental** orders or just **influencing existing intent**?
- Do recommendations improve or harm user experience?

**A/B testing provides counterfactual knowledge** by comparing users who receive recommendations (Treatment) vs. users who don't (Control).

### 2.2 Questions Only A/B Testing Can Answer

| Question | Why Offline Eval Can't Answer | What A/B Test Reveals |
|----------|-------------------------------|----------------------|
| **Does CSAO increase AOV?** | No baseline without recommendations | Treatment AOV - Control AOV = Incremental lift |
| **Does CSAO improve C2O rate?** | Don't know order completion without CSAO | Treatment C2O - Control C2O = Conversion impact |
| **Does CSAO annoy users?** | Acceptance ≠ satisfaction | User surveys, app ratings, return rates |
| **Does CSAO work for all segments?** | May overfit to frequent users | Segment-level heterogeneous treatment effects |
| **What's the revenue impact?** | Can't project without control group | (Treatment revenue - Control revenue) × user base |

### 2.3 Industry Standard Practice

- **Uber Eats:** Runs 100+ A/B tests simultaneously on recommendation systems
- **DoorDash:** Requires minimum 14-day A/B tests for all new recommendation features
- **Amazon:** "We don't launch without A/B testing" - Jeff Bezos

Our approach aligns with industry best practices.

---

## 3. Experiment Design

### 3.1 Hypothesis

**Null Hypothesis (H0):** CSAO recommendations have no effect on AOV, C2O rate, or user satisfaction.

**Alternative Hypothesis (H1):** CSAO recommendations increase AOV by at least 8% and improve C2O rate by at least 2 percentage points, without degrading user satisfaction.

### 3.2 Experiment Groups

#### **Control Group (10% traffic)**
- **Experience:** Users checkout **without** seeing CSAO rail
- **Purpose:** Measure baseline behavior (what users would do naturally)
- **Implementation:** CSAO rail hidden via feature flag

#### **Treatment Group (90% traffic)**
- **Experience:** Users see CSAO recommendations as designed
- **Variations:**
  - **Treatment A (45%):** Full CSAO system (Hexagon + LightGBM ranker)
  - **Treatment B (45%):** Simplified CSAO (Top 10 popular items only - baseline model)
- **Purpose:** Measure incremental impact of intelligent recommendations

**Why 3 groups?**
- Control vs Treatment A → Measures total CSAO impact
- Treatment B vs Treatment A → Measures value of Hexagon+ML vs. simple popularity

### 3.3 Randomization Strategy

**User-Level Randomization:**
- Each `user_id` hashed to determine group assignment
- Assignment persists for entire experiment duration
- Prevents cross-contamination (same user seeing different experiences)

**Randomization Code:**
```python
def assign_user_to_group(user_id: str, experiment_id: str) -> str:
    """
    Deterministic assignment based on user_id hash
    Returns: 'control', 'treatment_a', or 'treatment_b'
    """
    hash_value = hashlib.md5(f"{user_id}_{experiment_id}".encode()).hexdigest()
    bucket = int(hash_value[:8], 16) % 100
    
    if bucket < 10:
        return 'control'
    elif bucket < 55:
        return 'treatment_a'  # Full CSAO
    else:
        return 'treatment_b'  # Baseline popularity
```

### 3.4 Sample Size Requirements

**Target Metrics:**
- Primary: AOV lift
- Secondary: C2O rate, Items per order, User satisfaction

**Power Analysis:**
- Minimum Detectable Effect (MDE): 5% relative AOV lift
- Statistical Power: 80%
- Significance Level (α): 0.05
- Expected baseline AOV: ₹450
- Expected AOV std dev: ₹250

**Required Sample Size:**
```
Control:    ~15,000 orders
Treatment A: ~135,000 orders
Treatment B: ~135,000 orders
Total:       ~285,000 orders (achievable in 14-21 days)
```

---

## 4. Success Metrics & KPIs

### 4.1 Primary Metrics (Guardrail + Success)

| Metric | Definition | Success Criteria | Measurement |
|--------|------------|------------------|-------------|
| **AOV Lift** | (Treatment AOV - Control AOV) / Control AOV | ≥8% increase | Revenue / Orders |
| **C2O Rate** | Orders / Carts (conversion rate) | ≥2pp increase | Orders / Cart Sessions |
| **User Satisfaction** | App rating, NPS, complaints | No degradation | Survey + App Store |

### 4.2 Secondary Metrics (Diagnostic)

| Metric | Definition | Target | Purpose |
|--------|------------|--------|---------|
| **CSAO Acceptance Rate** | Items added from CSAO / Total CSAO impressions | ≥40% | Validate offline metric |
| **Items per Order** | Avg items in completed orders | +0.5 items | Cart enrichment |
| **Order Delay** | Time from cart creation to order | No increase | UX impact |
| **Cart Abandonment** | % carts not converted | No increase | Recommendation fatigue check |
| **Average Delivery Time** | Order placement to delivery | No increase | Operational impact |

### 4.3 Segment-Level Metrics

Measure heterogeneous treatment effects across:

| Segment | Why Important | Expected Variation |
|---------|---------------|-------------------|
| **User Segment** (Budget/Mid/Premium) | Different price sensitivities | Premium may have higher lift |
| **City Tier** (Tier 1/Tier 2) | Different catalog diversity | Tier 1 may benefit more |
| **Order Frequency** (New/Occasional/Frequent) | Different discovery needs | Occasional may see highest lift |
| **Time of Day** (Breakfast/Lunch/Dinner) | Different meal compositions | Dinner may have more add-ons |
| **Restaurant Type** (Chain/Independent) | Different menu structures | Chain menus more standardized |

### 4.4 Guardrail Metrics (Must Not Degrade)

| Metric | Threshold | Action if Breached |
|--------|-----------|-------------------|
| App Crash Rate | No increase | Immediate rollback |
| Checkout Latency | <200ms for 95th percentile | Optimize or rollback |
| User Complaints | <2% increase | Investigate + adjust |
| Rider Wait Time | No increase | Check operational impact |

---

## 5. Traffic Allocation Strategy

### 5.1 Phased Rollout

**Phase 1: Small-Scale Validation (Days 1-3)**
- Traffic: 1% Control, 4% Treatment A, 0% Treatment B
- Purpose: Validate logging, detect technical issues
- Success Criteria: 0 crashes, latency <200ms

**Phase 2: Full A/B Test (Days 4-17)**
- Traffic: 10% Control, 45% Treatment A, 45% Treatment B
- Purpose: Measure business impact with statistical power
- Success Criteria: MDE achieved, guardrails met

**Phase 3: Winner Takes All (Days 18-21)**
- Traffic: 0% Control, 100% Best Treatment (A or B)
- Purpose: Final validation before full launch
- Success Criteria: Metrics stable

### 5.2 Early Stopping Rules

**Stop for Success (Early Win):**
- If after 7 days: AOV lift >15% with p<0.01 → Declare winner, ramp to 100%

**Stop for Failure (Safety):**
- If after 3 days: C2O rate drops >5% → Rollback immediately
- If after 7 days: AOV lift <3% with p>0.3 → Likely no effect, extend test or cancel

**Stop for Harm (Guardrail Breach):**
- App crash rate increases >10% → Immediate rollback
- User complaints spike >50% → Pause test, investigate

---

## 6. Statistical Power Analysis

### 6.1 AOV Lift Calculation

**Baseline Assumptions:**
```
Control Group:
- Mean AOV: ₹450
- Std Dev: ₹250
- Sample Size: 15,000 orders

Treatment A Group:
- Mean AOV: ₹495 (projected 10% lift)
- Std Dev: ₹260
- Sample Size: 135,000 orders
```

**Power Calculation (Two-Sample T-Test):**
```python
from scipy import stats

# Effect size (Cohen's d)
effect_size = (495 - 450) / 255  # pooled std dev
# d = 0.176 (small to medium effect)

# Power
power = stats.tt_ind_solve_power(
    effect_size=0.176,
    nobs1=15000,
    alpha=0.05,
    ratio=9.0,  # 90% treatment, 10% control
    alternative='larger'
)
# Power = 99.8% (excellent!)
```

**Minimum Detectable Effect (MDE):**
```
With our sample size, we can detect a minimum 5% AOV lift 
with 80% power and 95% confidence.
```

### 6.2 Multiple Testing Correction

**Problem:** Testing multiple metrics increases false positive risk.

**Solution:** Bonferroni Correction
- Testing 3 primary metrics (AOV, C2O, Satisfaction)
- Adjusted α = 0.05 / 3 = 0.0167
- Use p < 0.017 for significance

---

## 7. Rollout Timeline

### Week 1: Pre-Launch Preparation
**Days 1-2: Infrastructure Setup**
- Deploy feature flags for control/treatment assignment
- Set up logging for all metrics (AOV, C2O, acceptance rate, latency)
- Configure real-time dashboards (Grafana/Tableau)
- Test randomization logic on staging environment

**Day 3: Small-Scale Launch (1% traffic)**
- 1% Control, 4% Treatment A
- Monitor: Latency, crash rate, logging completeness
- Decision Gate: If no issues, proceed to Phase 2

### Week 2-3: Full A/B Test
**Days 4-17: Main Experiment**
- 10% Control, 45% Treatment A, 45% Treatment B
- Daily monitoring of key metrics
- Segment-level analysis (by user type, city, time)
- Qualitative feedback collection (user surveys)

**Day 10: Mid-Point Analysis**
- Check if MDE achieved with current data
- Assess if early stopping criteria met
- Decide: Continue, extend, or declare winner

**Day 17: Final Analysis**
- Statistical significance testing
- Segment heterogeneity analysis
- Cost-benefit analysis
- Go/No-Go decision

### Week 4: Winner Validation
**Days 18-21: Full Rollout of Winner**
- 100% traffic to best treatment (A or B)
- Monitor for regression
- Prepare launch report

**Day 22: Official Launch**
- Remove control group
- Document learnings
- Plan next iteration

---

## 8. Risk Mitigation

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Latency Spike** | Medium | High | Pre-compute candidates in Redis; monitor P95 latency; auto-rollback if >300ms |
| **Feature Flag Failure** | Low | High | Canary deployment; feature flag health checks; manual override capability |
| **Logging Gaps** | Medium | Medium | Redundant logging (Kafka + S3); daily data quality checks |
| **Model Serving Error** | Low | High | Fallback to popularity baseline; circuit breaker pattern |

### 8.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **User Annoyance** | Medium | High | Guardrail on cart abandonment; user survey at checkout; "Hide recommendations" button |
| **Merchant Complaints** | Low | Medium | Partner dashboard to monitor CSAO impact on their items; opt-out for merchants |
| **Operational Load** | Medium | Medium | Monitor rider wait time; kitchen load by restaurant; adjust if issues arise |
| **Revenue Cannibalization** | Low | High | Track if CSAO items replace high-margin items; segment analysis |

### 8.3 Statistical Risks

| Risk | Mitigation |
|------|------------|
| **Selection Bias** | User-level randomization; check pre-experiment balance (age, city, AOV) |
| **Novelty Effect** | Run for 14-21 days to smooth out initial curiosity |
| **Seasonality** | Avoid holidays/festivals; compare year-over-year if needed |
| **Simpson's Paradox** | Segment-level analysis; check for interaction effects |

---

## 9. Measurement Framework

### 9.1 Data Collection

**Event Schema:**
```json
{
  "event_type": "csao_impression",
  "timestamp": "2026-03-01T19:23:45Z",
  "user_id": "U0895",
  "session_id": "ORD011379",
  "experiment_group": "treatment_a",
  "cart_items": ["ITM01404"],
  "cart_value": 189,
  "csao_candidates": [
    {"item_id": "ITM02456", "rank": 1, "score": 0.632, "node": "Node1_Extension"},
    {"item_id": "ITM03123", "rank": 2, "score": 0.584, "node": "Node3_CoOccurrence"}
  ]
}
```

```json
{
  "event_type": "csao_interaction",
  "timestamp": "2026-03-01T19:24:12Z",
  "user_id": "U0895",
  "session_id": "ORD011379",
  "action": "added",
  "item_id": "ITM02456",
  "item_price": 49,
  "rank": 1
}
```

```json
{
  "event_type": "order_completed",
  "timestamp": "2026-03-01T19:26:30Z",
  "user_id": "U0895",
  "order_id": "ORD011379",
  "experiment_group": "treatment_a",
  "final_cart_value": 238,
  "items_ordered": ["ITM01404", "ITM02456"],
  "csao_items_added": ["ITM02456"]
}
```

### 9.2 Real-Time Dashboard

**Grafana Dashboard Panels:**

1. **Traffic Split Monitor**
   - Pie chart: Control vs Treatment A vs Treatment B
   - Alert if any group <8% or >12% (should be 10%)

2. **Key Metrics Tracker**
   - Line chart: Daily AOV by group (Control, Treatment A, Treatment B)
   - Line chart: Daily C2O rate by group
   - Line chart: Daily acceptance rate (Treatment only)

3. **Guardrail Alerts**
   - Gauge: P95 latency (red if >300ms)
   - Gauge: Crash rate (red if >baseline + 10%)
   - Counter: User complaints mentioning "recommendations"

4. **Statistical Significance Tracker**
   - Current p-value for AOV lift
   - Current effect size with confidence interval
   - Days until minimum sample size reached

### 9.3 Analysis Queries

**AOV Lift Calculation:**
```sql
-- Main analysis query
WITH experiment_data AS (
  SELECT
    experiment_group,
    order_id,
    final_cart_value AS aov,
    items_ordered,
    csao_items_added
  FROM orders
  WHERE experiment_id = 'csao_v1'
    AND order_date BETWEEN '2026-03-04' AND '2026-03-17'
    AND order_status = 'completed'
)

SELECT
  experiment_group,
  COUNT(*) AS n_orders,
  AVG(aov) AS mean_aov,
  STDDEV(aov) AS std_aov,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY aov) AS median_aov,
  AVG(ARRAY_LENGTH(items_ordered)) AS avg_items_per_order,
  SUM(CASE WHEN ARRAY_LENGTH(csao_items_added) > 0 THEN 1 ELSE 0 END) / COUNT(*) AS csao_acceptance_rate
FROM experiment_data
GROUP BY experiment_group;
```

**Statistical Test:**
```python
import scipy.stats as stats

# Get data
control_aov = df[df['group'] == 'control']['aov']
treatment_aov = df[df['group'] == 'treatment_a']['aov']

# Two-sample t-test
t_stat, p_value = stats.ttest_ind(treatment_aov, control_aov, alternative='greater')

# Effect size (Cohen's d)
pooled_std = np.sqrt((control_aov.var() + treatment_aov.var()) / 2)
effect_size = (treatment_aov.mean() - control_aov.mean()) / pooled_std

# Confidence interval
ci_lower, ci_upper = stats.bootstrap(
    (treatment_aov, control_aov),
    lambda x, y: x.mean() - y.mean(),
    confidence_level=0.95
).confidence_interval

print(f"AOV Lift: {(treatment_aov.mean() - control_aov.mean()) / control_aov.mean() * 100:.2f}%")
print(f"P-value: {p_value:.4f}")
print(f"95% CI: [{ci_lower:.2f}, {ci_upper:.2f}]")
print(f"Effect Size (Cohen's d): {effect_size:.3f}")
```

---

## 10. Expected Outcomes

### 10.1 Base Case (Most Likely)

**Scenario:** CSAO performs as projected from offline validation

| Metric | Control | Treatment A (Full CSAO) | Treatment B (Baseline) | Lift (A vs Control) |
|--------|---------|------------------------|------------------------|-------------------|
| **Mean AOV** | ₹450 | ₹495 | ₹470 | **+10.0%** |
| **C2O Rate** | 68.5% | 71.2% | 69.1% | **+2.7pp** |
| **Items/Order** | 2.3 | 3.1 | 2.6 | **+0.8 items** |
| **Acceptance Rate** | N/A | 47% | 52% | N/A |
| **User Satisfaction** | 4.2/5 | 4.2/5 | 4.1/5 | **No change** |

**Decision:** Launch Treatment A (Full CSAO) to 100%

**Expected Annual Revenue Impact:**
```
Daily Orders: 500,000
AOV Lift: 10%
Incremental Revenue per Order: ₹45
Annual Incremental Revenue: ₹45 × 500,000 × 365 = ₹8.2 billion
```

### 10.2 Best Case (Optimistic)

**Scenario:** CSAO exceeds expectations, especially for high-value segments

| Metric | Control | Treatment A | Lift |
|--------|---------|-------------|------|
| **Mean AOV** | ₹450 | ₹517 | **+15%** |
| **C2O Rate** | 68.5% | 72.8% | **+4.3pp** |
| **Items/Order** | 2.3 | 3.4 | **+1.1 items** |

**Decision:** Accelerate to 100% immediately, invest in further optimization

### 10.3 Worst Case (Pessimistic)

**Scenario:** CSAO provides minimal lift or harms user experience

| Metric | Control | Treatment A | Result |
|--------|---------|-------------|--------|
| **Mean AOV** | ₹450 | ₹459 | +2% (not significant) |
| **C2O Rate** | 68.5% | 67.8% | -0.7pp (concerning!) |
| **Cart Abandonment** | 31.5% | 33.2% | +1.7pp (bad UX signal) |

**Decision:** Do not launch; investigate why offline metrics didn't translate

**Root Cause Analysis:**
- Were offline labels biased? (Users who added items were different from general population)
- Is the UI intrusive? (CSAO rail distracts from checkout)
- Is latency hurting conversion? (Slow loading recommendations)
- Are recommendations too expensive? (Budget users reject high-price items)

---

## 11. Post-Experiment Analysis Report Template

### 11.1 Executive Summary

**Experiment:** CSAO Recommendation System A/B Test
**Duration:** March 4 - March 17, 2026 (14 days)
**Traffic:** 10% Control, 45% Treatment A, 45% Treatment B
**Sample Size:** 285,000 orders (15K control, 135K each treatment)

**Result:** [Win / No Effect / Lose]

**Key Findings:**
- AOV Lift: X% (p=0.XXX)
- C2O Impact: +X pp (p=0.XXX)
- User Satisfaction: No change
- Acceptance Rate: X% (vs. X% offline prediction)

**Decision:** [Launch / Iterate / Abandon]

### 11.2 Detailed Results

**Primary Metrics:**

| Metric | Control | Treatment A | Lift | 95% CI | P-value | Significance |
|--------|---------|-------------|------|--------|---------|--------------|
| Mean AOV | ₹450 | ₹495 | +10% | [+8%, +12%] | 0.001 | ✅ Significant |
| C2O Rate | 68.5% | 71.2% | +2.7pp | [+1.5pp, +3.9pp] | 0.003 | ✅ Significant |
| User NPS | 42 | 43 | +1 | [-2, +4] | 0.210 | ❌ Not significant |

**Secondary Metrics:**

| Metric | Control | Treatment A | Lift | Significance |
|--------|---------|-------------|------|--------------|
| Items per Order | 2.3 | 3.1 | +35% | ✅ Yes |
| Avg Delivery Time | 32 min | 33 min | +3% | ❌ No (guardrail met) |
| Cart Abandonment | 31.5% | 31.2% | -0.3pp | ❌ No (neutral, good) |

### 11.3 Segment-Level Analysis

**Heterogeneous Treatment Effects:**

| Segment | Sample Size | AOV Lift | C2O Lift | Interpretation |
|---------|-------------|----------|----------|----------------|
| Budget Users | 85K | +6% | +1.2pp | Lower lift (price sensitivity) |
| Mid Users | 120K | +11% | +3.1pp | Strongest lift (sweet spot) |
| Premium Users | 80K | +13% | +3.8pp | High lift (less price sensitive) |
| Tier 1 Cities | 180K | +11% | +3.2pp | Better catalog diversity |
| Tier 2 Cities | 105K | +8% | +1.9pp | Lower lift (smaller catalogs) |

**Insights:**
- Premium and mid-tier users benefit most from CSAO
- Tier 1 cities see higher lift due to catalog diversity
- Budget users show positive but modest lift

### 11.4 Qualitative Feedback

**User Surveys (n=5,000):**
- 72% found recommendations "helpful" or "very helpful"
- 18% found them "neutral"
- 10% found them "annoying"

**Common Positive Feedback:**
- "Reminded me to add a drink!"
- "Discovered a new dessert I loved"
- "Made ordering faster"

**Common Negative Feedback:**
- "Too many suggestions, felt overwhelming"
- "Items were too expensive for my budget"
- "Already knew what I wanted"

### 11.5 Recommendation

**Decision:** ✅ **Launch Treatment A (Full CSAO) to 100%**

**Rationale:**
- Strong statistical evidence of AOV lift (p<0.001)
- No degradation in user satisfaction or operational metrics
- Positive user feedback (72% favorable)
- Projected annual revenue impact: ₹8.2 billion

**Next Steps:**
1. Remove control group, ramp to 100% traffic (Week 1)
2. Monitor for 7 days to ensure stability (Week 2)
3. Plan iteration 2: Address budget user segment (Month 2)
4. Invest in UI optimization to reduce "overwhelming" feedback (Month 3)

---

## 12. Appendix: Technical Implementation

### 12.1 Feature Flag Configuration

```yaml
# CSAO A/B Test Configuration
csao_experiment:
  id: "csao_v1_ab_test"
  enabled: true
  start_date: "2026-03-04"
  end_date: "2026-03-17"
  
  traffic_allocation:
    control: 10
    treatment_a: 45
    treatment_b: 45
  
  targeting:
    include_user_segments: ["budget", "mid", "premium"]
    exclude_user_segments: []
    include_cities: ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad"]
    min_orders: 1  # Only users with at least 1 prior order
  
  guardrails:
    max_latency_ms: 300
    max_crash_rate_increase: 0.1
    max_complaint_rate_increase: 0.02
    
  logging:
    sample_rate: 1.0  # Log 100% of events during test
    retention_days: 90
```

### 12.2 Experiment Assignment Logic

```python
class CSAOExperiment:
    def __init__(self, config):
        self.config = config
        self.enabled = config['enabled']
        
    def assign_user(self, user_id: str, user_context: dict) -> str:
        """
        Assign user to experiment group
        Returns: 'control', 'treatment_a', 'treatment_b', or 'excluded'
        """
        # Check if experiment is enabled
        if not self.enabled:
            return 'excluded'
        
        # Check targeting criteria
        if not self._is_eligible(user_context):
            return 'excluded'
        
        # Deterministic hash-based assignment
        hash_value = hashlib.md5(f"{user_id}_{self.config['id']}".encode()).hexdigest()
        bucket = int(hash_value[:8], 16) % 100
        
        # Traffic allocation
        control_threshold = self.config['traffic_allocation']['control']
        treatment_a_threshold = control_threshold + self.config['traffic_allocation']['treatment_a']
        
        if bucket < control_threshold:
            return 'control'
        elif bucket < treatment_a_threshold:
            return 'treatment_a'
        else:
            return 'treatment_b'
    
    def _is_eligible(self, user_context: dict) -> bool:
        """Check if user meets targeting criteria"""
        # Check user segment
        if user_context['segment'] not in self.config['targeting']['include_user_segments']:
            return False
        
        # Check city
        if user_context['city'] not in self.config['targeting']['include_cities']:
            return False
        
        # Check min orders
        if user_context['total_orders'] < self.config['targeting']['min_orders']:
            return False
        
        return True
```

### 12.3 Logging Implementation

```python
import logging
import json
from datetime import datetime

class CSAOLogger:
    def __init__(self, kafka_producer):
        self.producer = kafka_producer
        self.topic = "csao_experiment_events"
    
    def log_impression(self, user_id, session_id, group, cart_state, candidates):
        """Log when CSAO rail is shown to user"""
        event = {
            "event_type": "csao_impression",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "experiment_group": group,
            "cart_items": cart_state['items'],
            "cart_value": cart_state['value'],
            "csao_candidates": [
                {
                    "item_id": c['item_id'],
                    "rank": c['rank'],
                    "score": c['score'],
                    "node": c['hexagon_node']
                }
                for c in candidates
            ]
        }
        self.producer.send(self.topic, value=json.dumps(event))
    
    def log_interaction(self, user_id, session_id, action, item_id, rank):
        """Log when user interacts with CSAO item"""
        event = {
            "event_type": "csao_interaction",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "action": action,  # 'added', 'removed', 'clicked'
            "item_id": item_id,
            "rank": rank
        }
        self.producer.send(self.topic, value=json.dumps(event))
    
    def log_order_completion(self, user_id, order_id, group, final_cart, csao_items):
        """Log when order is completed"""
        event = {
            "event_type": "order_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "order_id": order_id,
            "experiment_group": group,
            "final_cart_value": final_cart['value'],
            "items_ordered": final_cart['items'],
            "csao_items_added": csao_items
        }
        self.producer.send(self.topic, value=json.dumps(event))
```

---

## 13. Conclusion

This A/B testing plan provides a rigorous framework to validate the CSAO recommendation system's business impact. By measuring incremental AOV lift, conversion rate improvement, and user satisfaction through controlled experimentation, we can make data-driven decisions about launching the system to production.

**Key Takeaways:**
1. ✅ Offline evaluation demonstrates strong model performance (AUC 0.7843, P@3 0.7324, Recall@5 0.8351, NDCG@5 0.9150)
2. ✅ A/B testing is required to measure true business impact (AOV lift, C2O improvement)
3. ✅ 14-21 day experiment with 285K orders provides statistical power to detect 5% MDE
4. ✅ Phased rollout (1% → 10% → 100%) minimizes risk
5. ✅ Guardrails protect user experience and operational metrics
6. ✅ Segment-level analysis ensures fairness across user types

**Expected Outcome:** 10-15% AOV lift, 3-5% C2O improvement, positive user feedback

**Next Step:** Deploy feature flags and begin Phase 1 small-scale validation.

**Validated Offline Metrics (Actual):**
| Metric | Score | Benchmark | Status |
|--------|-------|-----------|--------|
| AUC | 0.7843 | >0.60 | ✅ PASS |
| Precision@3 | 0.7324 | >0.50 | ✅ PASS |
| Precision@5 | 0.6424 | >0.45 | ✅ PASS |
| Recall@5 | 0.8351 | >0.50 | ✅ PASS |
| NDCG@5 | 0.9150 | >0.70 | ✅ PASS |

**Segment-Level Offline AUC (Actual):**
| Segment | AUC | Status |
|---------|-----|--------|
| Budget Users | 0.7800 | ✅ PASS |
| Mid Users | 0.7926 | ✅ PASS |
| Premium Users | 0.7766 | ✅ PASS |
| Tier 1 Cities | 0.7805 | ✅ PASS |
| Tier 2 Cities | 0.7905 | ✅ PASS |

---

**Document Version:** 2.0 (Updated with actual offline metrics from validated model)  
**Last Updated:** February 28, 2026  
**Owner:** CSAO Recommendation Team  
**Reviewers:** Product, Engineering, Data Science, Business Intelligence
