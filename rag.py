import os
import pickle
import faiss
import numpy as np

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


DATA_FOLDER = "data"
INDEX_FILE = "vector.index"
CHUNKS_FILE = "chunks.pkl"

# Local embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def read_documents():
    """
    Reads TXT and PDF files from the data folder.
    """

    documents = []

    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    for filename in os.listdir(DATA_FOLDER):

        filepath = os.path.join(DATA_FOLDER, filename)

        # TXT files
        if filename.lower().endswith(".txt"):

            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    text = file.read()

                documents.append({
                    "source": filename,
                    "text": text
                })

            except Exception as e:
                print(f"Error reading {filename}: {e}")

        # PDF files
        elif filename.lower().endswith(".pdf"):

            try:
                reader = PdfReader(filepath)

                text = ""

                for page in reader.pages:
                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

                documents.append({
                    "source": filename,
                    "text": text
                })

            except Exception as e:
                print(f"Error reading {filename}: {e}")

    return documents


def split_text(text, chunk_size=500, overlap=100):
    """
    Splits large text into smaller chunks.
    """

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def create_chunks():

    documents = read_documents()

    all_chunks = []

    for document in documents:

        chunks = split_text(document["text"])

        for chunk in chunks:

            all_chunks.append({
                "source": document["source"],
                "text": chunk
            })

    return all_chunks


def build_vector_database():

    print("Reading documents...")

    chunks = create_chunks()

    if not chunks:
        raise ValueError(
            "No documents found inside the data folder."
        )

    texts = [chunk["text"] for chunk in chunks]

    print("Creating embeddings...")

    embeddings = embedding_model.encode(
        texts,
        convert_to_numpy=True
    )

    embeddings = embeddings.astype("float32")

    # Normalize embeddings
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    faiss.write_index(index, INDEX_FILE)

    with open(CHUNKS_FILE, "wb") as file:
        pickle.dump(chunks, file)

    print("Vector database created successfully!")

    return len(chunks)


def load_vector_database():

    if not os.path.exists(INDEX_FILE):
        build_vector_database()

    index = faiss.read_index(INDEX_FILE)

    with open(CHUNKS_FILE, "rb") as file:
        chunks = pickle.load(file)

    return index, chunks


def search_documents(query, top_k=4):

    index, chunks = load_vector_database()

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    )

    query_embedding = query_embedding.astype("float32")

    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, index_position in zip(scores[0], indices[0]):

        if index_position == -1:
            continue

        result = chunks[index_position].copy()

        result["score"] = float(score)

        results.append(result)

    return results
