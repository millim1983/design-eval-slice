import os
import io
import torch
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration

# Path to local LLaVA model weights
MODEL_PATH = os.environ.get("LLAVA_MODEL_PATH")
if not MODEL_PATH:
    raise EnvironmentError("LLAVA_MODEL_PATH is not set")

# Optional device override; default to CUDA when available
DEVICE = os.getenv("LLAVA_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
DTYPE = torch.float16 if "cuda" in DEVICE else torch.float32

# Load processor and model once at import time
PROCESSOR = AutoProcessor.from_pretrained(MODEL_PATH)
MODEL = LlavaForConditionalGeneration.from_pretrained(
    MODEL_PATH, torch_dtype=DTYPE
).to(DEVICE)


def query_llm(prompt: str, image_bytes: bytes) -> str:
    """Run a prompt+image pair through the local LLaVA model."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = PROCESSOR(text=prompt, images=image, return_tensors="pt").to(DEVICE, dtype=DTYPE)
    with torch.inference_mode():
        output_ids = MODEL.generate(**inputs, max_new_tokens=256)
    return PROCESSOR.batch_decode(output_ids, skip_special_tokens=True)[0]
