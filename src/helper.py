import os
from git import Repo
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers import LanguageParser
from langchain.text_splitter import Language
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
import shutil
from git import GitCommandError
import logging

# Clone any GitHub repositories
def repo_ingestion(repo_url):
    try:
        repo_path = "repo/"
        
        # If repo directory exists, clear it
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            logging.info(f"Cleared existing repository folder: {repo_path}")

        # Create the repo directory and clone the repository
        os.makedirs(repo_path, exist_ok=True)
        logging.info(f"Cloning repository from {repo_url} into {repo_path}...")
        
        Repo.clone_from(repo_url, to_path=repo_path)
        logging.info("Repository cloned successfully.")

    except GitCommandError as e:
        logging.error(f"Git error during cloning: {e}")
        raise ValueError(f"Error cloning the repository: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during repo ingestion: {e}")
        raise ValueError(f"Unexpected error during repo ingestion: {e}")

def validate_repo_contents(repo_path):
    if not os.listdir(repo_path):
        raise ValueError("Cloning failed: repository is empty.")
    logging.info(f"Repository contents: {os.listdir(repo_path)}")

#Loading repositories as documents
def load_repo(repo_path):
    loader = GenericLoader.from_filesystem(repo_path,
                                        glob = "**/*",
                                       suffixes=[".py"],
                                       parser = LanguageParser(language=Language.PYTHON, parser_threshold=500)
                                        )
    
    documents = loader.load()

    return documents

#Creating text chunks 
def text_splitter(documents):
    documents_splitter = RecursiveCharacterTextSplitter.from_language(language = Language.PYTHON,
                                                             chunk_size = 2000,
                                                             chunk_overlap = 200)
    
    text_chunks = documents_splitter.split_documents(documents)

    return text_chunks

#loading embeddings model
def load_embedding():
    embeddings=OpenAIEmbeddings(disallowed_special=())
    return embeddings
