from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import os
import dotenv
from langchain_huggingface import HuggingFaceEmbeddings
import lancedb
from typing import Dict, TypedDict
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import  Field
from langchain_community.vectorstores import LanceDB
import vertexai
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient

from vertexai.generative_models import GenerativeModel

dotenv.load_dotenv()

class GraphState(TypedDict):
    keys: Dict[str, any]




embeddings_model  = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="cred.json"
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_KEY")
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

#suppress warnings
vertexai.init(project="vision-forge-414908", location="us-central1")


llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-001",
    system_instruction=''' 
    You are an insurance claim resolution agent. You will recieve user information, a compacted JSON of a rejected claim, and some relevant context as to how that claim should be filed, or the best practices to file that claim.
                             Using this information, you need to generate an output consisting of:
                             1) Why the claim was rejected. What portions were incomplete/missing/insufficient etc.
                             2) What they should have done instead, and why this is important.
                             3) How the claim can now be resolved? Should they file a new claim, should they contact the agency, etc.
                             
                             Be very elaborate, complete, and utterly professional. 
                             
                             Your output should be in a small HTML script. The only tags you are allowed to use are: <h2>, <p>, <ul>, <li>
                             
'''
)


user_profile = {
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
    "health_insurance_details": {
      "policy_number": "HSI123456789",
      "policy_provider": "SBI Health Insurance",
      "policy_path": "docs/united india health insurance.pdf",
      "policy_start_date": "2020-01-01",
      "policy_end_date": "2025-01-01",
      "coverage_amount": 500000,
      "premium_amount": 12000,
      "premium_frequency": "Yearly"
    },
    "vehicle_insurance_details": {
      "policy_number": "SBI5682100173",
      "policy_provider": "SBI Private Car Insurance",
      "policy_path": "docs/car insurance.pdf",
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
    "diagnosisDescription": "Dengue fever [classical dengue]",
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


def prepare_docs(request_type):
    if request_type=="health":
      paths = [user_profile["patient_profile"]["health_insurance_details"]["policy_path"]]
    else:
      paths = [user_profile["patient_profile"]["vehicle_insurance_details"]["policy_path"]]
    docs = [PyPDFLoader(url).load() for url in paths]
    docs_list = [item for sublist in docs for item in sublist]
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=3000, chunk_overlap=200
)
    doc_splits = text_splitter.split_documents(docs_list)
    return doc_splits


def lanceDBConnection(request_type, embed=embeddings_model):
    db = lancedb.connect("/tmp/lancedb")
    table = db.create_table(
        "crag_demo",
        data=[{"vector": embed.embed_query("Hello World"), "text": "Hello World"}],
        mode="overwrite",
    )
    
    vectorstore = LanceDB.from_documents(
        documents=prepare_docs(request_type),
        embedding=embeddings_model,
        connection=db,
    )
    retriever = vectorstore.as_retriever()

    return retriever

#retriever = lanceDBConnection(embeddings_model)

def generate_resolution(state_dict):#node 2
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with relevant documents
    """

    question = "claim filing, filing procedure, deadlines, expenses, eligible, included, denial, reimbursement, authorization, coverage"
    type=state_dict["type"]
    claim_json = state_dict["claim_json"]
    
    retriever = lanceDBConnection(state_dict["type"])
    op = retriever.invoke(question)
    documents = [o.page_content for o in op]

    # LLM

    # Prompt
    prompt = PromptTemplate(
        template="""
               
        You need to analyze the content of this claim:
        {claim_json}
        
        Relevant context pulled from the policy guidebook:
        {documents}
        Answer in the 2nd person. Answer with "you" and "your"
        Remember to generate your output in a short HTML script, The only tags you are allowed to use are: <h2>, <p>, <ul>, <li>.
        """,
        input_variables=["claim_json", "documents"],
    )

    # Chain
    chain = prompt | llm
    response = chain.invoke({"claim_json": claim_json, "documents": documents })

    # Score
    
 
    return {
        "response": response.content
            
    }


