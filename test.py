import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Set up Gemini API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Please set the GEMINI_API_KEY in the .env file.")

genai.configure(api_key=api_key)

# Function to generate flashcards using Gemini
def generate_flashcards(language, topic, num_cards=10):
    prompt = f"""
    Generate {num_cards} structured language learning flashcards for learning {language} about {topic}.
    Format the response as a valid JSON list:

    [
        {{"front": "Word", "back": "Translation, example sentence, pronunciation"}}
    ]
    """

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        print("Raw Response:", response.text)  # Debugging Line

        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]  # Remove Markdown JSON formatting
        flashcards = json.loads(response_text)
        return flashcards
    except json.JSONDecodeError:
        return "Error: Gemini returned an unexpected format."
    except Exception as e:
        return f"Error: {str(e)}"

# Command-line interaction
if __name__ == "__main__":
    print("Welcome to the LLM Flashcard Generator CLI! Type 'exit' anytime to quit.\n")
    
    while True:
        language = input("Enter the language you're learning: ").strip()
        if language.lower() in ["exit", "quit"]:
            break

        topic = input("Enter the topic (e.g., Food, Travel, Business): ").strip()
        if topic.lower() in ["exit", "quit"]:
            break

        print("\nGenerating flashcards...\n")
        flashcards = generate_flashcards(language, topic)

        if isinstance(flashcards, str):  # Check if an error occurred
            print(flashcards)
        else:
            for idx, card in enumerate(flashcards, 1):
                print(f"Flashcard {idx}:")
                print(f"  Front: {card['front']}")
                print(f"  Back: {card['back']}\n")

        print("=" * 40)
