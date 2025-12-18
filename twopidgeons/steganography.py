from PIL import Image
import struct

class Steganography:
    """
    Implements simple steganography for JPEG images using EXIF metadata.
    True LSB steganography is not possible with standard JPEG compression as it is lossy.
    We use the ImageDescription EXIF tag (0x010e) to hide data.
    """
    
    TAG_IMAGE_DESCRIPTION = 0x010e

    @staticmethod
    def embed(image_path: str, data: str) -> bool:
        """
        Embeds a string into the image metadata.
        """
        try:
            img = Image.open(image_path)
            exif = img.getexif()
            
            # Embed data into ImageDescription tag
            exif[Steganography.TAG_IMAGE_DESCRIPTION] = data
            
            # Save the image with the new EXIF data
            # Force JPEG format since .2pg is just a renamed JPEG
            img.save(image_path, exif=exif, format='JPEG')
            return True
        except Exception as e:
            print(f"Steganography error: {e}")
            return False

    @staticmethod
    def extract(image_path: str) -> str:
        """
        Extracts the hidden string from the image metadata.
        """
        try:
            img = Image.open(image_path)
            exif = img.getexif()
            
            data = exif.get(Steganography.TAG_IMAGE_DESCRIPTION)
            if data:
                return str(data)
            return None
        except Exception as e:
            print(f"Steganography extraction error: {e}")
            return None
