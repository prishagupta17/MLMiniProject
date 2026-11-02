"""
Enriches a newly-created Topic using an LLM: an initial universal difficulty
estimate, plus a "commonly confused with..." disambiguation note.

Runs once per topic (on creation). If reference_material is provided, the
LLM is asked to base its answer on that text; otherwise it falls back to
general subject knowledge of the topic name + course/module context.

Requires ANTHROPIC_API_KEY in the environment for real LLM calls. If it's
not set, falls back to a simple heuristic seed so the rest of the app still
works during development/demo without a key.
"""
import os
import json
import re

MODEL = "claude-sonnet-4-6"


def _heuristic_fallback(topic_name: str, sibling_names: list) -> dict:
    """No API key available — rough guess so the pipeline still runs."""
    difficulty = min(0.3 + 0.05 * len(topic_name.split()), 0.9)
    confusable = [n for n in sibling_names if n != topic_name][:2]
    note = (
        f"(auto-fallback, no LLM key set) Compare '{topic_name}' carefully with "
        f"{', '.join(confusable)} if studied in the same module."
        if confusable else ""
    )
    return {
        "difficulty": round(difficulty, 2),
        "confusable_topic_names": confusable,
        "confusable_note": note,
    }


def enrich_topic(topic_name: str, module_name: str, course_name: str,
                  sibling_topic_names: list, reference_material: str = None) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _heuristic_fallback(topic_name, sibling_topic_names)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        material_block = (
            f"\nReference material provided by the instructor:\n{reference_material[:4000]}\n"
            if reference_material else
            "\nNo reference material was provided — use your general knowledge of this subject.\n"
        )
        sibling_block = ", ".join(sibling_topic_names) if sibling_topic_names else "(none listed)"

        prompt = f"""You are helping build a study app. Course: "{course_name}", Module: "{module_name}".
Topic to analyze: "{topic_name}"
Other topics in the same module (possible sources of confusion): {sibling_block}
{material_block}
Return ONLY a JSON object, no other text, with this exact shape:
{{
  "difficulty": <float 0.0-1.0, how hard this topic typically is to retain/remember for a student>,
  "confusable_topic_names": [<subset of the sibling topic list above that students commonly confuse this with, empty list if none>],
  "confusable_note": "<one or two sentences: how to tell them apart / a memory hook to recall the right one; empty string if no confusions>"
}}"""

        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
        data = json.loads(text)
        data["difficulty"] = float(max(0.0, min(1.0, data.get("difficulty", 0.5))))
        return data
    except Exception as e:
        print(f"[topic_enrichment] LLM call failed, using fallback: {e}")
        return _heuristic_fallback(topic_name, sibling_topic_names)
