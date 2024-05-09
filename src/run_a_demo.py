from utils import seperate_image, ocr_table
import cv2
import json
from table2excel import table2excel


# image = r"C:\Users\Sondv\Documents\sondv\code4fun\smart_ocr\demo_image.png"
image = r"dd.png"
img = cv2.imread(image)
results = seperate_image(img)
tables_metadata = []
if len(results['tables']) != 0:
    for table in results['tables']:
        table_data = ocr_table(table)
        tables_metadata.append({'table_id': "id", 'table_coordinate': table['table_coordinate'],
                                'table_image': 'test', 'table_data': table_data})
dm = tables_metadata[0]
print(dm)
table2excel(data=dm, filename="table.xlsx")
