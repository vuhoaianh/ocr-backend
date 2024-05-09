from flask import jsonify, request, Flask
from pymongo import MongoClient
import os


app = Flask(__name__)


@app.route('/upload_text', methods=['POST'])
def up_keys_to_db():
    client = MongoClient('localhost', 27017)
    db = client[os.getenv('DB_KEY')]
    collection = db[os.getenv('COLL_KEY')]
    try:
        # Get the text from the form submission
        text = request.form.get('text')
        temp = {'id': '', 'name': 'Customer config', 'line': text.split(',')}
        # Check if text is provided
        if not text:
            return jsonify({'error': 'Text is required'}), 400

        # Insert text into MongoDB
        text_id = collection.insert_one(temp).inserted_id

        return jsonify({'message': 'Text uploaded successfully', 'text_id': str(text_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)