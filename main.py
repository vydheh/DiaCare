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
    last_glucometer_reading = request.form.get('lastglucometerreading', 'N/A')

    file_path = 'photo/' + file.filename
    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {e}'}), 500

    input_prompt = f"""
    As an expert specializing in assessing the suitability of fruits and foods for individuals with diabetes, your task involves analyzing input images featuring various food items. Your first objective is to identify the type of fruit or food present in the image. Subsequently, you must determine the glycemic index of the identified item. Based on this glycemic index and the individual's last glucometer reading of 150mg/dl premeal provide recommendations on whether individuals with diabetes can include the detected food in their diet. If the food is deemed suitable, specify the recommended quantity for consumption.
Your answer should be in the given format :- 
Scanned food item is (Food name)
(Food name) has glycemic index of (Glycemic Index)
(Give a 1-2 line explanation on whether he should have this food item or not based on previous readings, also mention the last reading) 
Stick strictly to these 3 points no other content other than these three points.
Also if an Image is not of a food then just say Please enter an image of food
    """
    try:
        response = generate_gemini_response(input_prompt, file_path)
    except Exception as e:
        return jsonify({'error': f'Failed to generate response: {e}'}), 500

    return jsonify({'file_path': file_path, 'response': response}), 200

if __name__ == '__main__':
    app.run(debug=True)
