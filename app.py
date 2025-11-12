# app.py
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from models import init_db, SessionLocal, User, Note
from datetime import datetime
import sqlite3
import os

# Optional LLM integration helper
from llm_integration import query_llm_or_rules

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-key")

# Init DB (create tables if not exist)
init_db()

# Utility: get DB session
def get_db():
    return SessionLocal()

# ROUTES
@app.route("/")
def index():
    return render_template("index.html")

# Register
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    db = get_db()
    from sqlalchemy.exc import IntegrityError
    user = User(username=username, password=password)
    db.add(user)
    try:
        db.commit()
        return jsonify({"status":"ok", "user_id": user.user_id})
    except IntegrityError:
        db.rollback()
        return jsonify({"status":"error", "message":"username already exists"}), 400
    finally:
        db.close()

# Login
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    db = get_db()
    user = db.query(User).filter_by(username=username, password=password).first()
    if user:
        user.last_login = datetime.utcnow()
        db.commit()
        session['user_id'] = user.user_id
        db.close()
        return jsonify({"status":"ok", "user_id": user.user_id})
    db.close()
    return jsonify({"status":"error", "message":"invalid credentials"}), 401

# Logout
@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop('user_id', None)
    return jsonify({"status":"ok"})

# Create note
@app.route("/api/notes", methods=["POST"])
def create_note():
    if 'user_id' not in session: return jsonify({"status":"error","message":"not logged in"}),401
    user_id = session['user_id']
    data = request.json
    topic = data.get("topic")
    message = data.get("message")
    db = get_db()
    note = Note(user_id=user_id, topic=topic, message=message, last_update=datetime.utcnow())
    db.add(note)
    db.commit()
    nid = note.note_id
    db.close()
    return jsonify({"status":"ok", "note_id": nid})

# Read notes for logged-in user
@app.route("/api/notes", methods=["GET"])
def read_notes():
    if 'user_id' not in session: return jsonify({"status":"error","message":"not logged in"}),401
    user_id = session['user_id']
    db = get_db()
    notes = db.query(Note).filter_by(user_id=user_id).all()
    out = [{"note_id": n.note_id, "topic": n.topic, "message": n.message, "last_update": n.last_update.isoformat()} for n in notes]
    db.close()
    return jsonify({"status":"ok", "notes": out})

# Update note
@app.route("/api/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    if 'user_id' not in session: return jsonify({"status":"error","message":"not logged in"}),401
    user_id = session['user_id']
    data = request.json
    db = get_db()
    note = db.query(Note).filter_by(note_id=note_id, user_id=user_id).first()
    if not note:
        db.close()
        return jsonify({"status":"error","message":"note not found"}),404
    note.topic = data.get("topic", note.topic)
    note.message = data.get("message", note.message)
    note.last_update = datetime.utcnow()
    db.commit()
    db.close()
    return jsonify({"status":"ok"})

# Delete note
@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    if 'user_id' not in session: return jsonify({"status":"error","message":"not logged in"}),401
    user_id = session['user_id']
    db = get_db()
    note = db.query(Note).filter_by(note_id=note_id, user_id=user_id).first()
    if not note:
        db.close()
        return jsonify({"status":"error","message":"note not found"}),404
    db.delete(note)
    db.commit()
    db.close()
    return jsonify({"status":"ok"})

# LLM endpoint: receives a natural language command, returns result
@app.route("/api/llm", methods=["POST"])
def llm_endpoint():
    if 'user_id' not in session: return jsonify({"status":"error","message":"not logged in"}),401
    user_id = session['user_id']
    data = request.json
    prompt = data.get("prompt", "")
    # This function will either call an LLM or fallback to simple rules (implemented in llm_integration.py)
    result = query_llm_or_rules(prompt, user_id)
    return jsonify({"status":"ok", "result": result})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
