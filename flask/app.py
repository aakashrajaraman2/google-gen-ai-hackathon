from flask import render_template, redirect, request, url_for, flash, Flask, session, send_from_directory
from dotenv import load_dotenv
import os
import json
from flask import jsonify
import time
from vertexai.generative_models import GenerativeModel, ChatSession, Content, Part
import vertexai
from crag import generate_langgraph
from policy_helper import grade_documents
import policy_helper
import claim_resolution
import comparison
print("Starting")
app = Flask(__name__)
crag_app = generate_langgraph()
app.jinja_env.globals.update(len=len)

print("DONE WITH CRAG APP")
vertexai.init(project="vision-forge-414908", location="us-central1")
model = GenerativeModel(model_name="gemini-1.5-flash-001",
                             system_instruction='''You have to have a conversation with a novice user about their insurance-related experience. 
                             This may be a hospitalization/car accident etc. Ask relevant questions one at a time, ask for necessary clarifications, etc. 
                             Give them as clear and sound advice from the policy context you are given. Format your answer as a very short html script. The only tags you can use are <p>, <ol>, <li>.
                             Once you are done with understanding their experience, the user will send you a list of necessary fields they require to fill out a form.
                             These fields include personal infromation, information about the incident: hospitalization, car accidents, etc. So, ensure to ask information along these lines.
                             You must return a json object with the values for these fields. 
                             Ensure that all your information is accurate, elaborate, and professional. 
                             Until the user asks for the json, don't provide it. Ask as many important questions required to fill out a insurance claim form.''',
                            
     )
docs_path = "german_docs"
summaries_path = "contract_summaries"
load_dotenv()
session={
    "ranjitsharma":{
    "username": "ranjitsharma",#default user
    "chat": None,
    "request": ""
    }
}

#set up the history for the chat session to use.
health_user_profile = {
  "patient_profile": {
    "personal_details": {
      "name": "Ranjit Sharma",
      "date_of_birth": "1985-06-15",
      "gender": "Male",
      "marital_status": "Married",
      "children": 0,
      "spouse_name": "Anita Sharma",
      "contact_details": {
        "phone": "+91-9876543210",
        "email": "ranjit.sharma@example.com",
        "address": {
          "street": "15, MG Road",
          "city": "Bengaluru",
          "state": "Karnataka",
          "postal_code": "560001",
          "country": "India"
        }
      }
    },
    "insurance_details": {
      "policy_number": "HSI123456789",
      "policy_provider": "SBI Health Insurance",
      "policy_path": "docs/united india health insurance.pdf",
      "policy_start_date": "2020-01-01",
      "policy_end_date": "2025-01-01",
      "coverage_amount": 500000,
      "premium_amount": 12000,
      "premium_frequency": "Yearly"
    },
    "medical_history": {
      "pre_existing_conditions": [],
      "allergies": [],
      "current_medications": [],
      "past_treatments": []
    },
    "emergency_contact": {
      "name": "Anita Sharma",
      "relationship": "Spouse",
      "phone": "+91-9876543211"
    },
    "claim_history": [
      {
        "claim_id": "CLAIM98765",
        "claim_date": "2023-04-15",
        "hospital_name": "Apollo Hospital",
        "treatment": "Fracture Treatment",
        "claim_amount": 50000,
        "status": "Approved"
      }
    ]
  }
}

default_chat_history = [
    {
        "role": "user",
        "text": "This is my user profile:\n"+ str(health_user_profile)
    },
    {
        "role": "model",
        "text": "Okay, got it. Please ask your questions related to insurance."
    },
    
]

example_claim = {
  "claimId": "DHC20240509001",
  "patientDetails": {
    "name": "Ranjit Sharma",
    "policyNumber": "HSI123456789",
    "dateOfBirth": "1985-06-15",
    "gender": "Male",
    "maritalStatus": "Married",
    "spouseName": "Anita Sharma",
    "contactNumber": "+91-9876543210",
    "email": "ranjit.sharma@example.com",
    "address": {
      "street": "15, MG Road",
      "city": "Bengaluru",
      "state": "Karnataka",
      "postalCode": "560001",
      "country": "India"
    }
  },
  "claimDetails": {
    "diagnosisCode": "A90",
    "diagnosisDescription": "Dengue fever classical dengue",
    "dateOfDiagnosis": "2024-05-01",
    "hospitalName": "Apollo Hospital, Bengaluru",
    "admissionDate": "2024-05-02",
    "dischargeDate": "2024-05-07",
    "totalBillAmount": 250000.00,
    "claimAmount": 225000.00,
    "claimDate": "2024-05-09"
  },
  "claimStatus": {
    "status": "REJECTED",
    "rejectionDate": "2024-05-15",
    "rejectionReasons": [
      "Pre-existing condition not disclosed",
      "Waiting period for vector-borne diseases not completed"
    ],
    "appealDeadline": "2024-06-14"
  },
  "insuranceCompany": {
    "name": "SBI Health Insurance",
    "contactNumber": "+91-1800-22-1111",
    "email": "customer.care@sbigeneral.in",
    "address": "Corporate Office, Fulcrum Building, 9th Floor, A & B Wing, Sahar Road, Andheri (East), Mumbai - 400099"
  },
  "policyDetails": {
    "policyProvider": "SBI Health Insurance",
    "policyPath": "docs/united india health insurance.pdf",
    "policyStartDate": "2020-01-01",
    "policyEndDate": "2025-01-01",
    "coverageAmount": 500000,
    "premiumAmount": 12000,
    "premiumFrequency": "Yearly"
  }
}



history = []

for message in default_chat_history:
    if message["role"] == "user":
        history.append(
            Content(role="user", parts=[Part.from_text(message["text"])])
        )
    else:
        history.append(
            Content(role="model", parts=[Part.from_text(f'{message["text"]}')])
        )

#default route
@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('service.html')

@app.route('/get_response', methods=['POST', 'GET'])#general response
def get_response():
    
    request_json = request.get_json()
    request_message = request_json['message']
    print(request_message)
    output = 9
    output = dict(crag_app.invoke({"keys": {"question": request_message}}))["keys"]["generation"].content
    
    output_json={
        "message": output
    }
    return jsonify(output_json)

@app.route('/compare', methods=['POST', 'GET'])
def compare():
    
    docs = os.listdir(summaries_path)
    
    output_json={
        "message": ""
    }
    return render_template('comparison_ui.html', documents = docs, filters = comparison.get_keys())
  
@app.route('/compare_docs', methods=['POST', 'GET'])
def compare_docs():
    docs = os.listdir(summaries_path)
    selected_docs = request.form.getlist('documents')
    filters = request.form.getlist("filters")
    docs_names = [i.split(".")[0] for i in selected_docs]
    jsons = comparison.load_jsons([summaries_path+"/"+doc for doc in selected_docs], filters)
    table_values, titles = comparison.get_comparison_table(jsons, filters)
    comparison_report = comparison.get_gemini_comparisons(jsons)
    final_doc_name = "comparisons/"+'+'.join(docs_names)+".txt"
    with open(final_doc_name, 'w', encoding='utf-8') as f:
            f.write(comparison_report)
    return render_template('comparison_ui.html', documents = docs, table_values=table_values, titles = titles, final_doc_name=final_doc_name, filters = comparison.get_keys())

@app.route('/upload_docs', methods=['POST', 'GET'])
def upload_docs():
    uploaded_files = request.files.getlist('new_documents')
    saved_files = []
    for file in uploaded_files:
        if file.filename:  # Ensure file was uploaded
            file_path = os.path.join(docs_path, file.filename)
            file.save(file_path)
            saved_files.append(file_path)
   
    comparison.get_summary_jsons(saved_files)
    docs = os.listdir(summaries_path)

    return render_template('comparison_ui.html', documents = docs,)



@app.route("/download", methods=['POST', 'GET'])
def download():
    file_name = request.form.get("final_doc_name")
    print(file_name.split("/")[-1])
    return send_from_directory("comparisons",file_name.split("/")[-1], as_attachment=True)


@app.route('/health_apply', methods=['POST', 'GET'])
def health_apply():
    output_json = {}
    return render_template('health_apply.html', output_json = output_json)
  
  
@app.route('/vehicle_apply', methods=['POST', 'GET'])
def vehicle_apply():
    output_json = {}
    return render_template('vehicle_apply.html', output_json = output_json)

@app.route("/health_question", methods=['POST', 'GET'])#specific chatbot call
def health_question():
    request_json = request.get_json()
    request_type = request_json["type"]
    if session["ranjitsharma"]["chat"] != None:
        chat = session["ranjitsharma"]["chat"]
    elif request_type!=session["ranjitsharma"]["request"]:#new chat, or new requet
      chat = ChatSession(model=model, history=history)
      session["ranjitsharma"]["chat"]=chat
      session["ranjitsharma"]["request"] = request_type
      retriever = policy_helper.lanceDBConnection(request_type=request_type)
      session["ranjitsharma"]["retriever"]=retriever
    docs=[]
    docs = grade_documents(retriever = session["ranjitsharma"]["retriever"],state_dict={"query":request_json["message"], "type": request_json["type"] })['documents']
    total_context = "\n".join(docs)
    #print(total_context)
    final_prompt = "Relevant Information from database:\n"+total_context+"\n\n"+request_json["message"]
    
  
    output=chat.send_message(final_prompt, stream=False)
    session["ranjitsharma"]["chat"]=chat

    return jsonify({"message":output.candidates[0].content.parts[0].text})

@app.route("/render_claim_resolution", methods=['POST', 'GET'])
def render_claim_resolution():
    return render_template('claim_resolution.html')
  
@app.route("/resolve_claim", methods=['POST', 'GET'])
def resolve_claim():
    request_type= request.get_json()["type"]
    state_dict = {
      "type": request_type,
      "claim_json": example_claim
    }
    resolve_response=claim_resolution.generate_resolution(state_dict)["response"]
    return jsonify({"message":resolve_response})


@app.route("/autofill_health_form", methods=["POST", "GET"])
def autofill_health_form():
  
    print(request.form.to_dict())
    
    if "Submit Claim Form"== request.form.to_dict()["final-submit"]:
      print("HEREEEEE")
      return render_template('health_apply.html', message='Your claim form has been submitted! You can submit a new form.')
    elif "Submit Vehicle Claim Form" == request.form.to_dict()["final-submit"]: 
      return render_template('vehicle_apply.html', message='Your claim form has been submitted! You can submit a new form.')
  
    input_names = request.form.to_dict().keys()
    request_type = request.form["request_type"]
    prompt = '''Generate a simple json with the following information. If you don't know the information have an empty string as the value for the key. Ensure that all the keys are accounted for in the output json. Only return the json, no other text. 
    Refer to the user profile and the contents of the chat thus far to fill the information. Do not change any of the keys of the values I am giving you. they need to be exactly the same.
    required fields:
    '''+ str(input_names)+''' And here is the user profile again: \n'''+ str(health_user_profile)
    #print(prompt)
    output_json = session["ranjitsharma"]["chat"].send_message(prompt, stream=False)
    output_json = output_json.candidates[0].content.parts[0].text
    output_json = output_json[output_json.find("{") : output_json.rfind("}") + 1]
    print(output_json)
    output_json = json.loads(output_json)
    
    session["ranjitsharma"]["chat"] = None 
    if request_type == "vehicle":
        return render_template('vehicle_apply.html', output_json=output_json)
      
    
    return render_template('health_apply.html',output_json=output_json)
  

if __name__ == "__main__":
    app.run(host = "0.0.0.0",port=8080, debug=True, use_reloader=True)