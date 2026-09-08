import json
import os


MEMORY_FILE = "chat_memory.json"


def load_memory():

    if not os.path.exists(MEMORY_FILE):
        return []

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return []


def save_memory(memory):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            memory,
            file,
            indent=4,
            ensure_ascii=False
        )


def add_message(role, content):

    memory = load_memory()

    memory.append({

        "role": role,

        "content": content

    })

    memory = memory[-20:]

    save_memory(memory)


def clear_memory():

    if os.path.exists(MEMORY_FILE):

        os.remove(
            MEMORY_FILE
        )