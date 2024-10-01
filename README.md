#Polisense - Simply Secure
Polisense is an AI-powered chatbot system designed to tackle two key challenges in the insurance industry:

Improving financial literacy among policyholders and prospective users.
Streamlining the claims filing process to ensure ease and accuracy.
The chatbot leverages the Gemini LLM powered by a Corrective-RAG (CRAG) methodology to provide an intuitive, conversational interface for insurance-related inquiries and to simplify claims processing.

Key Features
Conversational Interface: Users can ask questions about insurance policies in simple terms and get accurate, easy-to-understand answers.
Real-time Policy Insights: Ensures users are fully informed before they apply for a policy or file a claim.
Auto-Fill for Claims: After a detailed conversation, the chatbot auto-fills claim forms using relevant information from the conversation.
Corrective-RAG Methodology: Provides factually grounded responses and supplements policy information with reliable web searches.
24/7 Availability: The chatbot is always accessible, offering answers anytime users need help.
Policy-Specific Answers: Users get accurate, context-specific answers to complex insurance-related queries.
Easily Updatable: New policy information and updates can be added seamlessly, ensuring the chatbot remains up-to-date.
Technologies Used
Gemini 1.5 Flash Model: For understanding user queries and providing accurate responses.
Flask: For building the API.
Langchain: To orchestrate the LLM, define prompt templates, and manage interactions.
LanceDB: For storing document vectors and running similarity searches.
Langgraph: To manage the Corrective RAG workflow.
Hugging Face Embeddings: (all-MiniLM-L6-v2) to generate embeddings for documents.
HTML/CSS/JS: For the front-end interface design.
Google Cloud Platform (GCP) Cloud Run: For deploying the application.
Challenges We Faced
Retrieval Process and CRAG Methodology
One of the biggest challenges was handling the retrieval of information from insurance policy documents. These documents contain technical terms and complex language that don't always match up with user queries. This caused inconsistencies in the responses, where relevant information wasn’t always returned.

While insurance policies contain detailed information, users often require additional context—such as legal standards or common practices—to fully understand the implications of their policies. The lack of this context created confusion, particularly when users were trying to file claims or assess policy options.

To address these issues, we implemented the Corrective-RAG (CRAG) methodology. CRAG ensures that all responses are grounded in factual policy data, and supplements it with web searches when additional information is required. This not only improved the relevance and accuracy of responses but also allowed the chatbot to better handle the nuanced terminology found in the documents.

How to Run the Project
Clone this repository to your local machine:

bash
Copy code
git clone <repo_url>
Navigate to the project directory:

bash
Copy code
cd <project_directory>
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Set up your environment variables:

GCP API keys for deploying to Cloud Run.
Hugging Face API key for embeddings.
Run the application locally:

bash
Copy code
flask run
For production, deploy the Flask application using Docker. A sample Dockerfile is provided:

bash
Copy code
docker build -t polisense .
docker run -p 8080:8080 polisense
To deploy to GCP Cloud Run, follow these steps:

Set up your GCP project and enable Cloud Run.
Deploy the Docker image to Cloud Run.
Contact
