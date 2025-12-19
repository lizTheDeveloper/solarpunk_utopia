# Proposal: Algorithmic Transparency

**Status:** DRAFT  
**Philosopher:** Joy Buolamwini (Algorithmic Justice)

## Problem
AI agents match offers to needs. But users don't know WHY they got matched. Is it fair? Is it biased? Black box matching erodes trust.

## Solution
Every AI match includes an **explanation**:
- "Matched because: proximity (2 miles), skill match (woodworking), trust score (7.2/10)"
- "Not matched because: too far (15 miles), no mutual availability"
- Users can see the weights: distance 30%, skill 40%, trust 20%, availability 10%

## Key Features
- Explainable AI - every match includes reasoning
- Adjustable weights - communities can tune matching priorities
- Bias detection - flag matches that seem systematically unfair
- Audit trail - researchers can analyze matching patterns

## Success Metric
>80% of users understand why they were or weren't matched.
