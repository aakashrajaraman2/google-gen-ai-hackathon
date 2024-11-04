import os
import dotenv

import vertexai
# from vertexai.generative_models import GenerativeModel
from vertexai.generative_models import GenerativeModel, ChatSession, Part
import vertexai.preview.generative_models as generative_models
import uuid
from langchain_community.document_loaders import PyPDFLoader
import os
import dotenv
import json

dotenv.load_dotenv()

contract_keys=["Contract_Title",
    "Parties_Involved",
    "Organization_Name",
    "Insurance_Provider",
    "Board_Members",
    "Contract_Date",
    "Effective_Date",
    "End_Date",
    "Membership_Description",
    "Coverage_Area",
    "Europe_Coverage_Duration",
    "Worldwide_Coverage_Duration",
    "Services_Provided",
    "Roadside_Assistance",
    "Accident_Assistance",
    "Medical_Transport",
    "Vehicle_Recovery",
    "Legal_Support",
    "Service_Exclusions",
    "Covered_Vehicles",
    "Insured_Persons",
    "Primary_Member",
    "Additional_Members",
    "Membership_Costs",
    "Service_Limitations",
    "Max_Payout_Limit",
    "Max_Incidents_Per_Year",
    "Contract_Cancellation",
    "Membership_Renewal",
    "Additional_Insurance",
    "Travel_Insurance",
    "Liability_Insurance",
    "Health_Insurance",
    "Member_Responsibilities",
    "Claims_Procedure",
    "Legal_Disputes",
    "Emergency_Contact_Details"
]
keys_string = ", ".join(contract_keys)
vertexai.init(project="vision-forge-414908", location="us-central1")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=r"infineon_key.json"
model = GenerativeModel(model_name="gemini-1.5-flash-001", system_instruction="You must answer the query given to you in english.")
summaries_path = "contract_summaries"


def get_gemini_summary(question):
    response = model.generate_content(
        [f'''You are a document summarizer who reads the content of documents, 
                        and responds with a json object containing these exact keys: {keys_string}.
                        You must respond only in english. 
                        If that that information isn't available in the text, write 'Not Given' as the value.
                        If there are additional keys that need to be added that represent crucial information from the document, 
                        add it to the json. Ensure that the key starts with the word 'extra.' 
                        Ensure that the values of the keys are detailed and extremely thorough: 
                        enough for a applicant to understand the whole document through. 
                        You need to be as detailed as possible while not including false information. 
                        document: {question}. \n\n\n your output should be json parsable''']
    )
    return response.candidates[0].content.parts[0].text

def load_doc(path):
    content = ""
    loader = PyPDFLoader(path)
    pages = loader.load()
    for i in pages:
        content= content+i.page_content
    return content


def get_summary_jsons(docs):
    print("generating summaries")
    for i in range(0,len(docs)):
        print("Doing", str(docs[i]))
        json_val = get_gemini_summary(load_doc(docs[i]))
        text = json_val
        real_text = text[text.find("{") : text.rfind("}") + 1]

        try:
            final_json = json.loads(real_text)

            with open("contract_summaries/"+docs[i].split("\\")[1]+' data.json', 'w') as f:
                json.dump(final_json, f, indent=4)
        except Exception as e:
            print(e)
            pass
            
def get_gemini_comparisons(jsons):
    print("generating comparisons")
    jsons_text = "" 
    for i in range(len(jsons)):
        jsons_text += str(i)+") "+ str(jsons[i]) + "\n\n"
    response=model.generate_content([
        f"You are a document comparison assistant, and your job is to compare the content of documents and generate a detailed comparison report in paragraph form. You will be given several jsons that are summaries of the insurance policies. You need to generate a highly detailed comparison report that covers all the differences between the  policies. Here are the policies: {jsons_text}. Your output needs to be text parseable, so ensure it is human readable"
    ])
    return response.candidates[0].content.parts[0].text

def load_jsons(paths):
    jsons = []
    for path in paths:
        try:
            with open(path, 'r') as f:
                jsons.append(json.load(f))
        except:
            pass
    return jsons

