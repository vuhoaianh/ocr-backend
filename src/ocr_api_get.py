import requests
import cv2

# URL of your FastAPI app's endpoint
api_url = "http://127.0.0.1:3502/api/ocr_temp"  # Replace with your actual URL

# Path to the image file you want to process
image_path = r"C:\Users\Sondv\Documents\sondv\code4fun\smart_ocr\demo_image.png"
# image_path = r"doc_temp/phieuchi_temp.docx"

# Create a dictionary with the file to send in the request
files = {"file": open(image_path, "rb")}

form_data = {"template_id": "1"}

# Make a POST request to the FastAPI endpoint
response = requests.post(api_url, files=files,data=form_data)

# Check the response
if response.status_code == 200:
    result = response.json()
    print("Image processing result:", result)
else:
    print("Error:", response.status_code, response.text)
