# Research Event Bank

This is a brainstorming bank, not a verified fact database. For any real event, use live web search and primary sources before analysis.

## Promising event categories

1. **Urban transport and environment**
   - Driving restrictions, congestion pricing, low-emission zones, parking reforms.
   - Outcomes: PM2.5, NO2, congestion, public transit use, retail activity.
   - Candidate designs: DID, event study, synthetic control, spatial spillover designs.

2. **Industrial policy and subsidies**
   - Subsidy rollout/withdrawal, tax credits, local procurement policies.
   - Outcomes: sales, entry, innovation, employment, prices.
   - Candidate designs: DID, IV if eligibility rules create exogenous variation, DML for high-dimensional controls.

3. **Education policy**
   - Admissions cutoff, scholarship eligibility, school accountability rules.
   - Outcomes: enrollment, achievement, earnings.
   - Candidate designs: RDD, DID, IV, matching.

4. **Labor and social insurance**
   - Minimum wage, unemployment benefits, paid leave, training programs.
   - Outcomes: employment, wages, hours, firm entry/exit.
   - Candidate designs: DID/event study, synthetic control, DML for individual-level confounding.

5. **Platform governance and digital regulation**
   - Rule changes, fee changes, seller verification, algorithmic policy changes.
   - Outcomes: entry, prices, fraud, user retention, seller revenue.
   - Candidate designs: interrupted time series, DID, synthetic control, causal forests for heterogeneous effects.

6. **Public health and safety**
   - Mask mandates, vaccination eligibility, safety campaigns, hospital capacity policies.
   - Outcomes: cases, mortality, utilization, mobility.
   - Candidate designs: event study, synthetic control, IV, spatial spillover analysis.

7. **Tax and fiscal policy**
   - VAT changes, local tax incentives, transfer programs.
   - Outcomes: consumption, investment, reported income, firm behavior.
   - Candidate designs: DID, RDD around thresholds, bunching, IV.

## Event scoring rubric

Score each candidate 1–5:

- Clear policy date and treatment definition.
- Plausible comparison group or donor pool.
- Multiple pre-periods.
- Outcome data available and consistently measured.
- Low contamination/spillovers.
- Policy relevance and novelty.
- Feasible robustness/falsification tests.
