#!/usr/bin/env python3
"""Synthetic education/economy scenario toy model, not empirical field predictions.
Usage: python docs/living-world/simulate.py
Standard library only. Deterministic seed 126.
"""
import random
import statistics

RNG = random.Random(126)
N = 2000
SCENARIOS = {
    "manual": (0.48, 0.65, 0.04, 90),
    "phone_ai": (0.81, 0.81, 0.12, 350),
    "sensor_familiar": (0.92, 0.88, 0.23, 820),
}

def clamp(value, low, high):
    return min(max(value, low), high)

def farm():
    for label, (coverage, correctness, prevention, equipment_budget) in SCENARIOS.items():
        actual, recorded, loss = [], [], []
        for _ in range(N):
            potential = max(0, RNG.gauss(1050, 140))
            baseline_loss = clamp(RNG.gauss(.23, .075), 0, .55)
            output = potential * (1 - baseline_loss * (1 - prevention))
            actual.append(output)
            loss.append(potential - output)
            recorded.append(output * coverage * RNG.gauss(1, (1 - correctness) * .09))
        print(label, {
            "actual_lb": round(statistics.mean(actual), 1),
            "recorded_lb": round(statistics.mean(recorded), 1),
            "lost_lb": round(statistics.mean(loss), 1),
            "hypothetical_equipment_usd": equipment_budget,
        })

ACTIONS = {
    "observation": (5, 5),
    "demonstration": (30, 2),
    "collaboration": (20, 2),
    "mentorship": (30, 1),
    "maintenance": (15, 2),
    "documentation": (20, 1),
}

def experience():
    for model in ("hours_proxy", "flat_actions", "evidence_capped"):
        scores = []
        for person in range(20):
            score = 0
            for week in range(12):
                for action, (points, maximum) in ACTIONS.items():
                    n = RNG.randint(0, maximum)
                    if model == "hours_proxy":
                        score += n * 12
                    elif model == "flat_actions":
                        score += points * n
                    else:
                        score += points * (min(n, 2) if action == "observation" else n)
            scores.append(score)
        print(model, {"mean": round(statistics.mean(scores)), "min": min(scores),
                      "max": max(scores), "sd": round(statistics.pstdev(scores))})

if __name__ == "__main__":
    farm()
    experience()
