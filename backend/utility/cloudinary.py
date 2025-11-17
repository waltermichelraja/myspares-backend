import cloudinary
import cloudinary.uploader

cloudinary.config(secure=True)

def upload_image(file_path, folder=None):
    try:
        result=cloudinary.uploader.upload(file_path, folder=folder)
        return result.get("secure_url")
    except Exception as e:
        raise RuntimeError(f"cloudinary upload failed: {e}")
