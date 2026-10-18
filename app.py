"""Interview Buddy - Flask app: AI mock interviews for freshers."""
import os, uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from dotenv import load_dotenv

load_dotenv()
import llm_service  # imported after load_dotenv so it can read the API key

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

# Interview data lives on the server, not in the cookie (cookies are limited to ~4 KB).
STORE = {}


def state():
    sid = session.setdefault("sid", str(uuid.uuid4()))
    return STORE.setdefault(sid, {})


def tier_for(avg):
    if avg >= 8.5:
        return "Interview ready", "badge-success", "Outstanding! Clear concepts and well-structured answers."
    if avg >= 7:
        return "Competitive candidate", "badge-primary", "Strong foundation. Polish examples and trade-offs to stand out."
    if avg >= 5:
        return "Developing", "badge-warning", "Good start. Deepen definitions and add concrete examples."
    return "Needs practice", "badge-danger", "Keep practicing. Review the basics and study the model answers below."


@app.route("/")
def index():
    return redirect(url_for("start"))


@app.route("/start", methods=["GET", "POST"])
def start():
    s = state()
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        custom = data.get("custom_role", "").strip()
        role = custom or data.get("role", "Software Engineer").strip()
        difficulty = data.get("difficulty", "Fresher / Entry-Level")
        language = data.get("language", "English")
        try:
            count = max(1, min(10, int(data.get("count", 3))))
        except (ValueError, TypeError):
            count = 3
        questions = llm_service.generate_questions(role=role, count=count, difficulty=difficulty)
        s.clear()
        s.update(role=role, difficulty=difficulty, language=language, questions=questions, index=0, evaluations=[])
        if request.is_json:
            return jsonify({"status": "success", "redirect_url": url_for("interview")})
        return redirect(url_for("interview"))
    active = bool(s.get("questions") and s.get("index", 0) < len(s["questions"]))
    return render_template("start.html", has_active_session=active)


@app.route("/interview")
def interview():
    s = state()
    qs, i = s.get("questions"), s.get("index", 0)
    if not qs:
        flash("Pick a role to begin your mock interview.", "info")
        return redirect(url_for("start"))
    if i >= len(qs):
        return redirect(url_for("summary"))
    return render_template("interview.html", role=s["role"], language=s.get("language", "English"),
                           question=qs[i], question_number=i + 1, total_questions=len(qs),
                           progress_pct=int(i / len(qs) * 100))


@app.route("/answer", methods=["POST"])
def answer():
    s = state()
    qs, i = s.get("questions"), s.get("index", 0)
    if not qs or i >= len(qs):
        return jsonify({"status": "error", "message": "No active question. Restart the interview.",
                        "redirect_url": url_for("start")}), 400
    data = request.get_json(silent=True) or request.form
    text = data.get("answer", "").strip()
    if not text:
        return jsonify({"status": "error", "message": "Please write or say an answer first."}), 400
    ev = llm_service.evaluate_answer(s["role"], qs[i], text, s.get("language", "English"))
    s["evaluations"].append({"index": i + 1, "question": qs[i], "answer": text, "score": ev.get("score", 5),
                             "good": ev.get("good", "N/A"), "missing": ev.get("missing", "N/A"),
                             "better_answer": ev.get("better_answer", "N/A"), "tip": ev.get("tip", "N/A")})
    s["index"] = i + 1
    last = s["index"] >= len(qs)
    return jsonify({"status": "success", "evaluation": ev, "is_last_question": last,
                    "next_url": url_for("summary") if last else url_for("interview")})


@app.route("/summary")
def summary():
    s = state()
    evs = s.get("evaluations", [])
    if not evs:
        flash("Finish at least one question to see your report.", "warning")
        return redirect(url_for("start"))
    avg = round(sum(e["score"] for e in evs) / len(evs), 1)
    tier, tier_class, verdict = tier_for(avg)
    return render_template("summary.html", role=s["role"], evaluations=evs, avg_score=avg,
                           percentage=int(avg * 10), tier=tier, tier_class=tier_class, verdict=verdict)


@app.route("/reset", methods=["GET", "POST"])
def reset():
    STORE.pop(session.get("sid"), None)
    session.clear()
    flash("Session cleared. Choose a role to start fresh.", "info")
    return redirect(url_for("start"))


if __name__ == "__main__":
    # Local only by default. Set HOST=0.0.0.0 to open it to your Wi-Fi (voice input will not work over plain http).
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 5000)),
            debug=os.getenv("FLASK_DEBUG") == "1")
