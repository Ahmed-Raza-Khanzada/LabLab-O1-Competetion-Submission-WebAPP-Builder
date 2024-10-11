from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import zipfile
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
import base64
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
import shutil


conversation_dict = {}

app = Flask(__name__)
CORS(app, supports_credentials=True)
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = "https://api.aimlapi.com"
MODEL_NAME = "o1-mini"

html = """<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome!</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #14110f; color: #81c14b; font-family: 'Courier New', Courier, monospace; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;">
        <h1 style="font-size: 4em; font-weight: normal; margin: 0; font-family: 'Courier New', Courier, monospace;">Welcome! to WebApp Builder</h1>
    <p style="font-size: 1.5em; font-weight: normal; margin: 0; font-family: 'Courier New', Courier, monospace;">Turn Ideas into Interactive Experiences.</p>
    <p style="font-size: 1.5em; font-weight: normal; margin: 0; font-family: 'Courier New', Courier, monospace;">Create your website using simple prompts and a single website design image upload.</p>

            <div style="position: absolute; bottom: 10px; text-align: center;">

            <p style="font-size: 1.5em; font-weight: normal; margin: 0; font-family: 'Courier New', Courier, monospace;">Try Now</p>
            <div style="font-size: 3em;">&#x2193;</div>
        </div>
    </body>
</html>"""



def save_website(session_id, website_code):
    
    session_path = Path("static") / session_id
    session_path.mkdir(parents=True, exist_ok=True)
    
    filenames = website_code.split("```")[0::2]
    website_code = website_code.split("```")[1::2]
    filenames = filenames[:-1] if len(filenames) != len(website_code) else filenames
    print(filenames, "*************************************")
    for ext, code in zip(filenames, website_code):
        code = code.split("\n", 1)[-1]
        ext = ext.strip().strip("*[]").strip().split("*")[-1]
        print(ext)
        # ext = "index.html" if ext == "html" else "styles.css" if ext == "css" else "script.js"
        with open(session_path / ext, "w", encoding="utf-8") as f:
            f.write(code)

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def generate_website_code(session_id, user_prompt, image_path=None):
    conversation= conversation_dict[session_id]
    flag = True
    if image_path:
        flag = True
        encoded_image = encode_image_to_base64(image_path)
        conversation.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"{user_prompt}"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_image}",
                        "detail": "auto"
                    }
                }
            ]
        })
        MODEL_NAME = "gpt-4o-2024-08-06"
    else:
        conversation.append({"role": "user", "content": user_prompt})
        MODEL_NAME = "o1-mini"

    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

        
    
    payload = {
        "model": MODEL_NAME,
        "messages": conversation,
        # "temperature": 0.3,
        "max_tokens": 4096,
        # "n": 2,
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=180)  # 3 minutes timeout
        if response.status_code in [200, 201]:
            response_data = response.json()
            assistant_reply = response_data['choices'][0]['message']['content']
            # print(assistant_reply,"********************************************")
            save_website(session_id, assistant_reply)
            conversation.pop(1)
            conversation.pop(1)

            assistant_reply = ""

            for i in os.listdir(Path("static") / session_id):
                with open(Path("static") / session_id / i, "r", encoding="utf-8") as f:
                    assistant_reply += i + "\n```" + i.split(".")[-1] + "\n" + f.read() + "\n```\n"
            
            print(assistant_reply)
            conversation.append({"role": "assistant", "content": assistant_reply})
            return None
        else:
            return response.text
    except requests.Timeout:
        return "The request timed out after 3 minutes."
    except Exception as e:
        return str(e)



@app.route('/api/submit', methods=['POST'])
def submit_data():
    text = request.form.get('text')
    if text:
        session = request.form.get('session')
        image = request.files.get('image')
        
       
        if image:
            os.makedirs(os.path.join(os.getcwd(),'uploaded_images', session), exist_ok=True)
            image.save(os.path.join('uploaded_images', session, image.filename))  # Save to 'uploads' folder
            generate_website_code(session, text, os.path.join('uploaded_images', session, image.filename))
        else:
            # os.makedirs(os.path.join(os.getcwd(),'uploaded_images', session), exist_ok=True)
            generate_website_code(session, text)
        
     
        return jsonify({
            'status': 'success',
            'text_received': text,
            'image_received': image.filename if image else None
        })
    else:
        return jsonify({'message': 'No text provided'}), 200

@app.route('/api/session', methods=['POST'])
def register_session():
    data = request.get_json()
    session_id = data.get('sessionId')

    if os.path.exists('./static/send.zip'):
        os.remove('./static/send.zip')


    if session_id:
        conversation_dict[session_id] = [{"role": "user", "content": "You are a helpful assistant that generates static website code based on user prompts. You are only allowed to only write one of each three types of codes (html, css, and js). Write the name of the file with extension just before the start of code block within **. And don't write any leading or trailing instructions. Use URL from internet to show the images."},
                                         {"role": "assistant", "content": "Hello! How can I help you?"}]
        os.makedirs(f"{os.getcwd()}/static/"+session_id, exist_ok=True)
        with open(f'{os.getcwd()}/static/'+session_id+'/index.html', 'w') as f:
            f.write(html)
        return jsonify({'message': 'Session registered successfully', 'sessionId': session_id})
    else:
        return jsonify({'error': 'No session ID provided'}), 400

@app.route('/api/leave', methods=['POST'])
def handle_leave():
    data = request.json
    session_id = data.get('sessionId')
    choice = data.get('choice')

    if not session_id or not choice:
        return jsonify({'error': 'Missing session ID or choice'}), 400
    
    os.system(f'zip -r ./static/send.zip ./static/{session_id}')
    shutil.rmtree("./static/"+session_id)
    shutil.rmtree("./uploaded_images/"+session_id)
    del conversation_dict[session_id]

    return jsonify({'message': f'User chose {choice}'}), 200

@app.route('/static/download', methods=['GET'])
def download_website():
    if os.path.exists('./static/send.zip'):
        return send_from_directory(os.getcwd(),"./static/", "send.zip", as_attachment=True)



@app.route('/api/download/<session_id>', methods=['GET'])
def download_code(session_id):
    session_dir = os.path.join("static", session_id)
    if not os.path.exists(session_dir):
        abort(404, description="No code exists")

    zip_path = os.path.join(os.getcwd(),"static", f"{session_id}.zip")

    
    if not os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(session_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, session_dir)
                    zipf.write(filepath, arcname)

    return send_from_directory(f"{os.getcwd()}/static", f"{session_id}.zip", as_attachment=True)


if __name__ == '__main__':
   
    os.makedirs(os.path.join(os.getcwd(),'uploaded_images'), exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
