import os
import sys
import json

import PIL
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

def main():

    if len(sys.argv) == 1:
        save_preprocessed = False
        subject_folders = os.listdir('image_sources')
    else:
        save_preprocessed = True
        subject_folders = sys.argv[1:]

    for cur_subject_folder in subject_folders:

        print('Creating dictionary for subject: ' + cur_subject_folder)

        if not os.path.exists('image_sources/' + cur_subject_folder + '/preprocessed'):
            os.mkdir('image_sources/' + cur_subject_folder + '/preprocessed')

        config_settings = get_config_for_subject(cur_subject_folder)
        dictionary_data = {'words': {}, 'letters': {}}

        files = os.listdir('image_sources/' + cur_subject_folder)
        
        for cur_file in files:
            if cur_file.lower().endswith(('.png', '.jpg', 'jpeg')):
                add_image_to_dictionary(dictionary_data, cur_subject_folder, cur_file, config_settings, save_preprocessed)

        with open('image_sources/' + cur_subject_folder + '/dictionary.json', 'w') as dictionary_file:
            json.dump(dictionary_data, dictionary_file)

def get_config_for_subject(subject_name: str) -> dict:
    with open('image_sources/' + subject_name + '/config.json') as config_file:
        return json.load(config_file)

def add_image_to_dictionary(dictionary_data: dict, subject_name: str, image_name: str, config_settings: dict, save_preprocessed: bool) -> None:
    image = Image.open('image_sources/' + subject_name + '/' + image_name)
    image = preprocess_image(image=image, invert=config_settings['invert'], threshold=config_settings['threshold'])
    image.save('image_sources/' + subject_name + '/preprocessed/' + image_name)

    words_ocr_results = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    add_words_to_dictionary(dictionary_data=dictionary_data, ocr_results=words_ocr_results, image_name=image_name, min_confidence=config_settings['word_confidence'])

    letters_ocr_results = pytesseract.image_to_pdf_or_hocr(image, config='-c hocr_char_boxes=1', extension='hocr').decode("utf-8") 
    add_letters_to_dictionary(dictionary_data=dictionary_data, ocr_results=letters_ocr_results, image_name=image_name, min_confidence=config_settings['letter_confidence'])


def add_words_to_dictionary(dictionary_data: dict, ocr_results: dict, image_name: str, min_confidence: float) -> None:
    num_results = len(ocr_results['level'])

    for i in range(num_results):
        if (ocr_results['level'][i] == 5):
            # Only if this result is a word match
            confidence = float(ocr_results['conf'][i])
            if confidence > min_confidence:
                # Greather than 50% confidence
                text = ocr_results['text'][i]
                left = int(ocr_results['left'][i])
                top = int(ocr_results['top'][i])
                width = int(ocr_results['width'][i])
                height = int(ocr_results['height'][i])

                if not text in dictionary_data['words']:
                    dictionary_data['words'][text] = []

                dictionary_data['words'][text].append({'image_name': image_name, 'left': left, 'top': top, 'width': width, 'height': height})

def add_letters_to_dictionary(dictionary_data: dict, ocr_results: str, image_name: str, min_confidence: float) -> None:             

    while True:
        next_letter_index = ocr_results.find('<span class=\'ocrx_cinfo\'')
        if next_letter_index == -1:
            break

        ocr_results = ocr_results[next_letter_index:]
        ocr_results = ocr_results[ocr_results.index('x_bboxes'):]
        ocr_results = ocr_results[ocr_results.index(' '):]

        bounding_box_as_strings = ocr_results[:ocr_results.index(';')].strip().split()
        left = int(bounding_box_as_strings[0])
        top = int(bounding_box_as_strings[1])
        right = int(bounding_box_as_strings[2])
        bottom = int(bounding_box_as_strings[3])

        ocr_results = ocr_results[ocr_results.index('x_conf'):]
        ocr_results = ocr_results[ocr_results.index(' '):]

        confidence_as_string = ocr_results[:ocr_results.index('\'')].strip()
        confidence = float(confidence_as_string)

        ocr_results = ocr_results[ocr_results.index('>') + 1:]
        letter = ocr_results[:ocr_results.index('<')]

        if confidence > min_confidence:
            if not letter in dictionary_data['letters']:
                dictionary_data['letters'][letter] = []

            dictionary_data['letters'][letter].append({'image_name': image_name, 'left': left, 'top': top, 'right': right, 'bottom': bottom})

def preprocess_image(image: Image.Image, invert: bool, threshold: int) -> Image.Image:
    image = image.convert('L')

    if invert:
        image = PIL.ImageOps.invert(image)

    image = image.point(lambda pixel: 0 if pixel < threshold else 255)
    return image

if __name__ == '__main__':
    main()