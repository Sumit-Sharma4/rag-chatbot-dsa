from dotenv import load_dotenv
load_dotenv()

import os
from pinecone import Pinecone

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore



# Initialize Embeddings

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)



# Connect to Pinecone

pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
)

index_name = os.getenv("PINECONE_INDEX_NAME")

vectorstore = PineconeVectorStore(
    index_name=index_name,
    embedding=embeddings
)

retriever = vectorstore.as_retriever(search_kwargs={"k":5})



# Gemini LLM

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)



# Chat History

history = []



# Query Rewriting (Follow-up Questions)

def rewrite_question(question):

    prompt = f"""
You are a query rewriting expert.

Based on the conversation history below,
rewrite the user's follow-up question into
a complete standalone question.

Chat History:
{history}

User Question:
{question}

Return ONLY the rewritten question.
"""

    response = llm.invoke(prompt)

    return response.content.strip()



# Ask LLM with Context

def ask_llm(question, context):

    prompt = f"""
You are a Data Structure and Algorithm expert.

You will be given a context of relevant information
and a user question.

Your task is to answer the question using ONLY the context.
 Give a SHORT answer (1–2 sentences).
- If the question asks for time complexity, answer only with the complexity.
- Do NOT explain unrelated algorithms.

If the answer is not present in the context say:

"I could not find the answer in the provided document."

Keep answers clear and educational.

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)

    return response.content



# Main Query Loop

print("\nRAG System Ready!")
print("Type 'exit' to quit.\n")


while True:

    question = input("Ask me anything --> ")

    if question.lower() == "exit":
        break


    # Step 1: Rewrite query if it is follow-up
    standalone_question = rewrite_question(question)


    # Step 2: Retrieve documents from Pinecone
    docs = retriever.invoke(standalone_question)

    context = "\n\n---\n\n".join([doc.page_content for doc in docs])


    # Step 3: Send context + question to LLM
    answer = ask_llm(standalone_question, context)


    # Save conversation history
    history.append({
        "user": question,
        "assistant": answer
    })


    print("\nAnswer:\n")
    print(answer)
    print("\n--------------------------------------\n")
