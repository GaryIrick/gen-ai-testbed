from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import openai

from settings import AppSettings

app_settings = AppSettings()

st.set_page_config(page_title="Tool Comparison - Raw OpenAI", page_icon="ocelot.ico")

openai.api_base = app_settings.chat_api_endpoint
openai.api_type = "azure"
openai.api_key = app_settings.chat_api_key
openai.api_version = "2023-07-01-preview"

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


def show_chat_history():
    for message in st.session_state["chat_history"]:
        role = message["role"]
        content = message["content"]
        completion = message["completion"]

        with st.chat_message(name=role):
            st.write(content)

        if completion:
            st.json(completion, expanded=False)


def append_to_chat_history(role, content, completion=None):
    st.session_state["chat_history"].append(
        {
            "role": role,
            "content": content,
            "completion": completion,
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

    completion = openai.ChatCompletion.create(
        engine=app_settings.chat_model, messages=get_conversation()
    )
    response = completion.choices[0].message.content
    role = completion.choices[0].message.role

    append_to_chat_history(role, response, completion)

show_chat_history()
