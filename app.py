# app.py
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
import os
from visualizeData import prepare_graph_data
import weaviate

# Load environment variables
load_dotenv()

def connect_to_weaviate():
    return weaviate.connect_to_wcs(
        cluster_url=os.getenv("WCS_URL"),
        auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WCS_API_KEY")),
        headers={
            "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"]
        }
    )

def show_collection(client, collection_name):
    collection = client.collections.get(collection_name)
    response = collection.query.fetch_objects(include_vector=True)
    return response

def format_output(objects):
    data = [{"properties": o.properties, "vector": o.vector} for o in objects]
    return data

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/graph-data')
def graph_data():
    # Connect to Weaviate
    with connect_to_weaviate() as client:
        collection = show_collection(client, "GithubIssues")
        collection_output = format_output(collection.objects)
        graph_json = prepare_graph_data(collection_output)
        print(jsonify(graph_json))
        return jsonify(graph_json)

if __name__ == "__main__":
    app.run(debug=True)
