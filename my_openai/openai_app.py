import json

from dotenv import load_dotenv
import streamlit as st
import openai
import requests
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from settings import AppSettings

load_dotenv()

app_settings = AppSettings()

st.set_page_config(page_title="Tool Comparison - Raw OpenAI", page_icon="ocelot.ico")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


def append_to_chat_history(
    role, content=None, function_call=None, function_name=None, detail=None
):
    st.session_state["chat_history"].append(
        {
            "role": role,
            "content": content,
            "function_call": function_call,
            "function_name": function_name,
            "detail": detail,
        }
    )


def get_heroes_stats(start_date, end_date):
    url = f"{app_settings.heroes_api_endpoint}/hero-stats"
    params = {"startDate": start_date, "endDate": end_date}
    req = requests.get(url, params)
    return req.json()


# https://learn.microsoft.com/en-us/python/api/overview/azure/search-documents-readme?view=azure-python


def search_for_hotel_information(query, count=3):
    credential = AzureKeyCredential(app_settings.search_api_key)
    client = SearchClient(
        endpoint=app_settings.search_api_endpoint,
        index_name=app_settings.search_index,
        credential=credential,
    )

    results = list(
        client.search(
            search_text=query,
            top=int(count),
            select=[
                "HotelName",
                "Description",
                "Address",
                "Rating",
                "Rooms",
            ],
        )
    )

    # Trim down the data we return to save on tokens.
    for result in results:
        del result["@search.score"]
        del result["@search.highlights"]

        result["Rooms"] = [
            {
                "Description": room["Description"],
                "BaseRate": room["BaseRate"],
                "SleepsCount": room["SleepsCount"],
            }
            for room in result["Rooms"]
        ]

    return results


# See this link for more about function calling:
#
# https://platform.openai.com/docs/api-reference/chat/create

available_functions = [
    {
        "name": "get_heroes_winrate_stats",
        "description": "Pass in a date range and get statistics for all heroes over that date range.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "first day of the date range as YYYY-MM-DD",
                },
                "end_date": {
                    "type": "string",
                    "description": "last day of the date range as YYYY-MM-DD",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
    {
        "name": "get_hotel_information",
        "description": "Perform a search for current information about hotels.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "a query to use to find information about hotels",
                },
                "count": {
                    "type": "string",
                    "description": "the number of results to find",
                },
            },
            "required": ["query"],
        },
    },
]

# All of these functions return a dictionary created from a JSON response.
# The data will be serialized and sent back to the LLM.
map_of_available_functions = {
    "get_heroes_winrate_stats": get_heroes_stats,
    "get_hotel_information": search_for_hotel_information,
}

openai.api_base = app_settings.chat_api_endpoint
openai.api_type = "azure"
openai.api_key = app_settings.chat_api_key
openai.api_version = "2023-07-01-preview"


def show_chat_history():
    for message in st.session_state["chat_history"]:
        role = message["role"]
        content = message.get("content")
        detail = message.get("detail")

        avatar = None

        if role == "system":
            avatar = "🤖"

        if role == "function":
            avatar = "⚡"
            content = "Here's the data you asked for.  (Actual content is serialized JSON, see the detail below.)"

        if content is None:
            content = "Please call a function for me."

        with st.chat_message(name=role, avatar=avatar):
            st.write(content)

        if detail:
            st.json(detail, expanded=False)


def get_conversation():
    def make_message(dict):
        role = dict.get("role")
        content = dict.get("content")
        function_call = dict.get("function_call")
        function_name = dict.get("function_name")

        # content is required, even if it's None
        message = {"role": role, "content": content}

        if function_call is not None:
            message["function_call"] = function_call

        if function_name is not None:
            message["name"] = function_name

        return message

    return [make_message(m) for m in st.session_state["chat_history"]]


def make_llm_call(max_recursion, recursion_count=0):
    # Protect against the LLM asking for lots of function calls in a row.
    if recursion_count > max_recursion:
        raise ValueError("Too many recursive calls to LLM.")

    messages = get_conversation()
    llm_response = openai.ChatCompletion.create(
        engine=app_settings.chat_model,
        messages=messages,
        functions=available_functions,
        function_call="auto",
    )
    response_message = llm_response.choices[0].message
    role = response_message["role"]
    content = response_message.get("content")
    function_call = response_message.get("function_call")

    if function_call:
        function_name = function_call["name"]
        python_function_to_call = map_of_available_functions[function_name]
        function_args = json.loads(function_call["arguments"])
        function_response = python_function_to_call(**function_args)
        append_to_chat_history(
            role,
            function_call=response_message["function_call"],
            detail=function_call,
        )
        append_to_chat_history(
            "function",
            content=json.dumps(function_response),
            function_name=function_name,
            detail=function_response,
        )
        make_llm_call(max_recursion, recursion_count + 1)
    else:
        append_to_chat_history(role, content=content, detail=llm_response)


prompt = st.chat_input("Ask a question")

if prompt:
    append_to_chat_history("user", content=prompt)
    make_llm_call(max_recursion=5)


show_chat_history()
