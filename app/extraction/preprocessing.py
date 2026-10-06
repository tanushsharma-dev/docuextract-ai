import os
import logging
import time
from typing import List, Tuple

logger = logging.getLogger(__name__)

# ==========================================================
# BALANCED: Good OCR accuracy + Fast processing
# ==========================================================
PDF_DPI = 200        # 300 was too slow, 150 was inaccurate
MAX_WIDTH = 1500     # balanced
MAX_PAGES = 1


def convert_pdf_to_images(pdf_path: str, output_dir: str) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    image_paths: List[str] = []

    try:
        import pypdfium2 as pdfium
        t0 = time.time()
        pdf = pdfium.PdfDocument(pdf_path)
        n_pages = len(pdf)
        pages = min(n_pages, MAX_PAGES)

        for i in range(pages):
            page = pdf[i]
            bitmap = page.render(scale=PDF_DPI / 72.0)
            pil = bitmap.to_pil()
            if pil.width > MAX_WIDTH:
                ratio = MAX_WIDTH / pil.width
                pil = pil.resize((MAX_WIDTH, int(pil.height * ratio)), resample=1)
            out = os.path.join(output_dir, f"page_{i + 1}.png")
            pil.convert("RGB").save(out, format="PNG", optimize=False)
            image_paths.append(out)

        pdf.close()
        logger.info(f"⏱️ PDF convert: {time.time()-t0:.1f}s ({pages}/{n_pages} pages @ {PDF_DPI} DPI)")
        return image_paths

    except ImportError:
        logger.warning("pypdfium2 not installed — using pdf2image")
    except Exception as e:
        logger.warning(f"pypdfium2 failed: {e}")

    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=PDF_DPI, first_page=1, last_page=MAX_PAGES)
        for i, img in enumerate(images):
            if img.width > MAX_WIDTH:
                ratio = MAX_WIDTH / img.width
                img = img.resize((MAX_WIDTH, int(img.height * ratio)))
            out = os.path.join(output_dir, f"page_{i + 1}.png")
            img.convert("RGB").save(out, format="PNG", optimize=False)
            image_paths.append(out)
        return image_paths
    except Exception as e:
        logger.error(f"PDF conversion failed: {e}")
        return []


def preprocess_document(input_path: str, output_dir: str) -> Tuple[str, List[str]]:
    os.makedirs(output_dir, exist_ok=True)
    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".pdf":
        return "pdf", convert_pdf_to_images(input_path, output_dir)
    elif ext in (".png", ".jpg", ".jpeg", ".webp", ".tiff"):
        return "image", [input_path]

    logger.error(f"Unsupported file type: {ext}")
    return "unknown", []


def extract_text_from_image(image_path: str) -> str:
    return ""