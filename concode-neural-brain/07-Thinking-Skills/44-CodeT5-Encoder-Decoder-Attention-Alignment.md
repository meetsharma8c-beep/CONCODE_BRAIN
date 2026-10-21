---
title: Thinking Skill — CodeT5 Encoder-Decoder Attention Alignment
type: thinking_skill
tags:
  - skill/cross-attention
  - codet5/seq2seq
---

# Thinking Skill: CodeT5 Encoder-Decoder Attention Alignment

> Aligns cross-attention activations between broken input code sequences and generated fix target sequences inside CodeT5.

---

## Cross-Attention Equation

$$\text{CrossAttention}(Q_{\text{dec}}, K_{\text{enc}}, V_{\text{enc}}) = \text{Softmax}\left(\frac{Q_{\text{dec}} K_{\text{enc}}^T}{\sqrt{d_k}}\right) V_{\text{enc}}$$

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
