# Refactor Item Template

Use this format for every entry in `refactorPlan[]` rendered to the user.

---

## [PRIORITY] <Title>

**What:** <one-line concrete change>

**Why:** Addresses `<finding ID or category>` — <one-line rationale>

**Projected token savings:** `<n>` tokens (**estimated**)

**Risk:** `low | medium | high`
- <specific failure mode if any>

**Preservation contract:**
- <what MUST remain identical>
- <validation/reconciliation/output structure that cannot change>

**Steps:**
1. <concrete step>
2. <concrete step>
3. <concrete step>

**Verification after change:**
- Re-run the analyzer; expect CES delta ≥ `<n>`
- Spot-check that `<preserved element>` is unchanged

---

## Tradeoff flag (if applicable)

`TRADEOFF: <accuracy concern> vs <token savings>`

Use only when an optimization could measurably affect output quality.
Never propose tradeoffs that violate the preservation contract.
