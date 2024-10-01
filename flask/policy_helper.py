from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import os
import dotenv
from langchain_huggingface import HuggingFaceEmbeddings
import lancedb
from typing import Dict, TypedDict
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.pydantic_v1 import  Field
from langchain_community.vectorstores import LanceDB
import vertexai
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient
from langgraph.graph import END, StateGraph
import warnings
from vertexai.generative_models import GenerativeModel, ChatSession, Content, Part
import vertexai.preview.generative_models as generative_models

dotenv.load_dotenv()

class GraphState(TypedDict):
    keys: Dict[str, any]




embeddings_model  = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="cred.json"
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_KEY")
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

#suppress warnings
vertexai.init(project="vision-forge-414908", location="us-central1")
model = GenerativeModel(model_name="gemini-1.5-flash-001",
                             system_instruction="You have to have a conversation with the user about their insurance-related experience. This may be a hospitalization/car accident etc. Ask relevant questions, ask for necessary clarifications, etc. Once you are done with understanding their experience, the user will send you a list of necessary fields they require to fill out a form. You must return a json object with the values for these fields. Ensure that all your information is accurate, elaborate, and professional. This json object will be your final output.",
                            
     )

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-001",
system_instruction="You will be given various tasks in the following prompts. Remember that you must be as elaborate and professional as possible. Understand the task carefully, then respond"
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
      "policy_path": "../docs/united india health insurance.pdf",
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

def grade_documents(retriever, state_dict):#node 2
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with relevant documents
    """

    question = state_dict["query"]
    type=state_dict["type"]
    op = retriever.invoke(question)
    documents = op

    # LLM

    # Prompt
    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a policy document to a user question. \n
        Here is the retrieved document: \n\n {context} \n\n
        Here is the user question: {question} \n
        If the document relates to the user question, grade it as relevant. \n
        Ensure that the user's question's specific policy question matches the policy type (auto, pet, life, etc) in the documents.
        Only give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.
        Only answer with the words 'yes' or 'no'. Do not provide any other text. \n\n
        """,
        input_variables=["context", "question"],
    )

    # Chain
    chain = prompt | llm 

    # Score
    filtered_docs = []
    for d in documents:
        score = chain.invoke({"question": question, "context": d.page_content})
        score = [score.content.replace("\n", "")]
        print("THIS IS THE SCORE:", score)
        grade2 = score[0]
        if "yes" in grade2 or "Yes" in grade2:
            print("*" * 5, " RATED DOCUMENT: RELEVANT", "*" * 5)
            filtered_docs.append(d.page_content)
        else:
            print("*" * 5, " RATED DOCUMENT: NOT RELEVANT", "*" * 5)
            continue
        
        #if not even half the docs are relevant
 
    return {
        
            "documents": filtered_docs,
            "question": question,
        
    }


