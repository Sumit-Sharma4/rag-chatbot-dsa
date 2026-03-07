from dotenv import load_dotenv
load_dotenv()

import os
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone


print("Loading PDF...")

loader = PyPDFLoader("data/dsa.pdf")
documents = loader.load()

print("PDF Loaded")


# ----------------------------
# Split Documents into Chunks
# ----------------------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=100
)

chunks = splitter.split_documents(documents)

print("Chunking Completed")
print(f"Total Chunks Created: {len(chunks)}")


# ----------------------------
# Embedding Model (Gemini)
# ----------------------------
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

print("Embedding Model Ready")


# ----------------------------
# Initialize Pinecone
# ----------------------------
pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
)

index_name = os.getenv("PINECONE_INDEX_NAME")


# ----------------------------
# Upload Embeddings in Batches
# ----------------------------
batch_size = 30

print("Uploading vectors to Pinecone...")

for i in range(0, len(chunks), batch_size):

    batch = chunks[i:i + batch_size]

    while True:
        try:
            PineconeVectorStore.from_documents(
                documents=batch,
                embedding=embeddings,
                index_name=index_name
            )

            print(f"Uploaded batch {i//batch_size + 1}")

            # small delay to stay under Gemini limits
            time.sleep(15)

            break

        except Exception as e:
            print("⚠ Gemini rate limit hit. Waiting 60 seconds before retrying...")
            time.sleep(60)


print("✅ Data Stored in Pinecone Successfully")