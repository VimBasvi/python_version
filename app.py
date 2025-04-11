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
from datetime import datetime, timedelta

# Strength = box number

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
            'strength': 0, # leitner box level starts at 1 
            'box_level': 1,
            'last_practiced': None,
            'times_reviewed': 0,
            'first_seen': firestore.SERVER_TIMESTAMP 
        })

    return redirect(url_for('practice', language=language, topic=topic))


@app.route('/practice/<language>/<topic>')
def practice(language, topic):
    user_id = 'demo_user'  # In real app, get this from session or auth
    cards_ref = db.collection('users').document(user_id).collection('practice_cards')
    
    # get only cards that match the language and topic
    docs = cards_ref.where('language', '==', language).where('topic', '==', topic).stream()

    flashcards = []
    for doc in docs:
        data = doc.to_dict()
        last_practiced = data.get('last_practiced')
        box_level = data.get('box_level', 1)

        # Convert Firestore timestamp to datetime
        if last_practiced is not None:
            last_practiced = last_practiced.replace(tzinfo=None)
        # Check if the card is due for review from leitner box system
        if is_card_due(last_practiced, box_level):
            flashcards.append({
                'front': data.get('front', ''),
                'back': data.get('back', ''),
                'language': data.get('language', ''),
                'topic': data.get('topic', ''),
                'doc_id': doc.id
        })

    return render_template('practice.html', flashcards=flashcards, language=language, topic=topic)

@app.route('/update-progress', methods=['POST'])
def update_progress():
    data = request.get_json()
    user_id = 'demo_user'
    doc_id = data['doc_id']

    doc_ref = db.collection('users').document(user_id).collection('practice_cards').document(doc_id)
    doc = doc_ref.get()
    
    doc_data = doc.to_dict()
    times_reviewed = doc_data.get('times_reviewed', 0) + 1
    
    current_box = doc_data.get('box_level', 1)

    if not doc.exists:
        return jsonify({"error": "Card not found"}), 404

    updates = {
        'status': data['status'],
        'last_practiced': firestore.SERVER_TIMESTAMP,
        'times_reviewed': times_reviewed
    }

    current_strength = doc.to_dict().get('strength', 0)

    if data['status'] == 'mastered':
        updates['strength'] = current_strength + 1
        updates['box_level'] = min(current_box + 1, 5)
    elif data['status'] == 'review':
        updates['strength'] = max(current_strength - 1, 0)  # don't go below 0
        updates['box_level'] = 1  # RESET to Box 1 in Leitner system
        
    doc_ref.update(updates)
    return jsonify({"message": "Progress updated"}), 200


@app.route('/my-flashcards')
def my_flashcards():
    user_id = 'demo_user' # In real app, get this from session or auth
    cards_ref = db.collection('users').document(user_id).collection('practice_cards')
    docs = cards_ref.stream()

    sets = set()
    for doc in docs:
        data = doc.to_dict()
        sets.add((data['language'], data['topic']))

    flashcard_sets = [{'language': lang, 'topic': topic} for lang, topic in sets]
    return render_template('my_flashcards.html', flashcard_sets=flashcard_sets)

def is_card_due(last_practiced, box_level):
    if not last_practiced:
        return True  # never practiced before = due

    delay_map = { # need to mod map appropriately for the number of boxes
        1: 1,
        2: 2,
        3: 4,
        4: 7,
        5: 15
    }
    delay_days = delay_map.get(box_level, 1)
    next_due_date = last_practiced + timedelta(days=delay_days)
    return datetime.utcnow() >= next_due_date


    
# Run the Flask App
if __name__ == "__main__":
    app.run(debug=True)
