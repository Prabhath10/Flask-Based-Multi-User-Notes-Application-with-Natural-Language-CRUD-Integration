# llm_integration.py
import re
from models import SessionLocal, Note
from datetime import datetime
import os
# OPTIONAL: import for llama-cpp if you have it installed
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except Exception:
    LLAMA_AVAILABLE = False

# If you have a local Llama model path, set LLAMA_MODEL_PATH env var, e.g. path/to/ggml-model.bin
LLAMA_MODEL_PATH = os.environ.get("LLAMA_MODEL_PATH", "")

def call_local_llama(prompt: str) -> str:
    if not LLAMA_AVAILABLE or not LLAMA_MODEL_PATH:
        return "LLM not configured."
    llm = Llama(model_path=LLAMA_MODEL_PATH)
    out = llm(prompt, max_tokens=256)
    return out["choices"][0]["text"]

def simple_rule_processor(prompt: str, user_id: int):
    """
    Extremely simple NL parser for demo:
    - 'create note about X: Y'
    - 'list notes'
    - 'delete note 3'
    - 'update note 4 set message to Z'
    """
    p = prompt.strip().lower()

    db = SessionLocal()
    if p.startswith("create note about"):
        # format: create note about TOPIC: MESSAGE
        m = re.match(r"create note about (.+?): (.+)", prompt, re.I)
        if m:
            topic = m.group(1).strip()
            message = m.group(2).strip()
            n = Note(user_id=user_id, topic=topic, message=message, last_update=datetime.utcnow())
            db.add(n); db.commit()
            nid = n.note_id
            db.close()
            return f"Created note id={nid}"
        db.close()
        return "Could not parse create command."

    if p.startswith("list notes") or p.startswith("show notes"):
        notes = db.query(Note).filter_by(user_id=user_id).all()
        out = []
        for n in notes:
            out.append(f"[{n.note_id}] {n.topic} - {n.message}")
        db.close()
        return "\n".join(out) if out else "No notes found."

    m = re.match(r"(delete note|remove note) (\d+)", p, re.I)
    if m:
        nid = int(m.group(2))
        note = db.query(Note).filter_by(user_id=user_id, note_id=nid).first()
        if not note:
            db.close()
            return f"Note {nid} not found."
        db.delete(note); db.commit(); db.close()
        return f"Deleted note {nid}."

    m = re.match(r"(update note) (\d+) set (topic|message) to (.+)", prompt, re.I)
    if m:
        nid = int(m.group(2))
        field = m.group(3).lower()
        val = m.group(4).strip()
        note = db.query(Note).filter_by(user_id=user_id, note_id=nid).first()
        if not note:
            db.close()
            return f"Note {nid} not found."
        if field == "topic":
            note.topic = val
        else:
            note.message = val
        note.last_update = datetime.utcnow()
        db.commit(); db.close()
        return f"Updated note {nid}."

    db.close()
    return "Sorry, I could not interpret that command."

def query_llm_or_rules(prompt: str, user_id: int):
    # If Llama is configured, call it to interpret; else fall back to simple rules
    if LLAMA_AVAILABLE and LLAMA_MODEL_PATH:
        # build a system prompt that instructs the model to output JSON actions (create/list/update/delete)
        system = ("You are an assistant that converts natural language commands into simple actions for a personal notes app. "
                  "If the user asks to create, update, list, or delete a note, respond with only the action and values in a short text.")
        full_prompt = system + "\nUser: " + prompt
        try:
            return call_local_llama(full_prompt)
        except Exception as e:
            return f"LLM error: {e}"
    # fallback
    return simple_rule_processor(prompt, user_id)
