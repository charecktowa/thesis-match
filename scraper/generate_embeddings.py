from http import HTTPStatus
import os
from time import sleep

import dashscope
from dotenv import load_dotenv

from app.db.database import SessionLocal
from app.db import models


load_dotenv()

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# Singapur region (we don't want to upload passport data to Beijing servers)
dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

BATCH_SIZE = 10


def clean_text(text: str) -> str:
    # Normalize unicode
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")

    # Trim
    text = text.strip()

    # Encoding correction
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")

    # Remove characters
    text = text.replace("\n", " ").replace("\r", " ")

    return text


def populate_embeddings():
    db = SessionLocal()

    try:
        research_product_to_embed = (
            db.query(models.ResearchProduct)
            .filter(models.ResearchProduct.embedding.is_(None))
            .all()
        )

        theses_to_embed = (
            db.query(models.Thesis).filter(models.Thesis.embedding.is_(None)).all()
        )

        # Process batch
        for i in range(0, len(research_product_to_embed), BATCH_SIZE):
            batch_objects = research_product_to_embed[i : i + BATCH_SIZE]
            batch_titles = [p.title for p in batch_objects if p.title]

            if not batch_titles:
                continue

            print(
                f"  Generando embeddings para el lote de productos {i//BATCH_SIZE + 1} de {len(batch_titles)}..."
            )

            # Before sending to Dashscope, preprocess the title (clean text)
            batch_titles = [clean_text(title) for title in batch_titles]

            try:
                resp = dashscope.TextEmbedding.call(
                    model=dashscope.TextEmbedding.Models.text_embedding_v4,
                    input=batch_titles,
                    text_type="document",
                    dimension=1024,
                )

                if resp.status_code == HTTPStatus.OK:
                    for product, embedding_data in zip(
                        batch_objects, resp.output["embeddings"]
                    ):
                        product.embedding = embedding_data["embedding"]
                else:
                    print(
                        f"Error generating embeddings for research products batch starting at index {i}: {resp.text}"
                    )

                sleep(1)
            except Exception as e:
                print(
                    f"Exception during embedding generation for research products batch starting at index {i}: {e}"
                )
                sleep(5)

        for i in range(0, len(theses_to_embed), BATCH_SIZE):
            batch_objects = theses_to_embed[i : i + BATCH_SIZE]
            batch_titles = [t.title for t in batch_objects if t.title]

            if not batch_titles:
                continue

            # Before sending to Dashscope, preprocess the title (clean text)
            batch_titles = [clean_text(title) for title in batch_titles]

            print(
                f"  Generando embeddings para el lote de productos {i//BATCH_SIZE + 1} de {len(batch_titles)}..."
            )

            try:
                resp = dashscope.TextEmbedding.call(
                    model=dashscope.TextEmbedding.Models.text_embedding_v4,
                    input=batch_titles,
                    text_type="document",
                    dimension=1024,
                )

                if resp.status_code == HTTPStatus.OK:
                    for thesis, embedding_data in zip(
                        batch_objects, resp.output["embeddings"]
                    ):
                        thesis.embedding = embedding_data["embedding"]
                else:
                    print(
                        f"Error generating embeddings for theses batch starting at index {i}: {resp.text}"
                    )

                sleep(1)
            except Exception as e:
                print(
                    f"Exception during embedding generation for theses batch starting at index {i}: {e}"
                )
                sleep(5)

        print("\nSaving embeddings to the database...")
        db.commit()
        print("Embeddings saved successfully.")
    except Exception as e:
        db.rollback()
        print(f"Exception during database commit: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    populate_embeddings()
