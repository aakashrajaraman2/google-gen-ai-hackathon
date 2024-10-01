# Polisense

## Problem Statement 8 for Google Gen AI Exchange:
Revolutionize Insurance Accessibility and Trust with AI. Develop an AI-powered humanoid agent that transforms the insurance experience for consumers. The platform should:

- Simplify: Provide 24/7, personalized guidance on policy selection and claims via voice, video, or chat.
- Educate: Ensure clear understanding of policy terms and accurate disclosures, fostering trust.
- Streamline: Automate form-filling with AI for error-free applications and higher claim acceptance rates.
- Focus Area (Subset): Prioritize building an AI-powered form-filling assistant for immediate impact.

## Solution
Polisense is an AI-powered chatbot system designed to tackle two key challenges in the insurance industry:
- Improving financial literacy among policyholders and prospective users.
- Streamlining the claims filing process to ensure ease and accuracy.
The chatbot leverages the Gemini LLM powered by a Corrective-RAG (CRAG) methodology to provide an intuitive, conversational interface for insurance-related inquiries and to simplify claims processing.

## Key Features
- Conversational Interface: Users can ask questions about insurance policies in simple terms and get accurate, easy-to-understand answers.
- Real-time Policy Insights: Ensures users are fully informed before they apply for a policy or file a claim.
- Auto-Fill for Claims: After a detailed conversation, the chatbot auto-fills claim forms using relevant information from the conversation.
- Corrective-RAG Methodology: Provides factually grounded responses and supplements policy information with reliable web searches.

## How to Run the Project
Clone this repository to your local machine:
```git clone <repo_url>```  
```cd <project_directory>```

Install dependencies:

```pip install -r requirements.txt```

**Set up your environment variables:**

- GCP API keys for deploying to Cloud Run.
- Hugging Face API key for embeddings.


Run the application locally:

```python app.py```
For production, deploy the Flask application using Docker. A sample Dockerfile is provided in the root folder.


**Note:** For the purposes of this hackathon, both the documents and user profile have been hardcoded to allow the workflow to focus solely on the performance of the application and adherance to the hackathon problem statement. In production, a database for users, and long term storage for documents and vectors would also be integrated and interfaced with their respoective SDKs.
