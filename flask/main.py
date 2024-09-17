from flask import render_template, redirect, request, url_for, flash, Flask, session
from dotenv import load_dotenv
import os
from flask import jsonify
import time


app = Flask(__name__)



load_dotenv()

#default route
@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('1st_page.html')

@app.route('/get_response', methods=['POST', 'GET'])
def get_response():
    
    request_json = request.get_json()
    request_message = request_json['message']
    print(request_message)
    
    
    output = "Hello, nice to meet you"
    output_json={
        "message" : output
    }
    return jsonify(output_json)


if __name__ == "__main__":
    app.run(host = "0.0.0.0",port=8085, debug=True)