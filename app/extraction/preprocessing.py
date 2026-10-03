import os
import logging

import fitz
import PIL.Image

logger = logging.getLogger(__name__)

MAX_DIM = 1568


def is_pdf(path):
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


def _resize(img):
    w, h = img.size
    scale = min(1.0, MAX_DIM / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), PIL.Image.LANCZOS)
    return img


def preprocess_document(file_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    try:
        if is_pdf(file_path):
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=150)
                img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img = _resize(img)
                out = os.path.join(output_dir, f"page_{i + 1}.png")
                img.save(out, "PNG")
                image_paths.append(out)
            doc.close()
            logger.info(f"PDF rendered: {len(image_paths)} page(s)")
        else:
            img = PIL.Image.open(file_path).convert("RGB")
            img = _resize(img)
            out = os.path.join(output_dir, "page_1.png")
            img.save(out, "PNG")
            image_paths.append(out)
            logger.info("Image preprocessed")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
    return image_paths