from flask import Flask, request, jsonify
from pathlib import Path
import gradio as gr
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key='AIzaSyCyBk7JDaoLq32uLgJqmWZsAfpnW_bm2nY')

generation_config = {
  "temperature": 0.4,
  "top_p": 1,
  "top_k": 32,
  "max_output_tokens": 4096,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  }
]

model = genai.GenerativeModel(model_name="gemini-pro-vision",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

def input_image_setup(image_loc):
    try:
        if not (img := Path(image_loc)).exists():
            raise FileNotFoundError(f"Could not find image: {img}")

        with open(img, 'rb') as f:
            image_data = f.read()

        image_parts = [
            {
                "mime_type": "image/jpeg",  # Adjust MIME type if necessary
                "data": image_data
            }
        ]

        return image_parts

    except Exception as e:
        raise e  # Re-raise the exception for handling in generate_gemini_response

def generate_gemini_response(input_prompt, image_loc):
    try:
        image_parts = input_image_setup(image_loc)  # Assuming input_image_setup returns a list of image data dictionaries

        # Combine text prompt and image data
        prompt_parts = [input_prompt] + image_parts

        response = model.generate_content(prompt_parts)
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

    # Extracting additional input
    last_glucometer_reading = request.form.get('expense', 'N/A')

    file_path = 'photo/' + file.filename
    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {e}'}), 500

    input_prompt = f"""
    you have an image containing a list of categories, and you also have a parameter expense containing some input. Your task is to classify the input based on the categories in the image and return the result.
    """
    try:
        response = generate_gemini_response(input_prompt, file_path)
    except Exception as e:
        return jsonify({'error': f'Failed to generate response: {e}'}), 500

    return jsonify({'file_path': file_path, 'response': response}), 200

if __name__ == '__main__':
  app.run(debug=True)
