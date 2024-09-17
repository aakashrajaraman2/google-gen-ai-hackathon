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


dotenv.load_dotenv()

class GraphState(TypedDict):
    keys: Dict[str, any]




embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="cred.json"
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_KEY")
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

#suppress warnings
vertexai.init(project="vision-forge-414908", location="us-central1")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-001",
system_instruction="You will be given various tasks in the following prompts. Remember that you must be as elaborate and professional as possible. Understand the task carefully, then respond"
)



paths =[
    "../docs/90ade7e39d5e481f9aeb772a19a30234.pdf",
    "../docs/English Health Handbook.pdf",
    "../docs/English Motor Handbook.pdf",
    "../docs/insurance_motor_car_motor_policy_booklet_241017_NMDMG10249_v3.pdf"
]

def prepare_docs():
    docs = [PyPDFLoader(url).load() for url in paths]
    docs_list = [item for sublist in docs for item in sublist]
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=1000, chunk_overlap=50
)
    doc_splits = text_splitter.split_documents(docs_list)
    return doc_splits

def lanceDBConnection(embed):
    db = lancedb.connect("/tmp/lancedb")
    table = db.create_table(
        "crag_demo",
        data=[{"vector": embed.embed_query("Hello World"), "text": "Hello World"}],
        mode="overwrite",
    )
    
    vectorstore = LanceDB.from_documents(
        documents=prepare_docs(),
        embedding=embeddings_model,
        connection=table,
    )
    retriever = vectorstore.as_retriever()

    return retriever

retriever = lanceDBConnection(embeddings_model)

def retrieve(state):#Node 1. will act as a tool
    """
    Helper function for retrieving documents. 

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("*" * 5, " RETRIEVE ", "*" * 5)
    state_dict = state["keys"]
    question = state_dict["question"]
    documents = retriever.invoke(question)
    
    return {"keys": {"documents": documents, "question": question}}#return the same state dict


def grade_documents(state):#node 2
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with relevant documents
    """

    state_dict = state["keys"]
    question = state_dict["question"]
    documents = state_dict["documents"]
    
    binary_score: str = Field(description="Relevance score 'yes' or 'no'")

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
    search = "No"  # Default do not opt for web search to supplement retrieval
    for d in documents:
        score = chain.invoke({"question": question, "context": d.page_content})
        score = [score.content.replace("\n", "")]
        print("THIS IS THE SCORE:", score)
        grade2 = score[0]
        if "yes" in grade2 or "Yes" in grade2:
            print("*" * 5, " RATED DOCUMENT: RELEVANT", "*" * 5)
            filtered_docs.append(d)
        else:
            print("*" * 5, " RATED DOCUMENT: NOT RELEVANT", "*" * 5)
            continue
        
        #if not even half the docs are relevant
    if len(filtered_docs) < int(len(documents)/2):
        print(len(filtered_docs), "     ", len(documents))
        search = "Yes"

    return {
        "keys": {
            "documents": filtered_docs,
            "question": question,
            "run_web_search": search,
        }
    }

def decide_to_generate(state):#node 5
    """
    Helper function to determine whether to generate an answer or re-generate a question for web search.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        str: Next node to call
    """

    print("*" * 5, " DECIDE TO GENERATE ", "*" * 5)
    state_dict = state["keys"]
    search = state_dict["run_web_search"]

    if "yes" in search or "Yes" in search:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print("*" * 5, " DECISION: TRANSFORM QUERY and RUN WEB SEARCH ", "*" * 5)
        return "transform_query"
    else:
        # We have relevant documents, so generate answer
        print("*" * 5, " DECISION: GENERATE ", "*" * 5)
        return "generate"

def transform_query(state):#node 4
    """
    Helper function for transforming the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("*" * 5, "TRANSFORM QUERY", "*" * 5)
    state_dict = state["keys"]
    question = state_dict["question"]
    documents = state_dict["documents"]

    # Create a prompt template with format instructions and the query
    prompt = PromptTemplate(
        template="""You are generating questions that is well optimized for retrieval. \n
        Look at the input and try to reason about the underlying sematic intent / meaning. \n
        You have to modify the search query to only look for Indian related results. 
        Only return the question, no further explanation or text.\n
        Here is the initial question:
        \n --------- \n
        {question}
        \n --------- \n
        Formulate an improved question: """,
        input_variables=["question"],
    )

    model = llm

    # Prompt
    chain = prompt | model | StrOutputParser()
    better_question = chain.invoke({"question": question})
    print(better_question)

    return {"keys": {"documents": documents, "question": better_question}}

def web_search(state):#node 6
   
    print("*" * 5, " WEB SEARCH ", "*" * 5)
    state_dict = state["keys"]
    question = state_dict["question"]
    documents = state_dict["documents"]

    tool = tavily_client.search(    query=question,
                                    search_depth="advanced",
                                    include_answer=True,
                                    include_domains=["https://www.acko.com/car-insurance/irdai-rules/", "https://www.lexisnexis.in/blogs/insurance-law-in-india/."])

    docs = tool["answer"]
    #web_results = "\n".join([d["content"] for d in docs])
    #print(web_results)
    web_results = Document(page_content=docs)
    documents.append(web_results)

    return {"keys": {"documents": documents, "question": question}}

def generate(state):#node 3. also, end.
    """
    Helper function for generating answers

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("*" * 5, " GENERATE ", "*" * 5)
    state_dict = state["keys"]
    question = state_dict["question"]
    documents = state_dict["documents"]

    # Prompt
    prompt = PromptTemplate(
    template='''
    You are an assistant for insurance related question-answering tasks. If the question is not insurance related, please respond with, "I can't answer that".
    Use the following pieces of insurance policies context to answer the question. 
    If you don't know the answer, just say that you don't know. 
    Give as much information as possible. Use a professional tone, and elaborate as much as you can.
    Try to explain the information in a simple manner so even beginners can understand. This info will be used by people applying for insurance.
    Do not address the user by saying "in the context you gave me" etc. simply act as an encyclopedia, and answer the question.

    Question: {question} 

    Context: {context} 

    Format your answer as a very short html script. The only tags you can use are <p>, <ol>, <li>.
    Answer:
    ''',
    input_variables=["question", "context"],)

    # LLM


    # RAG Chain
    rag_chain = prompt | llm 

    # Run generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    return {
        "keys": {"documents": documents, "question": question, "generation": generation}
    }

def generate_langgraph():
    # Define the nodes
    workflow = StateGraph(GraphState)#inherit empty state

    #nodes work by (node_name, function_of_node)
    workflow.add_node("retrieve", retrieve)  # retrieve docs
    workflow.add_node("grade_documents", grade_documents)  # grade retrieved docs
    workflow.add_node("generate", generate)  # generate answers
    workflow.add_node("transform_query", transform_query)  # transform_query for web search
    workflow.add_node("web_search", web_search)  # web search

    # Build graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(#conditional edges are based on a condition, which is a function that returns a boolean value
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        },
    )
    workflow.add_edge("transform_query", "web_search")
    workflow.add_edge("web_search", "generate")
    workflow.add_edge("generate", END)

    # Compile
    app = workflow.compile()
    return app


