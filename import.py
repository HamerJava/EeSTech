import weaviate
import os
import openai
from dotenv import load_dotenv
import pandas as pd
from weaviate import auth
from weaviate.classes.config import Property, DataType, Tokenization

# Load environment variables
load_dotenv()

# Initialize Weaviate client connection
client = weaviate.connect_to_wcs(
    cluster_url=os.getenv("WCS_URL"),
    auth_credentials=auth.AuthApiKey(os.getenv("WCS_API_KEY")),
    headers={
        "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"]
    }
)

def clear_data():
    """Clear data if a collection exists."""
    client.collections.delete("GithubIssues")
    client.collections.delete("Solved")

def create_collection():
    """Create the collection schema with all required properties, skipping vectorization as needed."""
    client.collections.create(
        name="GithubIssues",
        vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_openai(model="text-embedding-3-small"),
        properties=[
            Property(name="issue_id", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="title", data_type=DataType.TEXT, vectorize_property_name=True, tokenization=Tokenization.LOWERCASE),
            Property(name="body", data_type=DataType.TEXT, skip_vectorization=True, tokenization=Tokenization.WHITESPACE),
            Property(name="urgency", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="type", data_type=DataType.TEXT),
            Property(name="repo_name", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="state", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="created", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="updated", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="user_login", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="url", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="comments", data_type=DataType.NUMBER, skip_vectorization=True),
            Property(name="user_type", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="labels", data_type=DataType.TEXT_ARRAY, skip_vectorization=True),
            Property(name="assignees", data_type=DataType.TEXT_ARRAY, skip_vectorization=True)
        ]
    )
    print(client.collections.exists("GithubIssues"))

def create_solved_collection():
    """Create the Solved collection schema with all required properties."""
    client.collections.create(
        name="Solved",
        vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_openai(model="text-embedding-3-small"),
        properties=[
            Property(name="issue_id", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="title", data_type=DataType.TEXT, vectorize_property_name=True, tokenization=Tokenization.LOWERCASE),
            Property(name="body", data_type=DataType.TEXT, skip_vectorization=True, tokenization=Tokenization.WHITESPACE),
            Property(name="urgency", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="type", data_type=DataType.TEXT),
            Property(name="repo_name", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="state", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="created", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="updated", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="user_login", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="url", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="comments", data_type=DataType.NUMBER, skip_vectorization=True),
            Property(name="user_type", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="labels", data_type=DataType.TEXT_ARRAY, skip_vectorization=True),
            Property(name="assignees", data_type=DataType.TEXT_ARRAY, skip_vectorization=True)
        ]
    )
    print(client.collections.exists("Solved"))


def generate_urgency(title, body):
    """Generate an urgency score using OpenAI GPT."""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Rate the Urgency from the given Issue or Pull Request. Respond with one number only. 1 = not very urgent, 4 = extremely urgent."},
            {"role": "user", "content": f"This is the title of the issue or pull request: '{title}' and the body: '{body}'"}
        ],
        temperature=1,
        max_tokens=1
    )
    urgency = response.choices[0].message.content
    print(urgency)
    return urgency

def load_data_to_weaviate():
    """Load issues and pull requests into Weaviate."""
    df = pd.read_pickle('data/github_issues.pkl')

    # Prepare the collection for batch import
    collection = client.collections.get("GithubIssues")

    with collection.batch.dynamic() as batch:
        for i, (issue_id, row) in enumerate(df.iterrows(), start=1):
            # Extract properties from the row, including the index as `issue_id`
            title = str(row['title'])
            body = str(row['body'])
            pr = str(row['pr'])
            repo_name = str(row['repo_name'])
            state = str(row['state'])
            created = str(row['created'])
            updated = str(row['updated'])
            user_login = str(row['user_login'])
            url = str(row['url'])
            comments = int(row['comments']) if row['comments'] else 0
            user_type = str(row['user_type'])
            labels = list(map(str, row['labels']))
            assignees = list(map(str, row['assignees']))

            # Display the current progress using `i`
            print(f"Importing {pr} {i}/{len(df)}: {title}")

            # Determine urgency
            urgency = generate_urgency(title, body)

            # Prepare properties with the new schema, including the `issue_id` field
            properties = {
                "issue_id": str(issue_id),  # Add the index value as `issue_id`
                "title": title,
                "body": body,
                "urgency": urgency,
                "type": "pull request" if pr == "pull-request" else "issue",
                "repo_name": repo_name,
                "state": state,
                "created": created,
                "updated": updated,
                "user_login": user_login,
                "url": url,
                "comments": comments,
                "user_type": user_type,
                "labels": labels,
                "assignees": assignees
            }

            batch.add_object(properties)

    print("All data imported successfully with urgency, issue ID, and additional properties.")

# Main execution
if __name__ == "__main__":
    clear_data()
    create_collection()
    load_data_to_weaviate()
