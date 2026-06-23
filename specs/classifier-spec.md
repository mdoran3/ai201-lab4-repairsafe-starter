# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
Low-risk, routine repairs that most homeowners can handle with basic tools and patience — no permit or license required, and the worst-case outcome if something goes wrong is cosmetic damage or a broken fixture, not injury, fire, or flooding.
```

**caution:**
```
Repairs a motivated homeowner can tackle, but involving water or electrical systems where mistakes carry real cost or mild injury risk — no permit typically required, but errors have meaningful consequences.
```

**refuse:**
```
Do not provide DIY instructions for repairs that require a licensed professional and permit, or where an amateur mistake could cause fire, flooding, structural damage, serious injury, or death.
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
The LLM receives all three tier definitions plus few-shot examples for each tier (3–4 per tier, covering clear cases and boundary cases). It is asked to reason step-by-step before naming the tier, applying one explicit test for ambiguous cases: if this goes wrong, can it cause fire, flooding, structural failure, injury, or death? If yes → refuse; if the work involves water or electrical systems but failure is recoverable → caution. When the question sits at a boundary, the classifier errs toward the more restrictive tier. Key edge case rules are stated explicitly: "replacing" an existing electrical component at the same location is caution; "adding" a new circuit or outlet is refuse. Any gas work is always refuse. Any wall removal is refuse unless a structural engineer has already confirmed it is non-load-bearing.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
The LLM returns a JSON object with exactly two keys: "tier" (one of "safe", "caution", or "refuse") and "reason" (one sentence explaining the classification). The response is parsed with json.loads(). If parsing fails or the tier value is not in VALID_TIERS, the function falls back to a default error response.
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
You are a home repair safety classifier. Given a home repair question, classify it into one of three tiers: "safe", "caution", or "refuse".

Tier definitions:
- safe: Low-risk, routine repairs that most homeowners can handle with basic tools and patience — no permit or license required, and the worst-case outcome if something goes wrong is cosmetic damage or a broken fixture, not injury, fire, or flooding.
- caution: Repairs a motivated homeowner can tackle, but involving water or electrical systems where mistakes carry real cost or mild injury risk — no permit typically required, but errors have meaningful consequences.
- refuse: Do not provide DIY instructions for repairs that require a licensed professional and permit, or where an amateur mistake could cause fire, flooding, structural damage, serious injury, or death.

Examples:
"How do I patch a small hole in drywall?" → {"tier": "safe", "reason": "Patching small drywall holes is routine cosmetic work requiring only basic tools with no risk of injury or system damage."}
"How do I replace weather stripping on my front door?" → {"tier": "safe", "reason": "Replacing weather stripping is low-risk maintenance with no permit required and no risk of injury or system damage."}
"How do I replace a bathroom faucet?" → {"tier": "caution", "reason": "Replacing a faucet involves the water supply system — a mistake can cause leaks or water damage, though no permit is typically required."}
"How do I replace a GFCI outlet?" → {"tier": "caution", "reason": "Swapping a GFCI outlet at the same location involves electrical work where incorrect wiring could cause a shock, but no permit is typically required."}
"How do I add a new outlet to my garage?" → {"tier": "refuse", "reason": "Adding a new outlet requires running a new circuit from the breaker panel, which is permit-required work where amateur mistakes create fire hazards."}
"How do I replace my water heater?" → {"tier": "refuse", "reason": "Water heater replacement requires a permit in most jurisdictions and improper installation can cause an explosion."}

Key rules for boundary cases:
- If a mistake could cause fire, flooding, structural failure, injury, or death → refuse.
- "Replacing" an existing electrical component at the same location → caution. "Adding" a new circuit or outlet → refuse.
- Any gas work → always refuse.
- Any wall removal → refuse unless a structural engineer has already confirmed it is non-load-bearing.
- When in doubt, err toward the more restrictive tier.

Reason step-by-step before naming the tier. Then return ONLY a JSON object with exactly two keys: "tier" and "reason". The "reason" value must be one sentence. No other text.
```

**User message:**
```
Classify this home repair question: {question}
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
Classify as refuse if an amateur mistake could cause fire, flooding, structural failure, serious injury, or death, or if the work legally requires a permit and licensed professional — otherwise classify as caution.

"How do I replace the outlet in my bathroom that stopped working?" → caution. Swapping an existing outlet at the same location involves electrical work with shock risk, but it's on an existing circuit with no new wiring — if wired incorrectly, a breaker trips. Recoverable.

"How do I add an outlet to my bathroom?" → refuse. Adding a new outlet requires running a new circuit from the panel, obtaining a permit, and creating a permanent fire hazard if done incorrectly. The word "add" is the signal.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
If the LLM response cannot be parsed as JSON or the tier value is not in VALID_TIERS, the function returns {"tier": "caution", "reason": "Classification failed — treating as caution out of caution."}. Failing closed to "caution" is the right choice here: failing open to "safe" risks giving DIY instructions for a repair that should have been refused or warned, while failing to "caution" ensures the user at least receives a warning rather than false confidence.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
"How do I patch a large hole in drywall (over 6 inches)?" — expected caution (it was listed in our caution examples), but the LLM returned safe. The reasoning was that it's still cosmetic work with no system risk, just more material and effort. In hindsight the tier is debatable, but it shows the model focuses on injury/system risk rather than repair complexity when assigning caution.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
After seeing the warning that LLMs might return tier values with capital letters, surrounding quotes, or markdown code fences, we added normalization to the parser: .lower(), .strip("\"'"), and a regex to strip code fences before json.loads(). Without this, a response like {"tier": "Safe"} would fail validation and fall back to caution even when the classification was correct.
```
