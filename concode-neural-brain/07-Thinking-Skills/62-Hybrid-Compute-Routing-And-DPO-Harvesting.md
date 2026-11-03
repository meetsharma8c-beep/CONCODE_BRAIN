---
title: Thinking Skill -- Hybrid Compute Routing And DPO Harvesting
type: thinking_skill
tags:
  - skill/compute-routing
  - subsystem/router
  - subsystem/evolution
---

# Thinking Skill: Hybrid Compute Routing And DPO Harvesting

> Scores problem complexity across three neural compute tiers (`TIER_1_REFLEX`, `TIER_2_DEEP_LOCAL`, `TIER_3_FRONTIER`) and harvests verified outputs and self-repair pairs into QLoRA and DPO datasets.

---

## Complexity Scoring Equation

$$
C = \min\left(1.0,\; 0.15 + \min\left(\frac{W}{150}, 0.30\right) + \min\left(\frac{F}{10}, 0.25\right) + \min\left(\frac{B}{25000}, 0.20\right) + \mathbb{I}_{G \ge 2}\cdot 0.15 + \mathbb{I}_{\text{meta}}\cdot 0.10\right)
$$

where $W$ is word count, $F$ is workspace file count, $B$ is total workspace characters, and $G$ is active guild count.

---

## Continual Harvesting Streams

1. **Instruction Trajectories (`data/harvested_trajectories.jsonl`)**: Recorded when $S_{\text{critic}} \ge 0.80$.
2. **DPO Preference Pairs (`data/harvested_dpo_pairs.jsonl`)**: Recorded as `(prompt, chosen=repaired, rejected=broken)` whenever `CodeRepairer` heals syntax defects.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Router Subsystem: [[01-Brain-Architecture/16-Hybrid-Compute-Router|16-Hybrid-Compute-Router]]
- Evolution Subsystem: [[01-Brain-Architecture/17-Evolution-Harvester|17-Evolution-Harvester]]
