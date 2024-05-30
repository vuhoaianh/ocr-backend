import gradio as gr
from PIL import Image
import numpy as np
from init_models import cccd_ocr


iface = gr.Interface(
    fn=cccd_ocr.ocr_process,
    inputs="image",   # Input component type (image input in this case)
    outputs="text"   # Output component type (image output in this case)
)

iface.launch(share=True)