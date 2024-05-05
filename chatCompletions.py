import openai
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import Generator

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialisiere Gesprächsverlauf
conversation = [{"role": "system", "content": "you are a helpful assistant."}]
message_buffer = []


async def get_results(prompt: str, conversation: list) -> Generator: # type: ignore
    message_buffer = []
    conversation.append({"role": "user", "content": prompt})

    # Kürzen Sie das Array auf die letzten 20 Elemente, falls nötig
    if len(conversation) > 20:
        conversation = conversation[-20:]

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation,
        temperature=0.8,
        stream=True
    )

    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            chunk_content = chunk.choices[0].delta.content
            message_buffer.append(chunk_content)
            yield chunk_content

    complete_message = "".join(message_buffer)
    yield "__message_finished__"
    conversation.append({"role": "assistant", "content": complete_message})
    print([message['content'] for message in conversation])