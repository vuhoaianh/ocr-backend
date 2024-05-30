import json
import sys

import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import pandas as pd
import matplotlib
from src.init_models import tsr_model

str_class_name2idx = {
            'table': 0,
            'table column': 1,
            'table row': 2,
            'table column header': 3,
            'table projected row header': 4,
            'table spanning cell': 5,
            'no object': 6
        }
str_class_idx2name = {v:k for k, v in str_class_name2idx.items()}

str_class_thresholds = {
    "table": 0.5,
    "table column": 0.5,
    "table row": 0.5,
    "table column header": 0.5,
    "table projected row header": 0.5,
    "table spanning cell": 0.5,
    "no object": 0.5
}

class MaxResize(object):
    def __init__(self, max_size=800):
        self.max_size = max_size

    def __call__(self, image):
        width, height = image.size
        print(width, height)
        current_max_size = max(width, height)
        scale = self.max_size / current_max_size
        resized_image = image.resize((int(round(scale*width)), int(round(scale*height))))
        
        return resized_image

structure_transform = transforms.Compose([
    MaxResize(1000),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def outputs_to_objects(outputs, img_size, class_idx2name):
    m = outputs['pred_logits'].softmax(-1).max(-1)
    pred_labels = list(m.indices.detach().cpu().numpy())[0]
    pred_scores = list(m.values.detach().cpu().numpy())[0]
    pred_bboxes = outputs['pred_boxes'].detach().cpu()[0]
    pred_bboxes = [elem.tolist() for elem in rescale_bboxes(pred_bboxes, img_size)]
    objects = []
    for label, score, bbox in zip(pred_labels, pred_scores, pred_bboxes):
        class_label = class_idx2name[int(label)]
        if not class_label == 'no object':
            if bbox == None:
              continue
            objects.append({'label': class_label, 'bbox': [int(elem) for elem in bbox]})

    return objects

def box_cxcywh_to_xyxy(x):
    x_c, y_c, w, h = x.unbind(-1)
    b = [(x_c - 0.5 * w), (y_c - 0.5 * h), (x_c + 0.5 * w), (y_c + 0.5 * h)]
    return torch.stack(b, dim=1)

def rescale_bboxes(out_bbox, size):
    img_w, img_h = size
    b = box_cxcywh_to_xyxy(out_bbox)
    b = b * torch.tensor([img_w, img_h, img_w, img_h], dtype=torch.float32)
    return b


def table_structure_recognize(img, out_objects=False, out_cells=False,
                  out_html=False, out_csv=False):
    out_formats = {}
    if tsr_model is None:
        print("No structure model loaded.")
        return out_formats
    # Transform the image how the model expects it
    img_tensor = structure_transform(img)

    # Run input image through the model
    outputs = tsr_model([img_tensor.to("cpu")])
    # Post-process detected objects, assign class labels
    objects = outputs_to_objects(outputs, img.size, str_class_idx2name)
    return objects

if __name__ == "__main__":
    output = table_structure_recognize("../data/tsr/hsg_20.jpg")
    print(output)