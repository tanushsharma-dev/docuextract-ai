import os
import cv2
import numpy as np
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path

def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 200) -> list:
    """Convert PDF pages to PNG images."""
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []

    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        output_path = os.path.join(output_dir, f"page_{page_num+1}.png")
        pix.save(output_path)
        image_paths.append(output_path)

    doc.close()
    return image_paths

def enhance_image(image_path: str, output_path: str = None) -> str:
    """Enhance image: denoise, contrast, sharpen."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    # Convert to grayscale for processing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Adaptive threshold for better OCR
    enhanced = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    output_path = output_path or image_path.replace(".png", "_enhanced.png")
    cv2.imwrite(output_path, enhanced)
    return output_path

def deskew_image(image_path: str, output_path: str = None) -> str:
    """Correct skew in scanned document."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Hough lines
    lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)

    if lines is None:
        return image_path

    # Calculate median angle
    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90
        if -45 < angle < 45:
            angles.append(angle)

    if not angles:
        return image_path

    median_angle = np.median(angles)

    # Rotate
    h, w = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)

    output_path = output_path or image_path.replace(".png", "_deskewed.png")
    cv2.imwrite(output_path, rotated)
    return output_path

def detect_document_quality(image_path: str) -> dict:
    """Detect image quality metrics."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {"quality": "unknown"}

    # Blur detection (Laplacian variance)
    blur_score = cv2.Laplacian(img, cv2.CV_64F).var()

    # Brightness
    brightness = np.mean(img)

    quality = "good"
    if blur_score < 100:
        quality = "blurry"
    elif brightness < 60 or brightness > 220:
        quality = "poor_lighting"

    return {
        "quality": quality,
        "blur_score": float(blur_score),
        "brightness": float(brightness)
    }

def preprocess_document(file_path: str, output_dir: str) -> list:
    """Full preprocessing pipeline."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Check if PDF
    if file_path.lower().endswith(".pdf"):
        image_paths = pdf_to_images(file_path, output_dir)
    else:
        # Single image
        output_path = os.path.join(output_dir, "page_1.png")
        img = Image.open(file_path)
        img.save(output_path)
        image_paths = [output_path]

    # Enhance each page
    enhanced_paths = []
    for path in image_paths:
        enhanced = enhance_image(path)
        deskewed = deskew_image(enhanced)
        enhanced_paths.append(deskewed)

    return enhanced_paths