import os
import gridfs
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
fs = gridfs.GridFS(db)

def save_file(file_obj, filename, content_type):
    try:
        file_id = fs.put(file_obj, filename=filename, content_type=content_type)
        return str(file_id)
    except PyMongoError as e:
        raise RuntimeError(f"Failed to save file to MongoDB: {e}")

def get_file(file_id):
    try:
        return fs.get(ObjectId(file_id))
    except PyMongoError as e:
        raise RuntimeError(f"Failed to fetch file from MongoDB: {e}")

def get_file_bytes(file_id):
    grid_out = get_file(file_id)
    return grid_out.read()

def delete_file(file_id):
    try:
        fs.delete(ObjectId(file_id))
    except PyMongoError as e:
        raise RuntimeError(f"Failed to delete file from MongoDB: {e}")

def file_exists(filename):
    return fs.exists({"filename": filename})
    
def list_files():
    return [
        {
            "id": str(f._id),
            "filename": f.filename,
            "content_type": getattr(f, "content_type", None),
            "upload_date": f.upload_date,
            "length": f.length,}
        for f in fs.find()]
