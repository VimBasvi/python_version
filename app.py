import os
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from flashcard_prompts import generate_flashcards  # Import the function from flashcard_prompts.py
from flask import request, redirect, url_for
import json
from urllib.parse import quote


# Initialize Flask app
app = Flask(__name__)

# Load Firebase credentials
cred = credentials.Certificate("firebase_config.json")  # Update with your Firebase config
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        language = request.form['language']
        topic = request.form['topic']
        # of flashcards to generate can be added here if needed, default is 10 in the function
        try:
            flashcards = generate_flashcards(language, topic)
            if isinstance(flashcards, str):
                # Handle the error as a flash message or pass directly to the template
                return render_template('index.html', error=flashcards)
            else:
                return render_template('index.html', flashcards=flashcards)
        except Exception as e:
            return render_template('index.html', error=str(e))
    else:
        # Just render the empty form on a GET request
        return render_template('index.html')

@app.route('/start-practice', methods=['POST'])
def start_practice():
    language = request.form['language']
    topic = request.form['topic']
    flashcards_json = request.form['flashcards']
    flashcards = json.loads(flashcards_json)
    user_id = 'demo_user'
    user_choice = request.form.get('save_option')  # <-- new field from form

    cards_ref = db.collection('users').document(user_id).collection('practice_cards')

    if user_choice == 'overwrite':
        # Clear old cards
        docs = cards_ref.stream()
        for doc in docs:
            doc.reference.delete()

    for idx, card in enumerate(flashcards):
        doc_id = f"{language}_{topic}_{idx}"
        doc_ref = cards_ref.document(doc_id)
        doc_ref.set({
            'front': card['front'],
            'back': card['back'],
            'language': language,
            'topic': topic,
            'status': 'new',
            'strength': 0,
            'last_practiced': None,
            'times_reviewed': 0,
            'first_seen': firestore.SERVER_TIMESTAMP 
        })

    return redirect(url_for('practice'))


@app.route('/practice')
def practice():
    user_id = 'demo_user'  # In real app, get this from session or auth
    cards_ref = db.collection('users').document(user_id).collection('practice_cards')
    docs = cards_ref.stream()

    flashcards = []
    for doc in docs:
        data = doc.to_dict()
        flashcards.append({
            'front': data.get('front', ''),
            'back': data.get('back', ''),
            'language': data.get('language', ''),
            'topic': data.get('topic', ''),
            'doc_id': doc.id 
        })

    return render_template('practice.html', flashcards=flashcards)

@app.route('/update-progress', methods=['POST'])
def update_progress():
    data = request.get_json()
    user_id = 'demo_user'
    doc_id = data['doc_id']

    doc_ref = db.collection('users').document(user_id).collection('practice_cards').document(doc_id)
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({"error": "Card not found"}), 404

    updates = {
        'status': data['status'],
        'last_practiced': firestore.SERVER_TIMESTAMP
    }

    current_strength = doc.to_dict().get('strength', 0)

    if data['status'] == 'mastered':
        updates['strength'] = current_strength + 1
    elif data['status'] == 'review':
        updates['strength'] = max(current_strength - 1, 0)  # don't go below 0

    doc_ref.update(updates)
    return jsonify({"message": "Progress updated"}), 200

    
    
# Run the Flask App
if __name__ == "__main__":
    app.run(debug=True)
