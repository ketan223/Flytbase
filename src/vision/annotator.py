"""
Tactical Frame Annotator.
Draws visual bounding boxes, HUD telemetry overlays, and security alert indicators
onto video frames for display in the security dashboard or exported patrol videos.
"""

import os
from PIL import Image, ImageDraw
from ..telemetry.models import FrameAnalysis, SecurityAlert


class FrameAnnotator:
    """Renders tactical security annotations and alert banners on frames."""

    @staticmethod
    def annotate(frame: FrameAnalysis, alert: SecurityAlert = None, save_path: str = None) -> Image.Image:
        """Draw bounding boxes, tags, and alert banners onto the frame image."""
        img = Image.open(frame.image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        w, h = img.size

        # If there is an active alert on this frame, draw high-visibility alert banner at the top
        if alert or frame.is_alert:
            banner_height = 42
            # Semi-transparent/solid red warning banner
            draw.rectangle([0, 0, w, banner_height], fill=(220, 30, 30))
            alert_text = f"SECURITY ALERT: {alert.description if alert else 'ANOMALY DETECTED'}"
            draw.text((20, 12), alert_text, fill=(255, 255, 255))
            if alert:
                rule_text = f"RULE: {alert.rule_name} | SEVERITY: {alert.severity.value}"
                draw.text((w - 380, 12), rule_text, fill=(255, 255, 255))

        # Re-verify and emphasize object bounding boxes if needed
        for obj in frame.detected_objects:
            if obj.bbox:
                ymin, xmin, ymax, xmax = obj.bbox
                box_color = (255, 60, 60) if (alert or frame.is_alert) else (0, 255, 136)
                draw.rectangle([xmin, ymin, xmax, ymax], outline=box_color, width=3)

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            img.save(save_path)

        return img
