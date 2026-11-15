"""OCR engine wrappers. All model names / inference settings live here so the
configuration that produced any prediction file is documented in one place
(see docs/ocr_models.md)."""
import os

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

PADDLE_DET_MODEL = "PP-OCRv6_medium_det"
PADDLE_REC_MODEL = "PP-OCRv6_medium_rec"
PADDLE_LAYOUT_MODEL = "PP-DocLayout-L"


def paddle_ocr(orientation: bool, rec_model_dir: str | None = None):
    """Pretrained PaddleOCR pipeline (detection + recognition), CPU inference.

    `orientation=True` adds the whole-page 0/90/180/270 classifier, used on full
    pages because several scans are upside-down or sideways. Crops are already
    upright, so it is off for them. `rec_model_dir` swaps in a fine-tuned
    recognition model exported by finetune/run_finetune.sh.
    """
    from paddleocr import PaddleOCR
    return PaddleOCR(
        text_detection_model_name=PADDLE_DET_MODEL,
        text_recognition_model_name=PADDLE_REC_MODEL,
        text_recognition_model_dir=rec_model_dir,
        use_doc_orientation_classify=orientation,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device="cpu",
    )


def paddle_layout():
    from paddleocr import LayoutDetection
    return LayoutDetection(model_name=PADDLE_LAYOUT_MODEL, device="cpu")


def reading_order(lines: list[dict]) -> list[dict]:
    """Sort detected lines top-to-bottom, merging fragments on the same row."""
    lines = sorted(lines, key=lambda l: (l["box"][1] + l["box"][3]) / 2)
    rows: list[list[dict]] = []
    for ln in lines:
        cy = (ln["box"][1] + ln["box"][3]) / 2
        h = ln["box"][3] - ln["box"][1]
        if rows:
            last = rows[-1][-1]
            lcy = (last["box"][1] + last["box"][3]) / 2
            if abs(cy - lcy) < 0.5 * min(h, last["box"][3] - last["box"][1]):
                rows[-1].append(ln)
                continue
        rows.append([ln])
    return [sorted(r, key=lambda l: l["box"][0]) for r in rows]


def paddle_lines(result) -> list[dict]:
    return [dict(box=[int(v) for v in box], text=text, score=round(float(score), 4))
            for text, score, box in zip(result["rec_texts"], result["rec_scores"], result["rec_boxes"])]
