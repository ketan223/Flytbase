"""
Synthetic Drone Flight & Visual Frame Generator for FlytBase Security Prototype.
Generates realistic drone camera frames with HUD telemetry overlays, environmental lighting,
and synchronized telemetry streams covering daytime and nighttime patrols.
"""

import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def draw_hud(draw: ImageDraw.ImageDraw, width: int, height: int, telemetry: dict, is_night: bool):
    """Render a tactical drone HUD overlay onto the frame."""
    hud_color = (0, 255, 136) if not is_night else (0, 230, 255)
    alert_color = (255, 60, 60)
    
    # Corner brackets (Gimbal reticle)
    reticle_len = 30
    pad = 20
    draw.line([(pad, pad), (pad + reticle_len, pad)], fill=hud_color, width=2)
    draw.line([(pad, pad), (pad, pad + reticle_len)], fill=hud_color, width=2)
    
    draw.line([(width - pad, pad), (width - pad - reticle_len, pad)], fill=hud_color, width=2)
    draw.line([(width - pad, pad), (width - pad, pad + reticle_len)], fill=hud_color, width=2)
    
    draw.line([(pad, height - pad), (pad + reticle_len, height - pad)], fill=hud_color, width=2)
    draw.line([(pad, height - pad), (pad, height - pad - reticle_len)], fill=hud_color, width=2)
    
    draw.line([(width - pad, height - pad), (width - pad - reticle_len, height - pad)], fill=hud_color, width=2)
    draw.line([(width - pad, height - pad), (width - pad, height - pad - reticle_len)], fill=hud_color, width=2)

    # Top Bar: Telemetry Info
    time_str = telemetry["timestamp"]
    zone_str = f"ZONE: {telemetry['zone_name'].upper()}"
    status_str = "SYS: AUTONOMOUS DIAZ PATROL [AI ONLINE]"
    
    draw.text((pad + 10, pad + 5), f"{time_str} | {zone_str}", fill=hud_color)
    draw.text((width - 320, pad + 5), status_str, fill=hud_color)

    # Crosshair in center
    cx, cy = width // 2, height // 2
    ch_size = 15
    draw.line([(cx - ch_size, cy), (cx + ch_size, cy)], fill=hud_color, width=1)
    draw.line([(cx, cy - ch_size), (cx, cy + ch_size)], fill=hud_color, width=1)

    # Bottom HUD: Altitude, Battery, Speed, Coordinates
    telemetry_line1 = (
        f"ALT: {telemetry['altitude_m']:.1f}m  |  "
        f"BAT: {telemetry['battery_pct']:.0f}%  |  "
        f"SPD: {telemetry.get('speed_mps', 0.0):.1f}m/s  |  "
        f"HDG: {telemetry.get('heading_deg', 0):03.0f}°"
    )
    coords_line = f"GPS: {telemetry['latitude']:.6f} N, {telemetry['longitude']:.6f} W"
    
    draw.text((pad + 10, height - pad - 35), telemetry_line1, fill=hud_color)
    draw.text((pad + 10, height - pad - 18), coords_line, fill=hud_color)


def create_simulated_frame(
    output_path: str,
    scene_type: str,
    telemetry: dict,
    objects: list,
    is_night: bool = False
):
    """Create a realistic synthesized drone surveillance camera frame."""
    width, height = 800, 500
    
    # Background tone: Daytime daylight or Night-time IR/low-light
    if is_night:
        base_color = (20, 25, 30)
        ground_color = (30, 35, 40)
        structure_color = (50, 55, 60)
    else:
        base_color = (135, 175, 210)  # sky/ambient
        ground_color = (95, 100, 105) # asphalt / paved lot
        structure_color = (180, 185, 190)

    image = Image.new("RGB", (width, height), color=base_color)
    draw = ImageDraw.Draw(image)

    # Horizon and ground
    horizon_y = int(height * 0.35)
    draw.rectangle([0, horizon_y, width, height], fill=ground_color)

    # Road / Perimeter layout
    draw.polygon([(width * 0.25, height), (width * 0.40, horizon_y), (width * 0.60, horizon_y), (width * 0.75, height)], fill=(45, 48, 52) if not is_night else (18, 20, 22))
    # Lane divider
    draw.line([(width * 0.5, horizon_y), (width * 0.5, height)], fill=(200, 180, 50) if not is_night else (90, 85, 40), width=2)

    # Scene specific landmarks
    if "gate" in scene_type.lower():
        # Security Guardhouse / Gate Barrier
        draw.rectangle([50, horizon_y - 40, 180, horizon_y + 80], fill=structure_color, outline=(20, 20, 20))
        # Gate barrier arm
        draw.line([180, horizon_y + 50, 350, horizon_y + 50], fill=(220, 30, 30), width=4)
    elif "garage" in scene_type.lower() or "parking" in scene_type.lower():
        # Executive Garage Structure
        draw.rectangle([40, horizon_y - 60, 320, horizon_y + 60], fill=structure_color, outline=(20, 20, 20))
        for bay_x in [60, 150, 240]:
            draw.rectangle([bay_x, horizon_y - 10, bay_x + 60, horizon_y + 60], fill=(30, 30, 30))
    elif "warehouse" in scene_type.lower() or "fence" in scene_type.lower():
        # Industrial Perimeter Fence
        fence_y = horizon_y + 20
        draw.line([0, fence_y, width, fence_y], fill=(150, 150, 150), width=2)
        for fx in range(0, width, 40):
            draw.line([fx, fence_y - 30, fx, fence_y + 40], fill=(120, 120, 120), width=2)

    # Render Objects & Bounding Boxes
    for obj in objects:
        bbox = obj.get("bbox", [150, 200, 300, 350]) # ymin, xmin, ymax, xmax
        ymin, xmin, ymax, xmax = bbox
        label = obj.get("label", "object")
        desc = obj.get("description", label)

        if label == "vehicle":
            # Draw realistic vehicle chassis
            v_color = (25, 80, 190) if "blue" in desc.lower() else (180, 180, 180)
            draw.rectangle([xmin, ymin, xmax, ymax], fill=v_color, outline=(255, 255, 255), width=2)
            # Cab / windows
            cab_margin = 15
            draw.rectangle([xmin + cab_margin, ymin + 10, xmax - cab_margin, ymin + (ymax - ymin)//2], fill=(20, 25, 30), outline=(200, 200, 200))
            # Wheels
            draw.ellipse([xmin + 10, ymax - 15, xmin + 35, ymax + 10], fill=(10, 10, 10))
            draw.ellipse([xmax - 35, ymax - 15, xmax - 10, ymax + 10], fill=(10, 10, 10))
        elif label == "person":
            # Draw human figure
            p_color = (40, 40, 45) if is_night else (50, 70, 120)
            head_r = 10
            cx = (xmin + xmax) // 2
            # Head
            draw.ellipse([cx - head_r, ymin, cx + head_r, ymin + 20], fill=(220, 190, 160))
            # Torso
            draw.rectangle([xmin + 5, ymin + 20, xmax - 5, ymax - 25], fill=p_color)
            # Legs
            draw.line([xmin + 10, ymax - 25, xmin + 8, ymax], fill=p_color, width=4)
            draw.line([xmax - 10, ymax - 25, xmax - 8, ymax], fill=p_color, width=4)

        # Tactical detection box with label tag
        tag_color = (0, 255, 136) if not is_night else (255, 180, 0)
        draw.rectangle([xmin - 2, ymin - 2, xmax + 2, ymax + 2], outline=tag_color, width=2)
        draw.rectangle([xmin - 2, ymin - 22, xmin + 180, ymin - 2], fill=(10, 15, 20))
        draw.text((xmin + 2, ymin - 19), f"{desc} [{obj.get('confidence', 0.95):.2f}]", fill=tag_color)

    # Render HUD overlay on top of frame
    draw_hud(draw, width, height, telemetry, is_night)

    # Ensure output dir exists and save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)


def generate_all_sample_data():
    """Generate both Day Patrol (12:00) and Night Patrol (00:01) missions."""
    base_dir = "data"
    frames_dir = os.path.join(base_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    missions_data = []

    # =========================================================================
    # Mission 1: DAYTIME ROUTINE PERIMETER PATROL (12:00 PM)
    # Highlights: Blue Ford F150 enters property and is logged at garage.
    # =========================================================================
    day_frames = [
        {
            "frame_id": "FRAME_001",
            "mission_id": "PATROL_DAY_1200",
            "timestamp": "2026-09-30 12:00:00",
            "scene_type": "Main Gate Entrance",
            "telemetry": {
                "timestamp": "2026-09-30 12:00:00",
                "latitude": 37.774929,
                "longitude": -122.419416,
                "altitude_m": 16.5,
                "battery_pct": 98.0,
                "speed_mps": 4.2,
                "heading_deg": 45.0,
                "zone_id": "ZONE_GATE",
                "zone_name": "Main Gate",
                "mission_id": "PATROL_DAY_1200"
            },
            "objects": [
                {
                    "object_id": "VEH_001",
                    "label": "vehicle",
                    "description": "Blue Ford F150",
                    "attributes": {"color": "blue", "make": "Ford", "model": "F150", "type": "pickup_truck"},
                    "confidence": 0.97,
                    "bbox": [220, 260, 360, 480]
                }
            ],
            "caption": "A blue Ford F150 pickup truck approaching the Main Gate entrance barrier at 12:00.",
            "activity_summary": "Authorized commercial entry during operational hours.",
            "is_night": False
        },
        {
            "frame_id": "FRAME_002",
            "mission_id": "PATROL_DAY_1200",
            "timestamp": "2026-09-30 12:00:45",
            "scene_type": "Executive Garage",
            "telemetry": {
                "timestamp": "2026-09-30 12:00:45",
                "latitude": 37.775310,
                "longitude": -122.418850,
                "altitude_m": 18.0,
                "battery_pct": 96.0,
                "speed_mps": 2.1,
                "heading_deg": 90.0,
                "zone_id": "ZONE_GARAGE",
                "zone_name": "Executive Garage",
                "mission_id": "PATROL_DAY_1200"
            },
            "objects": [
                {
                    "object_id": "VEH_001",
                    "label": "vehicle",
                    "description": "Blue Ford F150",
                    "attributes": {"color": "blue", "make": "Ford", "model": "F150", "type": "pickup_truck"},
                    "confidence": 0.98,
                    "bbox": [210, 320, 350, 540]
                }
            ],
            "caption": "Blue Ford F150 spotted at garage, 12:00.",
            "activity_summary": "Vehicle maneuvering into assigned parking bay outside executive garage.",
            "is_night": False
        },
        {
            "frame_id": "FRAME_003",
            "mission_id": "PATROL_DAY_1200",
            "timestamp": "2026-09-30 12:01:30",
            "scene_type": "Warehouse Loading Bay",
            "telemetry": {
                "timestamp": "2026-09-30 12:01:30",
                "latitude": 37.776100,
                "longitude": -122.417900,
                "altitude_m": 22.0,
                "battery_pct": 94.0,
                "speed_mps": 5.0,
                "heading_deg": 135.0,
                "zone_id": "ZONE_WAREHOUSE",
                "zone_name": "Warehouse Loading Bay",
                "mission_id": "PATROL_DAY_1200"
            },
            "objects": [
                {
                    "object_id": "VEH_002",
                    "label": "vehicle",
                    "description": "White Delivery Box Truck",
                    "attributes": {"color": "white", "type": "delivery_truck"},
                    "confidence": 0.94,
                    "bbox": [200, 240, 370, 510]
                }
            ],
            "caption": "White commercial delivery truck staged at Warehouse Loading Bay 3.",
            "activity_summary": "Standard logistics operations at warehouse bay.",
            "is_night": False
        }
    ]

    # =========================================================================
    # Mission 2: NIGHT CURFEW SECURITY PATROL (00:01 AM)
    # Highlights:
    # 1. Person loitering at main gate at midnight (triggers LOITERING alert).
    # 2. Blue Ford F150 returns at night (triggers RECURRENCE & CURFEW alert).
    # =========================================================================
    night_frames = [
        {
            "frame_id": "FRAME_004",
            "mission_id": "PATROL_NIGHT_0001",
            "timestamp": "2026-09-30 00:00:50",
            "scene_type": "Perimeter Fence East",
            "telemetry": {
                "timestamp": "2026-09-30 00:00:50",
                "latitude": 37.774500,
                "longitude": -122.420100,
                "altitude_m": 15.0,
                "battery_pct": 100.0,
                "speed_mps": 3.8,
                "heading_deg": 180.0,
                "zone_id": "ZONE_FENCE_EAST",
                "zone_name": "Perimeter Fence East",
                "mission_id": "PATROL_NIGHT_0001"
            },
            "objects": [],
            "caption": "Night infrared scan of Perimeter Fence East. Boundary is intact and clear.",
            "activity_summary": "No security anomalies detected.",
            "is_night": True
        },
        {
            "frame_id": "FRAME_005",
            "mission_id": "PATROL_NIGHT_0001",
            "timestamp": "2026-09-30 00:01:00",
            "scene_type": "Main Gate Entrance",
            "telemetry": {
                "timestamp": "2026-09-30 00:01:00",
                "latitude": 37.774929,
                "longitude": -122.419416,
                "altitude_m": 14.0,
                "battery_pct": 98.0,
                "speed_mps": 1.2,
                "heading_deg": 270.0,
                "zone_id": "ZONE_GATE",
                "zone_name": "Main Gate",
                "mission_id": "PATROL_NIGHT_0001"
            },
            "objects": [
                {
                    "object_id": "PER_001",
                    "label": "person",
                    "description": "Individual in dark hoodie",
                    "attributes": {"clothing": "dark hoodie", "posture": "standing stationary", "action": "loitering"},
                    "confidence": 0.96,
                    "bbox": [230, 360, 370, 420]
                }
            ],
            "caption": "Person loitering at main gate, 00:01.",
            "activity_summary": "Unidentified individual observed standing stationary outside gate after curfew.",
            "is_night": True
        },
        {
            "frame_id": "FRAME_006",
            "mission_id": "PATROL_NIGHT_0001",
            "timestamp": "2026-09-30 00:01:30",
            "scene_type": "Main Gate Entrance",
            "telemetry": {
                "timestamp": "2026-09-30 00:01:30",
                "latitude": 37.774932,
                "longitude": -122.419418,
                "altitude_m": 12.5,
                "battery_pct": 97.0,
                "speed_mps": 0.3,
                "heading_deg": 270.0,
                "zone_id": "ZONE_GATE",
                "zone_name": "Main Gate",
                "mission_id": "PATROL_NIGHT_0001"
            },
            "objects": [
                {
                    "object_id": "PER_001",
                    "label": "person",
                    "description": "Individual in dark hoodie",
                    "attributes": {"clothing": "dark hoodie", "posture": "pacing", "action": "loitering"},
                    "confidence": 0.97,
                    "bbox": [235, 370, 375, 430]
                }
            ],
            "caption": "Person loitering at main gate, 00:01. Continuous dwell time exceeded 30 seconds.",
            "activity_summary": "Sustained unauthorized loitering at access control gate.",
            "is_night": True
        },
        {
            "frame_id": "FRAME_007",
            "mission_id": "PATROL_NIGHT_0001",
            "timestamp": "2026-09-30 00:02:15",
            "scene_type": "Warehouse Loading Bay",
            "telemetry": {
                "timestamp": "2026-09-30 00:02:15",
                "latitude": 37.776105,
                "longitude": -122.417895,
                "altitude_m": 15.0,
                "battery_pct": 95.0,
                "speed_mps": 3.0,
                "heading_deg": 45.0,
                "zone_id": "ZONE_WAREHOUSE",
                "zone_name": "Warehouse Loading Bay",
                "mission_id": "PATROL_NIGHT_0001"
            },
            "objects": [
                {
                    "object_id": "VEH_001",
                    "label": "vehicle",
                    "description": "Blue Ford F150",
                    "attributes": {"color": "blue", "make": "Ford", "model": "F150", "type": "pickup_truck"},
                    "confidence": 0.98,
                    "bbox": [215, 270, 360, 500]
                }
            ],
            "caption": "Blue Ford F150 re-entered property and spotted idling near warehouse fire lane at 00:02.",
            "activity_summary": "Second sighting of vehicle today; unauthorized entry outside business hours.",
            "is_night": True
        }
    ]

    all_frames = day_frames + night_frames

    for frame in all_frames:
        img_name = f"{frame['frame_id']}.png"
        img_path = os.path.join(frames_dir, img_name)
        frame["image_path"] = img_path
        create_simulated_frame(
            output_path=img_path,
            scene_type=frame["scene_type"],
            telemetry=frame["telemetry"],
            objects=frame["objects"],
            is_night=frame["is_night"]
        )

    # Save metadata JSON file for pipeline ingestion
    meta_path = os.path.join(base_dir, "sample_flight_logs.json")
    with open(meta_path, "w") as f:
        json.dump(all_frames, f, indent=2)

    print(f"[OK] Generated {len(all_frames)} synchronized frames & metadata at {frames_dir}")
    print(f"[OK] Flight logs saved to {meta_path}")


if __name__ == "__main__":
    generate_all_sample_data()
