# Economy, XP and Agricultural Measurement Simulations
**2026-11-02 | Draft v0.1 | Synthetic scenario model, NOT observations from Wild Seeds Ranch.**

## Research basis and assumptions
Farm records should preserve source events, not reward raw data quantity. farmOS uses Assets, Logs, Quantities and data streams, with structured observation, harvest, lab test and maintenance logs (https://farmos.org/model/ and https://farmos.org/guide/logs/). For agricultural sensors, field calibration and error are major issues: https://pmc.ncbi.nlm.nih.gov/articles/PMC10007478/ and https://www.extension.arizona.edu/publication/guide-maintaining-and-calibrating-field-installed-soil-and-plant-moisture-sensors.

### Monte Carlo model
2,000 independently sampled hypothetical seasons per scenario, reproducible seed 126; potential production Gaussian(mean 1050 lb, sd 140 lb), baseline loss fraction bounded [0,55%] sampled Gaussian(mean 23%, sd 7.5%). Baseline loss reduced by assumed avoidable-loss prevention fractions 4%, 12%, 23%. Recorded harvest = actual harvest times assumed capture coverage times small measurement noise. These intervention assumptions are exploratory, not efficacy claims. Four crops are referenced conceptually; the numeric model aggregates rather than simulates distinct crop agronomy.
| Scenario | Recorded fraction | Assumed loss prevention | Mean actual harvest (lb) | Mean reported harvest (lb) | Mean loss (lb) | Illustrative device budget |
|---|---:|---:|---:|---:|---:|---:|
| Paper/manual-first | 48% | 4% | 816.1 | 391.8 | 233.8 | $90 |
| Reused phones + AI review | 81% | 12% | 839.2 | 679.5 | 215.8 | $350 |
| Calibrated sensors + familiar | 92% | 23% | 863.3 | 794.1 | 186.0 | $820 |

**Interpretation:** improved recording can make observed harvest rise dramatically with only modest change in actual harvest. DO NOT claim increased farm yield from increased logs. True efficiency analysis needs comparable area, planting, weather, inputs, crops, and preharvest loss baselines. Dollar figures are illustrative per-scenario equipment allowances, not quotes.

### Community economy accounting
**Flows:** seed/input purchase or gift -> planting and labor -> growing -> harvested stock -> kitchen, gifts, preserves, market or compost. Track inputs and outputs separately from XP. Reuse ValueFlows EconomicEvents and ResourceInstances when compatible. Measures: yield per area, harvest completeness, food distribution, wasted stock, input cost, water per bed, hours of equipment uptime, maintenance burden, training throughput and repair avoidance.

Economic benefit ledger distinguishes (a) actual cash saved, (b) estimated value of produce without a market sale, (c) avoided replacement cost of salvaged equipment, (d) actual material expenses, (e) equipment repair/replacement, (f) volunteer time (documented only voluntarily and never equated to zero cost), (g) educational value (nonmonetized unless justified), (h) ecological indicators (not monetized by default). Avoid double counting produce value and sale proceeds.

### XP models (synthetic)
20 hypothetical participants over 12 weeks, variable action participation each week with representative activities: observation, demonstration, collaboration, mentorship, maintenance and documentation. One seeded random draw per model, not matched participant populations, so comparisons illustrate behavior only.
| Rule | Mean XP | Range | Spread (SD) | Major drawback |
|---|---:|---:|---:|---|
| Activity count proxy (12 XP/event) | 921 | 732-1080 | 91 | Encourages repeated low-value logging |
| Flat per-activity rewards | 1255 | 1080-1515 | 104 | Incentive to spam easy events |
| Evidence-capped (max 2 observation rewards per week) | 1186 | 900-1415 | 122 | Still needs fair outcomes validation |

The synthetic score is **not** a measure of human worth or skill. Proposed production design uses distinct capabilities and records:
- Learning: demonstrated milestones, mentor endorsements, reproducible builds.
- Contribution: verified beneficial outcomes without individual productivity rankings.
- Collaboration: successful parties and teaching, private/noncompetitive.
- Stewardship: community progress measured from real baselines.
- XP: optional bounded celebration awarded on diverse achievements, not cash and not governance rights.

### Proposed sample XP schedule (tunable for playtests)
- First verified farm observation in a new method: 10 discovery XP.
- Accurate calibration with documented comparison: 35 practice XP.
- Successful instrument build plus maintenance instructions: 50 creation XP.
- Demonstrated interpretive skill with uncertainty: 30 research XP.
- Co-taught learning session with feedback: 40 mentorship XP.
- Community-verified tangible restoration milestone: 50 team XP to each consenting member (not split by hours).
- First independent replication at a second site: 75 federation XP for both teams.
No repeat XP for the same device event, duplicate photo, daily login or arbitrary chore count. One-to-many party awards have safeguards against fabricated participants. Skill endorsements require assessment beyond XP.

### Safeguards and experiments
A/B tests should evaluate voluntary participation, data quality, skill retention, member reported sense of agency and enjoyment, not screen time. Measure how rewarding calibration/teaching instead of logging volume changes error rate. Run more realistic site-calibrated simulations after a baseline growing season.
