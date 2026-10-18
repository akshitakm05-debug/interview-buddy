"""LLM helper for Interview Buddy (Gemini REST API). Falls back to Demo Mode if no key or on any error."""
import os, json, re
import requests

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def _call(prompt):
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.3}}
    r = requests.post(URL, headers={"x-goog-api-key": API_KEY}, json=body, timeout=30)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _json(prompt):
    """Ask for JSON, strip markdown fences, retry once if parsing fails."""
    for _ in range(2):
        text = re.sub(r"```json|```", "", _call(prompt)).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    raise ValueError("Model did not return valid JSON")


def generate_questions(role, count=3, difficulty="Fresher / Entry-Level"):
    try:
        if not API_KEY:
            raise RuntimeError("demo mode")
        data = _json(f"Write {count} interview questions for a {difficulty} candidate applying as {role}. "
                     f"Mix HR and basic role-specific questions. Keep each short and clear. "
                     f"Reply ONLY with a JSON array of strings.")
        qs = [str(q) for q in data][:count]
        if qs:
            return qs
    except Exception as e:
        print("generate_questions fallback:", e)
    pool = ["Tell me about yourself.", f"Why do you want to work as a {role}?",
            "Describe a project or task you are proud of.", "What are your strengths and weaknesses?",
            "How do you handle a tough deadline or problem?", f"What basic skills does a {role} need?",
            "How do you learn something new quickly?", "Tell me about a time you worked in a team.",
            "Where do you see yourself in 3 years?", "Do you have any questions for us?"]
    return pool[:count]


def evaluate_answer(role, question, answer, language="English"):
    try:
        if not API_KEY:
            raise RuntimeError("demo mode")
        res = _json(f"""You are an experienced interviewer evaluating a fresher for the role of {role}.
Question: {question}
Answer: {answer[:1500]}
Be fair and kind. Write good, missing and tip in {language}. Reply ONLY with JSON, keys in English:
{{"score": <integer 0-10>, "good": "...", "missing": "...", "better_answer": "...", "tip": "..."}}""")
        res["score"] = max(0, min(10, int(res.get("score", 5))))
        return res
    except Exception as e:
        print("evaluate_answer fallback:", e)
        n = len(answer.split())
        return {"score": min(9, 3 + n // 12), "good": "You made a clear attempt.",
                "missing": "Add a concrete example and more detail.",
                "better_answer": "(Demo Mode) Add an API key to see an AI-written sample answer.",
                "tip": "Structure it: definition, example, why it matters."}
