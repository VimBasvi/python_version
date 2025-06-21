# FlashLearn

FlashLearn is a flashcard learning platform designed to help users master material using spaced repetition algorithms. Built as a final thesis project, it combines a Flask backend with Firebase for data storage and authentication.

## Features

- User authentication and data persistence using Firebase.
- Support for user-generated decks and flashcards.
- Spaced repetition scheduling using SM-2 and Leitner algorithms.
- Interactive practice interface with recall rating and progress tracking.
- Built with Flask, Firebase, JavaScript, and custom CSS.

## Technologies Used

- **Backend:** Flask (Python)
- **Database & Auth:** Firebase
- **Frontend:** JavaScript, CSS
- **Algorithms:** SM-2, Leitner System

## Getting Started

To run the project locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/VimBasvi/FlashLearn.git

2. Navigate to the project directory:
  ```bash 
  cd FlashLearn

3. Set up a virtual environment and install dependencies:

  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt

4. Configure your Firebase credentials in config.py or as environment variables.

5. Run the Flask app:

```bash
python ....py

## License
This project is open-source and available under the MIT License

