from urllib.request import Request
from PIL import Image
import io

from create_titlecut import *

def app(environ, start_response):

    request = Request(environ)
    if request.method == 'GET':
        with open('index.html') as html_file:
            response_text = html_file.read()
        
        response_text = response_text.replace('{{DATA}}', 'Oh yeah custom data!')
        response_bytes = response_text.encode('utf-8')

        start_response('200 OK', [('Content-Type', 'text/html'), ('Content-Length', str(len(response_bytes)))])
        return iter([response_bytes])

    elif request.method == 'POST':
        image = create_titlecut(target_text='though~ rely on bad ligma!', dictionaries=['azurlane'])
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='png')
        image_byte_array = image_bytes.getvalue()

        data = image_byte_array
        start_response('200 OK', [('Content-Type', 'image/png'), ('Content-Length', str(len(data)))])
        return iter([data])