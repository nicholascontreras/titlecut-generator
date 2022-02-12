from urllib.request import Request
from urllib import parse
from PIL import Image
import io

from create_titlecut import *

def app(environ, start_response):

    request_method = environ['REQUEST_METHOD']

    if request_method == 'GET':
        response_bytes = get(start_response)
    elif request_method == 'POST':
        content_length = int(environ['CONTENT_LENGTH'])
        post_body = environ['wsgi.input'].read(content_length).decode('utf-8')
        response_bytes = post(start_response, post_body)
        
    return iter([response_bytes])

def get(start_response) -> bytes:
    with open('index.html') as html_file:
        response_text = html_file.read()
        
    response_text = response_text.replace('//DATA//', format_data())
    response_bytes = response_text.encode('utf-8')

    start_response('200 OK', [('Content-Type', 'text/html'), ('Content-Length', str(len(response_bytes)))])
    return response_bytes

def format_data() -> str:
    data_string = 'const SUBJECTS = ['
    for cur_subject in get_subjects():
        data_string += '"' + cur_subject + '",'
    data_string = data_string[:-1]
    data_string += '];\n'

    return data_string

def post(start_response, post_body: str) -> bytes:

    titlecut_text = ''
    titlecut_subjects = []
    titlecut_ignore_case = False

    for cur_form_response in post_body.split('&'):
        response_name, response_value = tuple(cur_form_response.split('='))
        response_value = parse.unquote_plus(response_value)

        if response_name == 'titlecut_subjects':
            titlecut_subjects.append(response_value)
        elif response_name == 'titlecut_text':
            titlecut_text = response_value
        elif response_name == 'titlecut_ignore_case':
            titlecut_ignore_case = True

    try:
        image = create_titlecut(target_text=titlecut_text, dictionaries=titlecut_subjects, ignore_case=titlecut_ignore_case)
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='png')
        image_byte_array = image_bytes.getvalue()

        data = image_byte_array
        start_response('200 OK', [('Content-Type', 'image/png'), ('Content-Length', str(len(data)))])
    except TitlecutException as e:
        error_message = 'ERROR:\n' + str(e) + '\n\nPlease go back and try again with a different set of source images or text.'
        data = error_message.encode('utf-8')
        start_response('500 Server Error', [('Content-Type', 'text/plain'), ('Content-Length', str(len(data)))])
    return data
