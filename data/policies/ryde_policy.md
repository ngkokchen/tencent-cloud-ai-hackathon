# Ryde Ride-Hailing Platform — Dispute Resolution Policy

> Version 2.1 — Effective October 1, 2026
> Applies to all disputes filed under the Ryde platform in Singapore.

---

## 1. Route Deviation Disputes

### 1.1 Definition

A route deviation dispute arises when a rider alleges that the driver
deviated from the navigation-recommended optimal route, resulting in a
higher fare (distance and/or time charges) than expected.

### 1.2 Optimal Route

The "optimal route" is the route recommended by the Ryde in-app
navigation system at the time of trip commencement. It is calculated
based on real-time traffic conditions and is logged with timestamps
and GPS waypoints at trip start.

### 1.3 Deviation Thresholds and Refund Tiers

| Deviation % | Additional distance | Refund action |
|-------------|--------------------|---------------|
| 0% – 10% | Within normal tolerance | No refund |
| 10% – 15% | Minor deviation | Refund fare difference if driver did not communicate |
| 15% – 30% | Significant deviation | Full refund of fare difference |
| > 30% | Major deviation | Full refund of fare difference + 50% of difference as goodwill credit |

**Deviation %** = ((actual_distance_km - optimal_distance_km) / optimal_distance_km) × 100

**Fare difference** = actual_total_fare - expected_total_fare (calculated using
optimal distance and estimated duration at the same surge multiplier).

### 1.4 Traffic Exception

If the driver can demonstrate that the optimal route was experiencing
heavy congestion (average vehicle speed < 20 km/h) at the time of the
trip, a deviation of up to 15% is considered justified and no refund
applies.

To qualify for the traffic exception, **all** of the following must hold:

1. The traffic congestion data must come from the Ryde traffic
   monitoring system (logged at trip time).
2. The driver must have informed the rider of the route change via
   in-app chat before or at the point of deviation.
3. The alternative route must not exceed 15% additional distance.

### 1.5 Communication Requirement

If the driver deviated from the optimal route by more than 10% **and**
did not communicate the deviation to the rider via in-app chat or
in-app call, the refund tier is automatically upgraded by one level
(e.g., "minor deviation" becomes "significant deviation" for refund
purposes).

### 1.6 Driver Defense

A driver may defend against a route deviation claim by providing
evidence of:

- Road closures or accidents on the optimal route (verified by
  Ryde's traffic system).
- Rider-requested route changes (documented in chat logs).
- Emergency situations (medical, safety) — requires police or
  hospital report.

### 1.7 Recurring Deviation Pattern

If a driver has 3 or more route deviation complaints with confirmed
refunds within a 90-day period, the case is escalated to the Driver
Quality team for review, and the dispute is flagged for possible
account suspension.

---

## 2. No-Show Charge Disputes

### 2.1 Definition

A no-show charge dispute arises when a rider disputes a no-show
cancellation fee charged after the driver reported the rider as
not present at the designated pickup point.

### 2.2 No-Show Fee

The standard no-show fee is **$5.00 SGD**. It is charged to the
rider's payment method when a driver cancels a trip due to rider
no-show.

### 2.3 Driver Wait Time Requirement

A driver **must** wait a minimum of **5 minutes** after arriving at
the pickup location before cancelling the trip as a no-show. The
arrival time is recorded by the driver's GPS when the vehicle is
stationary within 50 meters of the designated pickup coordinates.

### 2.4 Contact Attempt Requirement

Before cancelling as no-show, the driver **must** attempt to contact
the rider through **at least one** of the following:

1. In-app chat message (logged with timestamp).
2. In-app call (call log recorded).

If the driver cancels without any contact attempt, the no-show fee
is automatically voided, and the rider receives a full refund.

### 2.5 Early Departure Rule

If the driver leaves the pickup location (GPS moves > 50 meters from
pickup) **before** the 5-minute minimum wait period has elapsed,
the no-show charge is **voided**, and:

- The rider receives a full refund of the no-show fee.
- The rider may re-book at no additional cost.
- The driver receives a warning; repeated early departures (2+
  within 30 days) result in a $10 deduction from driver earnings.

### 2.6 Rider Presence Verification

To determine whether the rider was present at the pickup point,
the following evidence is considered:

| Evidence source | Weight |
|----------------|--------|
| Rider's GPS location at pickup time (within 50m of pickup) | High |
| Driver's GPS showing stationary at pickup for ≥ 5 min | High |
| Chat logs showing rider communication during wait period | Medium |
| Rider's account ride history and rating | Low (contextual) |
| Driver's completion rate and past no-show dispute history | Low (contextual) |

### 2.7 Genuine No-Show

A no-show charge is upheld if **all** of the following are true:

1. The driver waited at least 5 minutes at the pickup location.
2. The driver attempted at least one form of contact.
3. The rider was not within 50 meters of the pickup point during
   the wait period (verified by rider GPS).
4. The rider did not respond to contact attempts.

### 2.8 Disputed No-Show — Rider Present

The no-show fee is refunded if the rider can demonstrate that:

1. The rider was within 50 meters of the pickup point during the
   wait period (rider GPS verification), **OR**
2. The driver left before the 5-minute minimum (driver GPS
   verification), **OR**
3. The driver made no contact attempt (chat/call log verification).

If the rider was present but the driver also met all requirements
(waited 5 min, attempted contact), the case is reviewed individually
and may result in a partial refund or goodwill credit at the Judge's
discretion.

### 2.9 Recurring No-Show Pattern (Rider)

If a rider has 3 or more confirmed no-shows within a 90-day period,
the no-show fee is upheld regardless of edge-case circumstances,
and the rider account is flagged for review.

---

## 3. General Provisions

### 3.1 Dispute Filing Window

Disputes must be filed within **72 hours** of trip completion. Disputes
filed after the window may be rejected unless exceptional circumstances
are demonstrated.

### 3.2 Confidence Score

The Judge agent must output a confidence score between 0.0 and 1.0
representing the certainty of the ruling based on available evidence.
A score below 0.6 indicates insufficient evidence, and the case should
be flagged for human review.

### 3.3 Remedies

The following remedies may be ordered:

| Remedy | Description |
|--------|-------------|
| **Refund** | Full or partial refund of the disputed amount to the rider |
| **Compensation** | Additional credit issued to the rider beyond the disputed amount (goodwill) |
| **No action** | The charge stands; no refund or compensation is issued |
| **Driver warning** | Formal warning issued to the driver (separate from financial remedy) |
| **Account flag** | Account flagged for quality review (rider or driver) |

### 3.4 Evidence Standards

All evidence must be sourced from the Ryde platform's own data
systems. Third-party evidence (screenshots, external GPS apps) is
not admissible unless verified against platform logs.

### 3.5 Dual Explanation Requirement

The Judge must produce **two** natural-language explanations:

1. **Explanation for rider** — clear, non-technical, explaining the
   decision and any amount credited or charged.
2. **Explanation for driver** — professional, citing policy clauses
   applied and any consequences for the driver.

Both explanations must reference the specific policy sections applied
(e.g., "Section 1.3 — Significant deviation, full refund of fare
difference").
