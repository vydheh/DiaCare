from flask import Flask, request, jsonify
from pathlib import Path
from google.cloud import generativeai

app = Flask(__name__)

generativeai.configure(api_key='AIzaSyCyBk7JDaoLq32uLgJqmWZsAfpnW_bm2nY')

model = generativeai.GenerativeModel(model_name="gemini-pro-vision")

def input_image_setup(image_loc):
    try:
        if not (img := Path(image_loc)).exists():
            raise FileNotFoundError(f"Could not find image: {img}")

        with open(img, 'rb') as f:
            image_data = f.read()

        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": image_data
            }
        ]

        return image_parts

    except Exception as e:
        raise e

def generate_gemini_response(input_prompt, image_loc):
    try:
        image_parts = input_image_setup(image_loc)

        prompt_parts = [input_prompt] + image_parts

        response = model.generate_text(prompt_parts)
        return response.text

    except Exception as e:
        return jsonify({'error': f'Failed to generate response: {e}'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    expense = request.form.get('expense', 'N/A')

    file_path = 'photo/' + file.filename
    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {e}'}), 500

    input_prompt = f"""
    You have an image containing a list of categories, and you also have a parameter Expense: {expense} input. Your task is to classify the input based on the categories in the image and return the result. 
    """
    try:
        response = generate_gemini_response(input_prompt, file_path)
    except Exception as e:
        return jsonify({'error': f'Failed to generate response: {e}'}), 500

    return jsonify({'file_path': file_path, 'response': response}), 200

if __name__ == '__main__':
    app.run(debug=True)
