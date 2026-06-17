"""
Process monument canvas photographs for gallery-ready web display.
Straightens perspective, corrects lighting, adds uniform white mat, pure white background.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MONUMENT_DIR = ROOT / "images" / "collection-1" / "monument"
ORIGINALS_DIR = MONUMENT_DIR / "originals"
PROCESSED_DIR = MONUMENT_DIR / "processed"

ARTWORKS = {
    "monument-01.jpg": "The Living Circuit",
    "monument-02.jpg": "Mindstream",
    "monument-03.jpg": "The Pattern Oracle",
}

# Target aspect ratio: 24 x 36 in (2:3 portrait)
CANVAS_ASPECT = 2 / 3
MAT_RATIO = 0.055  # white mat as fraction of canvas short edge
OUTPUT_JPEG_QUALITY = 95


def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = order_points(pts.astype(np.float32))
    (tl, tr, br, bl) = rect
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = int(max(width_a, width_b))
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = int(max(height_a, height_b))
    dst = np.array(
        [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, matrix, (max_width, max_height), flags=cv2.INTER_LANCZOS4)


def find_document_corners(image: np.ndarray) -> np.ndarray | None:
    h, w = image.shape[:2]
    scale = 1200 / max(h, w)
    small = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    edged = cv2.Canny(gray, 40, 140)
    edged = cv2.dilate(edged, np.ones((3, 3), np.uint8), iterations=1)
    edged = cv2.erode(edged, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    img_area = small.shape[0] * small.shape[1]

    for contour in contours[:30]:
        area = cv2.contourArea(contour)
        if area < img_area * 0.15:
            continue
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) == 4:
            return (approx.reshape(4, 2) / scale).astype(np.float32)
    return None


def find_corners_by_artwork_mask(image: np.ndarray) -> np.ndarray | None:
    """Fallback: detect framed artwork via color mask (white mat + painted canvas)."""
    h, w = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    # Painted regions: burgundy / maroon / navy
    red1 = cv2.inRange(hsv, np.array([0, 35, 25]), np.array([18, 255, 210]))
    red2 = cv2.inRange(hsv, np.array([165, 35, 25]), np.array([180, 255, 210]))
    navy = cv2.inRange(hsv, np.array([85, 25, 15]), np.array([140, 255, 140]))
    painted = red1 | red2 | navy

    # White mat / line art
    white = cv2.inRange(lab, np.array([180, 120, 120]), np.array([255, 140, 140]))

    artwork = painted | white
    artwork = cv2.morphologyEx(artwork, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8), iterations=2)
    artwork = cv2.morphologyEx(artwork, cv2.MORPH_OPEN, np.ones([7, 7], np.uint8), iterations=1)

    contours, _ = cv2.findContours(artwork, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < h * w * 0.1:
        return None

    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    return order_points(box.astype(np.float32))


def straighten(image: np.ndarray) -> np.ndarray:
    corners = find_document_corners(image)
    if corners is None:
        corners = find_corners_by_artwork_mask(image)
    if corners is None:
        raise RuntimeError("Could not detect canvas corners")

    warped = four_point_transform(image, corners)

    # Fine rotation straighten using painted-area principal axis
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=120, minLineLength=200, maxLineGap=20)
    if lines is not None and len(lines) > 0:
        angles = []
        for line in lines[:40]:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Normalize to near-vertical edges
            if abs(angle) < 45:
                angle += 90
            angles.append(angle)
        if angles:
            median_angle = np.median(angles)
            if abs(median_angle) < 3:
                h, w = warped.shape[:2]
                center = (w // 2, h // 2)
                matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                warped = cv2.warpAffine(
                    warped,
                    matrix,
                    (w, h),
                    flags=cv2.INTER_LANCZOS4,
                    borderMode=cv2.BORDER_REPLICATE,
                )
    return warped


def painted_area_mask(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    red1 = cv2.inRange(hsv, np.array([0, 25, 18]), np.array([22, 255, 230]))
    red2 = cv2.inRange(hsv, np.array([155, 25, 18]), np.array([180, 255, 230]))
    navy = cv2.inRange(hsv, np.array([75, 18, 8]), np.array([150, 255, 170]))
    mask = red1 | red2 | navy
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8), iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8), iterations=1)
    return mask


def artifact_mask(image: np.ndarray) -> np.ndarray:
    """Pixels that are floor, wall, shadow, or photo background — not artwork."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    dark_neutral = ((v < 85) & (s < 70)).astype(np.uint8) * 255
    mid_gray = ((v > 85) & (v < 140) & (s < 35)).astype(np.uint8) * 255
    return dark_neutral | mid_gray


def trim_edge_artifacts(image: np.ndarray) -> np.ndarray:
    """Remove leftover floor, shadow, or background strips along edges."""
    painted = painted_area_mask(image)
    artifacts = artifact_mask(image)

    h, w = image.shape[:2]
    y0, y1 = 0, h
    x0, x1 = 0, w

    def row_score(y: int) -> float:
        row_painted = painted[y].mean() / 255
        row_artifact = artifacts[y].mean() / 255
        return row_painted - row_artifact * 1.2

    def col_score(x: int) -> float:
        col_painted = painted[:, x].mean() / 255
        col_artifact = artifacts[:, x].mean() / 255
        return col_painted - col_artifact * 1.2

    while y0 < y1 - 50 and row_score(y0) < 0.08:
        y0 += 1
    while y1 > y0 + 50 and row_score(y1 - 1) < 0.08:
        y1 -= 1
    while x0 < x1 - 50 and col_score(x0) < 0.08:
        x0 += 1
    while x1 > x0 + 50 and col_score(x1 - 1) < 0.08:
        x1 -= 1

    return image[y0:y1, x0:x1]


def crop_to_painted_canvas(image: np.ndarray) -> np.ndarray:
    mask = painted_area_mask(image)
    coords = cv2.findNonZero(mask)
    if coords is None:
        return image
    x, y, bw, bh = cv2.boundingRect(coords)
    pad = int(min(bw, bh) * 0.004)
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(image.shape[1], x + bw + pad)
    y2 = min(image.shape[0], y + bh + pad)
    cropped = image[y1:y2, x1:x2]
    return trim_edge_artifacts(cropped)


def correct_lighting(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
    l_corrected = clahe.apply(l_channel)

    # Gentle shadow lift on darker regions while preserving deep burgundy
    l_float = l_corrected.astype(np.float32)
    shadow_mask = (l_float < 95).astype(np.float32)
    shadow_mask = cv2.GaussianBlur(shadow_mask, (0, 0), 25)
    lift = shadow_mask * 12
    l_float = np.clip(l_float + lift, 0, 255)
    l_corrected = l_float.astype(np.uint8)

    merged = cv2.merge([l_corrected, a_channel, b_channel])
    result = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    # Subtle unsharp mask on luminance only
    blurred = cv2.GaussianBlur(result, (0, 0), 1.2)
    result = cv2.addWeighted(result, 1.25, blurred, -0.25, 0)
    return result


def resize_to_canvas_aspect(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    current_aspect = w / h
    if abs(current_aspect - CANVAS_ASPECT) < 0.01:
        return image

    if current_aspect > CANVAS_ASPECT:
        # Too wide — crop width
        new_w = int(h * CANVAS_ASPECT)
        x0 = (w - new_w) // 2
        return image[:, x0 : x0 + new_w]
    # Too tall — crop height
    new_h = int(w / CANVAS_ASPECT)
    y0 = (h - new_h) // 2
    return image[y0 : y0 + new_h, :]


def add_uniform_mat(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    mat_px = max(32, int(min(w, h) * MAT_RATIO))
    bordered = cv2.copyMakeBorder(
        image,
        mat_px,
        mat_px,
        mat_px,
        mat_px,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )
    return bordered


def enforce_pure_white_background(image: np.ndarray) -> np.ndarray:
    """Snap near-white border pixels to pure #FFFFFF."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0]
    near_white = l_channel > 238
    result = image.copy()
    result[near_white] = (255, 255, 255)
    return result


def process_image(src_path: Path, dst_path: Path) -> None:
    image = cv2.imread(str(src_path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Failed to read {src_path}")

    straight = straighten(image)
    canvas = crop_to_painted_canvas(straight)
    canvas = resize_to_canvas_aspect(canvas)
    enhanced = correct_lighting(canvas)
    final = add_uniform_mat(enhanced)
    final = enforce_pure_white_background(final)

    # Save via Pillow for high-quality JPEG
    rgb = cv2.cvtColor(final, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    pil_img.save(dst_path, format="JPEG", quality=OUTPUT_JPEG_QUALITY, optimize=True, subsampling=0)
    print(f"  -> {dst_path.name}  ({final.shape[1]}x{final.shape[0]})")


def main() -> None:
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for filename, title in ARTWORKS.items():
        src = MONUMENT_DIR / filename
        if not src.exists():
            raise FileNotFoundError(src)

        original_backup = ORIGINALS_DIR / filename
        if not original_backup.exists():
            shutil.copy2(src, original_backup)
            print(f"Backed up original: {original_backup}")

        print(f"Processing: {title} ({filename})")
        processed_path = PROCESSED_DIR / filename
        process_image(original_backup if original_backup.exists() else src, processed_path)

        # Update gallery file in place
        shutil.copy2(processed_path, MONUMENT_DIR / filename)

    print("\nDone. Originals in originals/, processed copies in processed/.")


if __name__ == "__main__":
    main()