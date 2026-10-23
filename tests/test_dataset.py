from pathlib import Path

import pandas as pd

from voc.infrastructure.dataset import FILES, clean_text, prepare


def test_cleaning_preserves_negative_and_accents_while_masking_contacts() -> None:
    text = clean_text("<b>Não chegou!</b>\nE-mail: pessoa@exemplo.com; (11) 99999-8888")
    assert "Não chegou!" in text
    assert "[EMAIL]" in text and "[TELEFONE]" in text
    assert "pessoa@" not in text


def test_missing_values_are_not_literal_nan() -> None:
    assert clean_text(float("nan")) == ""
    assert clean_text(None) == ""


def test_multi_item_join_keeps_one_document_and_title_only_review(tmp_path: Path) -> None:
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    common = {"review_creation_date": "2018-03-01", "review_score": 1}
    pd.DataFrame(
        [
            {
                **common,
                "review_id": "r1",
                "order_id": "o1",
                "review_comment_title": "Não recebi",
                "review_comment_message": None,
            },
            {
                **common,
                "review_id": "r2",
                "order_id": "o2",
                "review_comment_title": None,
                "review_comment_message": None,
            },
        ]
    ).to_csv(raw / FILES[0], index=False)
    pd.DataFrame(
        [
            {
                "order_id": "o1",
                "order_purchase_timestamp": "2018-02-01",
                "order_delivered_customer_date": None,
                "order_estimated_delivery_date": "2018-02-20",
            },
            {
                "order_id": "o2",
                "order_purchase_timestamp": "2018-02-01",
                "order_delivered_customer_date": "2018-02-20 21:00:00",
                "order_estimated_delivery_date": "2018-02-20 00:00:00",
            },
        ]
    ).to_csv(raw / FILES[1], index=False)
    pd.DataFrame(
        [{"order_id": "o1", "product_id": "p1"}, {"order_id": "o1", "product_id": "p2"}]
    ).to_csv(raw / FILES[2], index=False)
    pd.DataFrame(
        [
            {"product_id": "p1", "product_category_name": "a"},
            {"product_id": "p2", "product_category_name": "b"},
        ]
    ).to_csv(raw / FILES[3], index=False)
    result = prepare(tmp_path)
    docs = pd.read_parquet(tmp_path / "data/processed/reviews.parquet")
    assert result["documents"] == 1
    assert result["empty_text_rows"] == 1
    assert docs.iloc[0].text == "Não recebi"
    assert docs.iloc[0].categories == "a|b"
    assert pd.isna(docs.iloc[0].late)
