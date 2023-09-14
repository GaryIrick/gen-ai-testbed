from dotenv import load_dotenv

load_dotenv()

import streamlit as st


# We don't really need the langchain import here, but if we don't do it,
# we get spurious errors running this in streamlit, like:
#    - AttributeError: module 'langchain' has no attribute 'verbose'
#    - ImportError: cannot import name 'ChatOpenAI' from partially initialized module 'langchain.chat_models' (most likely due to a circular import)
import langchain

# Show the blow-by-blow as the agent runs.
langchain.debug = True

from langchain.schema import AIMessage, HumanMessage
from langchain.prompts.chat import MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import APIChain, LLMChain, RetrievalQA
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.retrievers import AzureCognitiveSearchRetriever

from my_langchain.callback_handler import CustomCallbackHandler

from settings import AppSettings

app_settings = AppSettings()

st.set_page_config(page_title="Tool Comparison - Langchain", page_icon="ocelot.ico")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


@st.cache_data
def get_api_spec():
    with open("resources/hots_api_spec.json") as api_spec_file:
        return api_spec_file.read()


llm = AzureChatOpenAI(
    openai_api_base=app_settings.chat_api_endpoint,
    openai_api_key=app_settings.chat_api_key,
    openai_api_type="azure",
    openai_api_version="2023-07-01-preview",
    deployment_name=app_settings.chat_model,
)

# We only return the "Description" field.  In a real example we
# would index this differently, but this is a convenient sample
# dataset provided by Azure.
retriever = AzureCognitiveSearchRetriever(
    service_name=app_settings.search_service,
    index_name=app_settings.search_index,
    api_key=app_settings.search_api_key,
    top_k=5,
    content_key="Description",
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
    conversation = get_conversation()
    append_to_chat_history("user", prompt)

    memory = ConversationBufferMemory(memory_key="chat_history")

    llm_chain = LLMChain(
        llm=llm, prompt=PromptTemplate.from_template("Answer this question: {content}")
    )
    chat_tool = Tool.from_function(
        llm_chain.run,
        name="chat",
        description="uses chat to answer general knowledge questions",
    )
    api_chain = APIChain.from_llm_and_api_docs(llm, get_api_spec())
    api_tool = Tool.from_function(
        api_chain.run,
        name="api",
        description="an API that can answer questions about win rates for Heroes of the Storm",
    )
    retrieval_chain = RetrievalQA.from_llm(
        llm=llm,
        retriever=retriever,
    )
    retrieval_tool = Tool.from_function(
        retrieval_chain.run,
        name="search",
        description="a index that can be searched to find information about hotels, and only hotels, not general knowledge questions",
    )

    # OPENAI_FUNCTIONS should take advantage of the "function calling" feature in the newest
    # gpt3.5 and gpt4 models.
    tools = [chat_tool, retrieval_tool, api_tool]
    agent = initialize_agent(
        tools=tools,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        llm=llm,
        memory=memory,
    )

    prompt_template = ChatPromptTemplate.from_messages(
        [
            # We would place the system message here, if we had one.
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{human_input}"),
        ]
    )

    handler = CustomCallbackHandler()
    full_prompt = prompt_template.format(human_input=prompt, chat_history=conversation)
    response = agent.run(input=full_prompt, callbacks=[handler])
    role = "ai"

    append_to_chat_history("ai", response, handler.events)

show_chat_history()
