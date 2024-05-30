from PIL import Image
from tempfile import SpooledTemporaryFile
from fastapi import FastAPI, File, UploadFile
from init_models import cccd_ocr
import numpy as np


app = FastAPI()


@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    with SpooledTemporaryFile(max_size=1024) as temp_file:
        temp_file.write(await file.read())

        if temp_file.tell() == 0:
            return {"status": "error", "message": "Empty data received"}

        temp_file.seek(0)

        try:
            image = Image.open(temp_file)
            image = np.array(image)

            result_image = cccd_ocr.ocr_process(image)

            return {"status": "success", "result": result_image}
        except Exception as e:
            return {"status": "error", "message": f"Failed to process image. Error: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=1998)