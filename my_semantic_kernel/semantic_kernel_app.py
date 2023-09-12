from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from settings import AppSettings
from my_semantic_kernel.in_memory_logger import get_in_memory_logger

app_settings = AppSettings()

st.set_page_config(
    page_title="Tool Comparison - Semantic Kernel", page_icon="ocelot.ico"
)


logger, handler = get_in_memory_logger()

kernel = sk.Kernel(log=logger)
kernel.add_chat_service(
    "chat",
    AzureChatCompletion(
        "ocelot-gpt4", app_settings.chat_api_endpoint, app_settings.chat_api_key
    ),
)

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


def show_chat_history():
    for message in st.session_state["chat_history"]:
        role = message["role"]
        content = message["content"]
        logs = message["logs"]

        with st.chat_message(name=role):
            st.write(content)

        if logs:
            st.json(logs, expanded=False)


def append_to_chat_history(role, content, logs=None):
    st.session_state["chat_history"].append(
        {
            "role": role,
            "content": content,
            "logs": logs,
        }
    )


def get_conversation():
    return [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state["chat_history"]
    ]


prompt = st.chat_input("Ask a question")

if prompt:
    append_to_chat_history("user", prompt)

    prompt_fn = kernel.create_semantic_function(prompt)
    response = prompt_fn()
    role = "assistant"

    append_to_chat_history(role, response.result, handler.get_logs())

show_chat_history()
