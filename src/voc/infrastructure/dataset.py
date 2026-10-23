"""Aquisição oficial e preparação auditável, sem multiplicar avaliações nas junções."""

import hashlib
import html
import re
import shutil
import unicodedata
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests

from voc.infrastructure.storage import digest, write_json

SOURCE = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce"
FILES = (
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
)


def download(root: Path, source_zip: Path | None = None) -> None:
    raw = root / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw / "olist.zip"
    if not archive.exists():
        if source_zip:
            shutil.copyfile(source_zip, archive)
        else:
            partial = archive.with_suffix(".partial")
            with requests.get(SOURCE, stream=True, timeout=(20, 180)) as response:
                response.raise_for_status()
                with partial.open("wb") as stream:
                    for chunk in response.iter_content(1024 * 1024):
                        stream.write(chunk)
            partial.rename(archive)
    with ZipFile(archive) as bundle:
        for name in FILES:
            # Nomes fixos; não se utiliza extractall ou caminhos fornecidos pelo ZIP.
            payload = bundle.read(name)
            target = raw / name
            if target.exists() and target.read_bytes() != payload:
                raise ValueError(f"Entrada local divergente, preservada: {name}")
            target.write_bytes(payload)
    write_json(
        root / "reports/source_manifest.json",
        {
            "url": SOURCE,
            "license": "CC BY-NC-SA 4.0",
            "archive_sha256": digest(archive),
            "files": {name: digest(raw / name) for name in FILES},
        },
    )


def clean_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", "[EMAIL]", value)
    value = re.sub(r"https?://\S+", "[LINK]", value)
    value = re.sub(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)", "[CPF]", value)
    value = re.sub(
        r"(?<!\d)(?:\+55\s*)?\(?\d{2}\)?\s*9?\d{4}[- .]?\d{4}(?!\d)", "[TELEFONE]", value
    )
    return re.sub(r"\s+", " ", value).strip()


def prepare(root: Path) -> dict[str, object]:
    raw = root / "data/raw"
    reviews = pd.read_csv(raw / FILES[0], dtype={"review_id": "string", "order_id": "string"})
    required = {
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
    }
    if not required <= set(reviews):
        raise ValueError("CSV de avaliações sem as colunas obrigatórias.")
    initial = len(reviews)
    reviews = reviews.drop_duplicates().copy()
    duplicate_rows = initial - len(reviews)
    reviews["title"] = reviews.review_comment_title.map(clean_text)
    reviews["message"] = reviews.review_comment_message.map(clean_text)
    reviews["text"] = (reviews.title + ". " + reviews.message).str.strip(" .")
    empty = ~reviews.text.str.contains(r"[^\W\d_]", regex=True)
    missing_ids = reviews.review_id.isna() | reviews.order_id.isna()
    invalid_score = ~reviews.review_score.isin([1, 2, 3, 4, 5])
    rejected = empty | missing_ids | invalid_score
    quality = {
        "source_rows": initial,
        "exact_duplicates_removed": duplicate_rows,
        "empty_text_rows": int(empty.sum()),
        "missing_id_rows": int(missing_ids.sum()),
        "invalid_score_rows": int(invalid_score.sum()),
        "excluded_rows_union": int(rejected.sum()),
    }
    reviews = reviews.loc[~rejected].copy()
    reviews["score"] = reviews.review_score.astype(int)
    reviews["date"] = (
        pd.to_datetime(reviews.review_creation_date, errors="coerce")
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )
    orders = pd.read_csv(raw / FILES[1])
    orders["purchase_date"] = (
        pd.to_datetime(orders.order_purchase_timestamp, errors="coerce")
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )
    delivered = pd.to_datetime(orders.order_delivered_customer_date, errors="coerce")
    expected = pd.to_datetime(orders.order_estimated_delivery_date, errors="coerce")
    # Comparação por dia civil; estimativa da Olist não inclui horário de entrega.
    orders["late"] = (delivered.dt.normalize() > expected.dt.normalize()).astype("boolean")
    orders.loc[delivered.isna() | expected.isna(), "late"] = pd.NA
    items = pd.read_csv(raw / FILES[2], usecols=["order_id", "product_id"])
    products = pd.read_csv(raw / FILES[3], usecols=["product_id", "product_category_name"])
    items = items.merge(products, on="product_id", how="left", validate="many_to_one")
    categories = (
        items.groupby("order_id")
        .product_category_name.agg(lambda values: "|".join(sorted(set(values.dropna()))))
        .rename("categories")
    )
    reviews = reviews.merge(
        orders[["order_id", "purchase_date", "late"]],
        on="order_id",
        how="left",
        validate="many_to_one",
    )
    reviews = reviews.merge(categories, on="order_id", how="left", validate="many_to_one")
    reviews["categories"] = reviews.categories.fillna("")
    reviews["purchase_date"] = reviews.purchase_date.fillna("")
    reviews["document_id"] = [
        hashlib.sha256("\x1f".join(str(value) for value in row).encode()).hexdigest()[:24]
        for row in reviews[["review_id", "order_id", "score", "date", "text"]].itertuples(
            index=False, name=None
        )
    ]
    repeated_docs = int(reviews.document_id.duplicated().sum())
    reviews = (
        reviews.drop_duplicates("document_id").sort_values("document_id").reset_index(drop=True)
    )
    columns = [
        "document_id",
        "review_id",
        "order_id",
        "text",
        "score",
        "date",
        "purchase_date",
        "categories",
        "late",
    ]
    processed = root / "data/processed/reviews.parquet"
    processed.parent.mkdir(parents=True, exist_ok=True)
    reviews[columns].to_parquet(processed, index=False)
    quality.update(
        {
            "same_document_rows_collapsed": repeated_docs,
            "documents": len(reviews),
            "unique_review_ids": reviews.review_id.nunique(),
            "unique_orders": reviews.order_id.nunique(),
            "score_counts": {
                str(k): int(v) for k, v in reviews.score.value_counts().sort_index().items()
            },
            "missing_review_dates": int(reviews.date.eq("").sum()),
            "missing_delivery_status": int(reviews.late.isna().sum()),
            "missing_categories": int(reviews.categories.eq("").sum()),
            "min_date": reviews.loc[reviews.date.ne(""), "date"].min(),
            "max_date": reviews.date.max(),
            "processed_sha256": digest(processed),
            "source_sha256": {name: digest(raw / name) for name in FILES},
        }
    )
    write_json(root / "reports/data_quality.json", quality)
    return quality
