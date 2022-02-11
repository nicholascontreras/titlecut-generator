from PIL import Image
import io

from create_titlecut import *

def app(environ, start_response):

    image = create_titlecut(target_text='though~ rely on bad ligma!', dictionaries=['azurlane'])
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='png')
    image_byte_array = image_bytes.getvalue()

    data = image_byte_array
    start_response("200 OK", [
        ("Content-Type", "image/png"),
        ("Content-Length", str(len(data)))
    ])
    return iter([data])