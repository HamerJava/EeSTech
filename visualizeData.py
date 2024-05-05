import weaviate
import os
from dotenv import load_dotenv
import json
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import numpy as np

# Load environment variables
load_dotenv()

def connect_to_weaviate():
    """Connect to the Weaviate cluster."""
    return weaviate.connect_to_wcs(
        cluster_url=os.getenv("WCS_URL"),
        auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WCS_API_KEY")),
        headers={
            "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"]
        }
    )

def show_collection(client, collection_name):
    """Returns all objects in a collection."""
    collection = client.collections.get(collection_name)
    response = collection.query.fetch_objects(
        include_vector=True
    )
    return response

def format_output(objects):
    """Format output to be JSON serializable and extract vectors."""
    data = []
    for o in objects:
        data.append({
            "properties": o.properties,
            "vector": o.vector
        })
    return data

def pretty_print_properties(objects):
    """Pretty-print only the properties of each object."""
    properties_list = [obj['properties'] for obj in objects]
    pretty_json = json.dumps(properties_list, indent=4)
    print(pretty_json)

import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

def visualize_vectors(vectors):
    """Use t-SNE to reduce vector dimensions, plot them with titles and colors based on urgency, and output the collection with reduced vectors."""
    cleaned_vectors = []
    titles = []  # List to store titles for annotations
    markers = []  # List to store marker shapes (triangle or circle)
    urgencies = []  # List to store urgency levels for color coding
    colors = {1: 'green', 2: 'yellow', 3: 'orange', 4: 'red'}  # Map urgency to colors
    
    for vector_info in vectors:
        vector = vector_info["vector"]["default"]
        title = vector_info["properties"]["title"]
        try:
            urgency = int(vector_info["properties"]["urgency"])  # Attempt to parse the urgency value
        except (ValueError, TypeError):
            urgency = 2  # Set default urgency to 2 if parsing fails

        pr_type = vector_info["properties"]["type"]

        try:
            vector_np = np.array(vector, dtype=float)
            if np.isfinite(vector_np).all():
                cleaned_vectors.append(vector_np)
                titles.append(title)
                urgencies.append(colors[urgency])  # Map urgency to corresponding color
                
                # Set marker shapes based on whether it's a pull request or issue
                if pr_type == "pull request":
                    markers.append("^")  # Triangle marker
                else:
                    markers.append("o")  # Circle marker
            else:
                print("Non-finite numbers found in vector:", vector)
        except TypeError:
            print("Error converting vector to float:", vector)
    
    if len(cleaned_vectors) > 1:
        vectors_np = np.array(cleaned_vectors)
        perplexity_value = min(5, len(vectors_np) - 1)
        tsne = TSNE(n_components=2, perplexity=perplexity_value, learning_rate=100)
        vectors_reduced = tsne.fit_transform(vectors_np)
        
        # Prepare to output the collection with the reduced vectors
        collection_with_reduced = []
        plt.figure(figsize=(12, 8))
        
        for i, (txt, marker, color) in enumerate(zip(titles, markers, urgencies)):
            x, y = vectors_reduced[i]
            plt.scatter(x, y, alpha=0.5, color=color, marker=marker, edgecolor="black")  # Use black outline
            plt.annotate(txt, (x, y))
            
            reduced_vector_dict = {
                "properties": vectors[i]["properties"],  # Copy original properties
                "reduced_vector": vectors_reduced[i].tolist()  # Save reduced vector as a list
            }
            collection_with_reduced.append(reduced_vector_dict)
        
        plt.title('2D Visualization of Vectors using t-SNE with Titles and Urgency Colors')
        plt.xlabel('Dimension 1')
        plt.ylabel('Dimension 2')
        plt.show()
        
        # Output the enhanced collection data
        print(json.dumps(collection_with_reduced, indent=4))
    else:
        print("Not enough valid vectors to perform t-SNE.")

# In visualizeData.py or wherever `prepare_graph_data` is implemented

def prepare_graph_data(vectors):
    """Prepare graph data using t-SNE and return reduced vectors as JSON."""
    cleaned_vectors = []
    titles = []
    issue_ids = []  # Add a list to store issue IDs
    markers = []
    urgencies = []
    colors = {1: 'green', 2: 'yellow', 3: 'orange', 4: 'red'}

    for vector_info in vectors:
        vector = vector_info["vector"]["default"]
        title = vector_info["properties"]["title"]
        issue_id = vector_info["properties"]["issue_id"]  # Add issue_id to the data
        try:
            urgency = int(vector_info["properties"]["urgency"])
        except (ValueError, TypeError):
            urgency = 2  # Default urgency

        pr_type = vector_info["properties"]["type"]

        try:
            vector_np = np.array(vector, dtype=float)
            if np.isfinite(vector_np).all():
                cleaned_vectors.append(vector_np)
                titles.append(title)
                issue_ids.append(issue_id)  # Append to the issue ID list
                urgencies.append(colors[urgency])
                markers.append("^" if pr_type == "pull request" else "o")
            else:
                print("Non-finite numbers found in vector:", vector)
        except TypeError:
            print("Error converting vector to float:", vector)

    if len(cleaned_vectors) > 1:
        vectors_np = np.array(cleaned_vectors)
        perplexity_value = min(5, len(vectors_np) - 1)
        tsne = TSNE(n_components=2, perplexity=perplexity_value, learning_rate=100)
        vectors_reduced = tsne.fit_transform(vectors_np)

        reduced_vectors = [
            {"title": titles[i], "issue_id": issue_ids[i], "x": float(x), "y": float(y), "marker": markers[i], "color": urgencies[i]}
            for i, (x, y) in enumerate(vectors_reduced)
        ]

        return json.dumps(reduced_vectors, indent=4)

    else:
        return {"error": "Not enough valid vectors to perform t-SNE."}


# Main execution
if __name__ == "__main__":
    # Connect to Weaviate
    with connect_to_weaviate() as client:  # Ensure the connection is closed properly
        # Perform near text search
        collection = show_collection(client, "GithubIssues")
        collection_output = format_output(collection.objects)

        # Pretty print all properties only
        pretty_print_properties(collection_output)

        # Visualize vectors
        prepare_graph_data(collection_output)
        visualize_vectors(collection_output)
