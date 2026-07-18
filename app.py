from dotenv import load_dotenv
load_dotenv()

import os
import streamlit as st
from pinecone import Pinecone

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore



# Streamlit Page Config

st.set_page_config(page_title="DSA RAG Chatbot", page_icon="🤖")

st.title("📚 DSA RAG Chatbot")
st.write("Ask questions from the uploaded Data Structures & Algorithms PDF")



# Initialize Embeddings

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)



# Connect to Pinecone

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index_name = os.getenv("PINECONE_INDEX_NAME")

vectorstore = PineconeVectorStore(
    index_name=index_name,
    embedding=embeddings
)

retriever = vectorstore.as_retriever(search_kwargs={"k":3})



# Gemini LLM

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)



# Session State

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []



# Query Rewriting

def rewrite_query(question):

    prompt = f"""
You are a query rewriting expert.

Rewrite the follow-up question into a
complete standalone question.

Conversation History:
{st.session_state.history}

Question:
{question}

Return ONLY the rewritten question.
"""

    response = llm.invoke(prompt)

    return response.content.strip()


-
# Generate Answer

def generate_answer(question, context):

    prompt = f"""
You are a Data Structure and Algorithm expert.

Answer the question using ONLY the context.

Rules:
- Keep answers SHORT (1–2 sentences).
- If asked for time complexity, respond only with the complexity.
- If the answer is not in the context say:
"I could not find the answer in the provided document."

Context:
{context}

Question:
{question}

Short Answer:
"""

    response = llm.invoke(prompt)

    return response.content



# Display Chat History

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])



# Chat Input

if prompt := st.chat_input("Ask a DSA question"):

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )


    # Rewrite query
    standalone_question = rewrite_query(prompt)


    # Retrieve context
    docs = retriever.invoke(standalone_question)

    context = "\n\n---\n\n".join(
        [doc.page_content for doc in docs]
    )


    # Generate answer
    answer = generate_answer(standalone_question, context)


    # Display assistant message
    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )


    # Save history
    st.session_state.history.append(
        {"user": prompt, "assistant": answer}
    )
