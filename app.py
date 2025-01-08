from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from langchain.chains import ConversationalRetrievalChain
from src.helper import load_embedding, repo_ingestion
import os
import logging
import subprocess

# Flask app initialization
app = Flask(__name__)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing from the .env file.")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Embedding and VectorStore setup
embeddings = load_embedding()
persist_directory = "db"
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

# Chat model and memory setup
llm = ChatOpenAI()
memory = ConversationSummaryMemory(llm=llm, memory_key="chat_history", return_messages=True)
qa = ConversationalRetrievalChain.from_llm(
    llm, retriever=vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 8}), memory=memory
)

# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/chatbot", methods=["POST"])
def git_repo():
    try:
        user_input = request.form.get("question")
        if not user_input:
            logging.error("No repository link provided.")
            return jsonify({"error": "No repository link provided."}), 400

        # Ingest the repository
        logging.info(f"Received GitHub repository link: {user_input}")
        repo_ingestion(user_input)

        # Execute the script to store the index
        result = subprocess.run(["python", "store_index.py"], capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Error in store_index.py: {result.stderr}")
            return jsonify({"error": "Error while indexing the repository."}), 500

        logging.info("Repository indexed successfully.")
        return jsonify({"response": f"Processed repository: {user_input}"})
    except Exception as e:
        logging.error(f"Error in /chatbot: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/get", methods=["POST"])
def chat():
    try:
        msg = request.form.get("msg")
        if not msg:
            logging.error("No message provided.")
            return jsonify({"error": "No message provided."}), 400

        logging.info(f"User input: {msg}")

        if msg.lower() == "clear":
            os.system("rm -rf repo")
            logging.info("Repository cleared.")
            return jsonify({"response": "Repository cleared."})

        # Process user message through the QA chain
        result = qa(msg)
        bot_response = result.get("answer", "Sorry, I couldn't process your question.")
        logging.info(f"Chatbot response: {bot_response}")

        return jsonify({"response": bot_response})
    except Exception as e:
        logging.error(f"Error in /get: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
