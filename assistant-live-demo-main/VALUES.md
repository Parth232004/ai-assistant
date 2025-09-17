# VALUES

This sprint reflects our shared values. Each owner has provided a brief note (≤150 words) on Humility, Gratitude, and Honesty.

---
## Nilesh — Metrics, Logging, Execution Tracking
- Humility: Reliable metrics depend on everyone’s endpoints, not just my middleware. When numbers looked off, I assumed my queries could be wrong and validated before blaming upstream services.
- Gratitude: Thanks to the team for instrumenting their endpoints; your quick fixes made the dashboards meaningful. I appreciate the patience while I refined aggregation logic.
- Honesty: If the error rate spikes, I report it as-is, even when it reflects on my components. Data over ego.

---
## Noopur — Responder Integration
- Humility: I kept the responder simple and hardened around safety checks. When ambiguity arose, I asked for clear contracts instead of guessing.
- Gratitude: Grateful for quick reviews and test data that helped finalize the response flow.
- Honesty: I documented limitations (mocked generation) and flagged areas that need model-backed improvements.

---
## Parth — CoachAgent & Feedback
- Humility: Auto-scoring is a heuristic; I treat it as guidance, not judgment. I tuned it with feedback from others.
- Gratitude: Thank you for surfacing similar context; it improved relevance scoring significantly.
- Honesty: I recorded how the aggregate score is computed and what it can and cannot capture.

---
## Chandresh — EmbedCore & Recall
- Humility: I replaced heavy models with a lightweight vectorizer to hit the deadline, noting trade-offs.
- Gratitude: Thanks to everyone who provided texts to index; it made similarity tests real.
- Honesty: I documented accuracy limitations and the path to swap in SentenceTransformer later.
