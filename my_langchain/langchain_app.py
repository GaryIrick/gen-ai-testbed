from dotenv import load_dotenv

load_dotenv()

import streamlit as st

# We don't really need the langchain import here, but if we don't do it,
# we get spurious errors, like:
#    - AttributeError: module 'langchain' has no attribute 'verbose'
#    - ImportError: cannot import name 'ChatOpenAI' from partially initialized module 'langchain.chat_models' (most likely due to a circular import)
import langchain

from langchain.schema import AIMessage, HumanMessage
from langchain.chat_models import AzureChatOpenAI

from settings import AppSettings

app_settings = AppSettings()

st.set_page_config(page_title="Tool Comparison - Langchain", page_icon="ocelot.ico")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

chat = AzureChatOpenAI(
    openai_api_base=app_settings.chat_api_endpoint,
    openai_api_key=app_settings.chat_api_key,
    openai_api_type="azure",
    openai_api_version="2023-07-01-preview",
    deployment_name=app_settings.chat_model,
)


def show_chat_history():
    for message in st.session_state["chat_history"]:
        role = message["role"]
        content = message["content"]
        llm_response = message["llm_response"]

        with st.chat_message(name=role):
            st.write(content)

        if llm_response:
            st.json(llm_response, expanded=False)


def append_to_chat_history(role, content, llm_response=None):
    st.session_state["chat_history"].append(
        {
            "role": role,
            "content": content,
            "llm_response": llm_response,
        }
    )


def get_conversation():
    def get_message(m):
        if m["role"] == "user":
            return HumanMessage(content=m["content"])
        else:
            # We don't expect any "system" messages for now.
            return AIMessage(content=m["content"])

    return [get_message(m) for m in st.session_state["chat_history"]]


prompt = st.chat_input("Ask a question")

if prompt:
    append_to_chat_history("user", prompt)
    conversation = get_conversation()

    llm_response = chat.predict_messages(conversation)

    role = llm_response.type
    response = llm_response.content

    append_to_chat_history("ai", response, {"type": role, "content": response})

show_chat_history()
