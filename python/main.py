import os
import logging
import pathlib
import sqlite3
import hashlib
from fastapi import FastAPI, Form, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [ os.environ.get('FRONT_URL', process.env.FRONT_URL) ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

DB_PATH = "../db/mercari.sqlite3"

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.post("/items")
async def add_item(name: str = Form(...),
                   category: str = Form(...),
                   image: UploadFile = File(...)):
    ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
    def is_image_file(filename: str) -> bool:
        extension = os.path.splitext(filename)[1].lower()
        return extension in ALLOWED_IMAGE_EXTENSIONS
    if not is_image_file(image.filename):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    image_bytes = await image.read() # turn the image into a buffer-like object
    image_hashed = hashlib.sha256(image_bytes).hexdigest()  # hash the image
    new_image_name = image_hashed + ".jpg"
    with open(f"images/{new_image_name}", "wb") as f:
        f.write(image_bytes)  # write the hashed image to a file
    
    connection = sqlite3.connect(DB_PATH) # connect to database
    cursor = connection.cursor()

    category_sql = "INSERT OR IGNORE INTO category (name) VALUES (?)"
    cursor.execute(category_sql, (category,))
    get_category_id_sql = "SELECT category.id FROM category WHERE category.name LIKE ?"
    cursor.execute(get_category_id_sql, (category,))
    category_id = cursor.fetchone()[0]

    new_item_sql = "INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?)"
    new_item = (name, category_id, new_image_name)
    cursor.execute(new_item_sql, new_item)
    connection.commit()

    logger.info(f"Receive item: {name}")
    return {"message": f"item received: {name}"}

@app.get("/items")
def listed_items():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT items.id, items.name, category.name as category, items.image_name FROM items JOIN category ON items.category_id = category.id")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    items = [dict(zip(columns, row)) for row in rows]
    connection.close()

    return {"items": items}

@app.get("/search")
def search_items(keyword: str):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    if keyword:
        cursor.execute(
            "SELECT items.name, category.name AS category_name, items.image_name "
            "FROM items "
            "JOIN category ON items.category_id = category.id "
            "WHERE items.name LIKE ?",
            ('%' + keyword + '%',))
    
    rows = cursor.fetchall()

    items = []  
    for row in rows:
        name, category_name, image_name = row
        item = {
            "name": name,
            "category_name": category_name,
            "image_name": image_name
        }
    
        items.append(item)

    if len(items) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    return {"items": items}

@app.get("/image/{image_filename}")
async def get_image(image_filename):
# Create image path
    image = images / image_filename

    if not image_filename.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"
    return FileResponse(image)