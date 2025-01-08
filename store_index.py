from src.helper import repo_ingestion, load_repo, text_splitter, load_embedding
from dotenv import load_dotenv
from langchain.vectorstores import Chroma
import os
import logging

load_dotenv()

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Example: URL for GitHub repository
# url = "https://github.com/sabahatatta/Multimodal-AI-Chat-Bot"
# repo_ingestion(url)

# Load repository
repo_path = "repo/"
documents = load_repo(repo_path)

# Split the documents into text chunks
text_chunks = text_splitter(documents)

# Load embeddings
embeddings = load_embedding()

# Create Chroma vector store
persist_directory = './db'

# Check if the directory exists; if not, create it
if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)
    logging.info(f"Created directory {persist_directory}")

# Initialize the Chroma vector store
try:
    vectordb = Chroma.from_documents(text_chunks, embedding=embeddings, persist_directory=persist_directory)
    vectordb.persist()  # Persist the vector store
    logging.info(f"Vector store persisted successfully at {persist_directory}")

except Exception as e:
    logging.error(f"Error during Chroma vector store creation or persistence: {e}")
    raise

