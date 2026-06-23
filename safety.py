from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    TODO — Milestone 1:

    Before writing any code, complete specs/classifier-spec.md. The blank fields
    there are the decisions that drive this implementation — prompt design, tier
    definitions, output format, and edge case handling.

    Your implementation should:
      1. Build a prompt using your tier definitions that asks the LLM to classify
         the question and explain its reasoning
      2. Send a single chat completion request (no tools, no history)
      3. Parse the tier and reason out of the raw response text
      4. Validate the tier against VALID_TIERS; fall back to "caution" if the
         response can't be parsed or the tier isn't recognized
      5. Return {"tier": ..., "reason": ...}

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned

    The three tiers:
      - "safe"    : routine, low-risk repairs most homeowners can handle safely
      - "caution" : doable with care, but mistakes have real cost or mild risk
      - "refuse"  : high-risk repairs that require a licensed professional —
                    mistakes can cause fire, flooding, injury, or structural damage
    """
    system_message = """You are a home repair safety classifier. Given a home repair question, classify it into one of three tiers: "safe", "caution", or "refuse".

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

Reason step-by-step before naming the tier. Then return ONLY a JSON object with exactly two keys: "tier" and "reason". The "reason" value must be one sentence. No other text."""

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Classify this home repair question: {question}"},
        ],
    )

    import json
    import re

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()

    try:
        result = json.loads(raw)
        tier = result.get("tier", "").lower().strip().strip("\"'")
        reason = result.get("reason", "")
        if tier not in VALID_TIERS:
            raise ValueError(f"Unrecognized tier: {tier}")
        return {"tier": tier, "reason": reason}
    except Exception:
        return {"tier": "caution", "reason": "Classification failed — treating as caution out of caution."}
