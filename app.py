import os

import streamlit as st

from dotenv import load_dotenv
from google import genai

from rag import search_documents, build_vector_database

from tools import use_tool

from memory import (
    load_memory,
    add_message,
    clear_memory
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Student Support Assistant",
    page_icon="🎓",
    layout="centered"
)


# ============================================================
# GEMINI MODELS
# ============================================================

# Models available for your API key
# If one model is temporarily unavailable,
# the next model will automatically be tried.

MODELS_TO_TRY = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash"
]


# ============================================================
# TITLE
# ============================================================

st.title("🎓 AI Student Support Assistant")

st.write(
    "Ask questions about syllabus, exams, "
    "fees, college rules and student information."
)


# ============================================================
# CHECK API KEY
# ============================================================

if not API_KEY:

    st.error(
        "❌ GEMINI_API_KEY is missing.\n\n"
        "Please add your Gemini API key to the .env file."
    )

    st.stop()


# ============================================================
# CREATE GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=API_KEY
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Project Controls")

    st.markdown("---")

    st.subheader("🤖 Gemini Models")

    for model in MODELS_TO_TRY:

        st.write(f"• {model}")

    st.markdown("---")


    # ========================================================
    # REBUILD RAG DATABASE
    # ========================================================

    if st.button("🔄 Rebuild RAG Database"):

        try:

            with st.spinner(
                "Rebuilding RAG database..."
            ):

                count = build_vector_database()

            st.success(
                f"RAG database rebuilt successfully!\n\n"
                f"Total chunks: {count}"
            )

        except Exception as e:

            st.error(
                f"❌ RAG Error:\n{str(e)}"
            )


    # ========================================================
    # CLEAR MEMORY
    # ========================================================

    if st.button("🗑️ Clear Memory"):

        clear_memory()

        st.session_state.messages = []

        st.success(
            "Conversation memory cleared!"
        )


    st.markdown("---")


    # ========================================================
    # AVAILABLE INFORMATION
    # ========================================================

    st.subheader("📚 Available Information")

    st.write("✅ Syllabus")

    st.write("✅ Exam Schedule")

    st.write("✅ College Rules")

    st.write("✅ Fees")

    st.write("✅ Attendance")

    st.write("✅ Student Support")


# ============================================================
# INITIALIZE SESSION MEMORY
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = load_memory()


# ============================================================
# DISPLAY PREVIOUS CHAT
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input(
    "Ask your question..."
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    # --------------------------------------------------------
    # DISPLAY USER QUESTION
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(question)


    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    user_message = {

        "role": "user",

        "content": question

    }

    st.session_state.messages.append(
        user_message
    )

    add_message(
        "user",
        question
    )


    # ========================================================
    # TOOL SEARCH
    # ========================================================

    try:

        tool_result = use_tool(
            question
        )

    except Exception as e:

        tool_result = None

        st.warning(
            f"Tool error: {str(e)}"
        )


    # ========================================================
    # RAG SEARCH
    # ========================================================

    try:

        rag_results = search_documents(
            question,
            top_k=4
        )

    except Exception as e:

        rag_results = []

        st.warning(
            f"RAG search error: {str(e)}"
        )


    # ========================================================
    # CREATE DOCUMENT CONTEXT
    # ========================================================

    document_context = ""

    sources = []


    for result in rag_results:

        document_context += (

            f"\n"
            f"Source: {result['source']}\n"
            f"Content: {result['text']}\n"

        )

        if result["source"] not in sources:

            sources.append(
                result["source"]
            )


    # ========================================================
    # CREATE TOOL CONTEXT
    # ========================================================

    tool_context = ""


    if tool_result:

        tool_context = (

            f"\nTool Used: "
            f"{tool_result['tool']}\n"

            f"Tool Result: "
            f"{tool_result['result']}\n"

        )


    # ========================================================
    # LOAD CONVERSATION MEMORY
    # ========================================================

    previous_messages = load_memory()

    memory_context = ""


    for message in previous_messages[-10:]:

        memory_context += (

            f"{message['role']}: "
            f"{message['content']}\n"

        )


    # ========================================================
    # SYSTEM INSTRUCTIONS
    # ========================================================

    system_prompt = """

You are an AI Student Support Assistant.

Your purpose is to help college students
with college-related questions.

IMPORTANT RULES:

1. Use the provided college document context
   whenever it is relevant.

2. Use the provided tool information whenever
   a tool result is available.

3. Use previous conversation context to
   understand follow-up questions.

4. Do not invent college information.

5. If the required information is not present
   in the documents, tools or conversation,
   clearly tell the student that the information
   is not available.

6. Keep answers simple, clear and useful.

7. Answer in the same language as the student
   whenever possible.

8. Do not claim that an action was performed
   unless it was actually performed.

9. If the question is about college information,
   prioritize the provided college resources.

10. Do not use unrelated general knowledge when
    answering college-specific questions.

"""


    # ========================================================
    # USER PROMPT
    # ========================================================

    user_prompt = f"""

STUDENT QUESTION:

{question}


PREVIOUS CONVERSATION:

{memory_context}


COLLEGE DOCUMENT CONTEXT:

{document_context}


TOOL INFORMATION:

{tool_context}


Please answer the student's question using
the available information.
"""


    # ========================================================
    # GEMINI MULTI-MODEL FALLBACK
    # ========================================================

    answer = None

    last_error = None

    successful_model = None


    # --------------------------------------------------------
    # TRY EACH GEMINI MODEL
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        status_box = st.empty()

        status_box.info(
            "🤖 Connecting to Gemini..."
        )


        for model_name in MODELS_TO_TRY:

            try:

                status_box.info(
                    f"🤖 Trying {model_name}..."
                )


                response = client.models.generate_content(

                    model=model_name,

                    contents=f"""
{system_prompt}

{user_prompt}
"""

                )


                # --------------------------------------------
                # CHECK RESPONSE
                # --------------------------------------------

                if response is None:

                    raise Exception(
                        "Empty response from Gemini."
                    )


                if not response.text:

                    raise Exception(
                        "Gemini returned an empty response."
                    )


                # --------------------------------------------
                # SUCCESS
                # --------------------------------------------

                answer = response.text

                successful_model = model_name

                break


            except Exception as e:

                last_error = e

                # --------------------------------------------
                # TRY NEXT MODEL
                # --------------------------------------------

                continue


        # ====================================================
        # ALL MODELS FAILED
        # ====================================================

        if answer is None:

            answer = (
                "❌ Sorry, I could not generate an answer.\n\n"
                "All configured Gemini models are "
                "temporarily unavailable.\n\n"
                f"Last error: {last_error}"
            )


        # ====================================================
        # CLEAR STATUS
        # ====================================================

        status_box.empty()


        # ====================================================
        # DISPLAY ANSWER
        # ====================================================

        st.markdown(answer)


        # ====================================================
        # SHOW MODEL USED
        # ====================================================

        if successful_model:

            st.caption(
                f"🤖 Model used: {successful_model}"
            )


    # ========================================================
    # SAVE AI RESPONSE TO MEMORY
    # ========================================================

    assistant_message = {

        "role": "assistant",

        "content": answer

    }


    st.session_state.messages.append(
        assistant_message
    )


    add_message(
        "assistant",
        answer
    )


    # ========================================================
    # DISPLAY SOURCES
    # ========================================================

    if sources:

        with st.expander(
            "📚 Sources"
        ):

            for source in sources:

                st.write(
                    f"📄 {source}"
                )


    # ========================================================
    # DISPLAY TOOL USED
    # ========================================================

    if tool_result:

        with st.expander(
            "🔧 Tool Information"
        ):

            st.write(
                f"Tool: {tool_result['tool']}"
            )

            st.write(
                f"Result: {tool_result['result']}"
            )