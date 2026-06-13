"""Fetch relevant images for paper topics."""

import os
import urllib.request
import hashlib

# All URLs verified working (200)
_AI1 = "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1920&h=1080&fit=crop"
_AI2 = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1920&h=1080&fit=crop"
_ROBOT = "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=1920&h=1080&fit=crop"
_CHIP = "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1920&h=1080&fit=crop"
_CODE = "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?w=1920&h=1080&fit=crop"
_BRAIN = "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=1920&h=1080&fit=crop"
_ABSTRACT = "https://images.unsplash.com/photo-1547954575-855750c57bd3?w=1920&h=1080&fit=crop"
_GRADIENT = "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=1920&h=1080&fit=crop"
_PHYSICS = "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1920&h=1080&fit=crop"
_MATH = "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=1920&h=1080&fit=crop"
_LAB = "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=1920&h=1080&fit=crop"
_DATAVIZ = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1920&h=1080&fit=crop"
_ANALYTICS = "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1920&h=1080&fit=crop"
_BOOKS = "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=1920&h=1080&fit=crop"
_DNA = "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=1920&h=1080&fit=crop"
_NEURAL = "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1920&h=1080&fit=crop"
_CIRCUIT = "https://images.unsplash.com/photo-1555664424-778a1e5e1b48?w=1920&h=1080&fit=crop"
_AUTO = "https://images.unsplash.com/photo-1555255707-c07966088b7b?w=1920&h=1080&fit=crop"

THEME_IMAGES = {
    "safety_governance_and_reliability": [_CODE, _CHIP, _AI1],
    "neuroscience_and_cognitive_science": [_BRAIN, _NEURAL, _AI2],
    "multimodal_foundation_models": [_AI1, _AI2, _ROBOT],
    "multimodal_and_generative_systems": [_AI1, _AI2, _ROBOT],
    "reinforcement_learning": [_ROBOT, _AI1, _CODE],
    "generative_modeling_and_diffusion": [_ABSTRACT, _GRADIENT, _AI2],
    "robotics_and_embodied_intelligence": [_ROBOT, _AUTO, _AI1],
    "physics_and_ai_for_science": [_PHYSICS, _MATH, _AI2],
    "agents_and_autonomous_science": [_AI1, _AUTO, _ROBOT],
    "agent_systems_and_execution": [_AI1, _AUTO, _ROBOT],
    "chemistry_biology_and_lab_automation": [_LAB, _DNA, _AI2],
    "reasoning_memory_and_inference_control": [_BOOKS, _BRAIN, _MATH],
    "ai_hardware_and_accelerator_design": [_CHIP, _CIRCUIT, _CODE],
    "math_and_formal_reasoning": [_MATH, _PHYSICS, _DATAVIZ],
    "interpretability_and_mechanistic_analysis": [_DATAVIZ, _ANALYTICS, _AI1],
    "scientific_discovery_flagships": [_PHYSICS, _LAB, _AI2],
    "software_engineering_and_coding_agents": [_CODE, _ANALYTICS, _AI1],
    "public_health_and_medical_operations": [_LAB, _DNA, _AI2],
    "theory_robustness_and_core_ml": [_MATH, _DATAVIZ, _AI1],
    "jepa_and_predictive_world_models": [_AI2, _ROBOT, _DATAVIZ],
    "geospatial_remote_sensing_and_disaster_systems": [_AUTO, _DATAVIZ, _AI1],
    "weather_climate_and_and_earth_systems": [_AUTO, _PHYSICS, _AI2],
    "energy_water_and_infrastructure_systems": [_AUTO, _CHIP, _AI1],
    "industrial_process_and_manufacturing_systems": [_AUTO, _CHIP, _ROBOT],
}

FALLBACK_IMAGES = [_AI1, _AI2, _ROBOT, _CHIP, _CODE]


def fetch_theme_image(theme: str, index: int = 0, cache_dir: str = None) -> str:
    """Fetch a relevant image for a research theme."""
    if cache_dir is None:
        cache_dir = os.path.join(os.path.dirname(__file__), "output", "_images")
    os.makedirs(cache_dir, exist_ok=True)

    theme_images = THEME_IMAGES.get(theme, FALLBACK_IMAGES)
    url = theme_images[index % len(theme_images)]

    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    local_path = os.path.join(cache_dir, f"{url_hash}.jpg")

    if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
        return local_path

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(local_path, "wb") as f:
                f.write(resp.read())
        if os.path.getsize(local_path) > 1000:
            return local_path
    except Exception as e:
        print(f"  ⚠ Image download failed: {e}")

    return None


if __name__ == "__main__":
    for theme in ["safety_governance_and_reliability", "neuroscience_and_cognitive_science"]:
        img = fetch_theme_image(theme, 0, "/tmp/test_images")
        print(f"{theme}: {img}")
