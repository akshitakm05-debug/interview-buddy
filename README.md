# Interview Buddy

AI mock-interview platform for freshers, built for QUANTEX'26. Pick a role (or type your own), answer questions one at a time, and get a score, feedback, a stronger sample answer and a final report. Feedback works in English, Tamil or Hindi, and answers can be spoken.

## Run locally
```
pip install -r requirements.txt
cp .env.example .env      # paste your Gemini API key and a random SECRET_KEY
python app.py
```
Open http://127.0.0.1:5000 in Chrome. With no API key the app runs in Demo Mode using built-in questions.

## Deploy (Render)
Build command `pip install -r requirements.txt`, start command `gunicorn app:app`, and add `GEMINI_API_KEY` and `SECRET_KEY` as environment variables.

## Stack
Flask, HTML/CSS/JavaScript, Gemini API, Web Speech API.

## Team
Add your team name and members here.
