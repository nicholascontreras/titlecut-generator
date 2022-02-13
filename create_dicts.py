import os
import sys
import json

import PIL
from PIL import Image
from PIL import ImageFilter
from PIL import ImageFont
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

        dictionary_size_words = 0
        for word_instance_list in dictionary_data['words'].values():
            dictionary_size_words += len(word_instance_list)

        dictionary_size_letters = 0
        for letter_instance_list in dictionary_data['letters'].values():
            dictionary_size_letters += len(letter_instance_list)

        print('Dictionary size - words: ' + str(dictionary_size_words) + ' letters: ' + str(dictionary_size_letters))

def get_config_for_subject(subject_name: str) -> dict:
    DEFAULT_CONFIG = {
        'word_erode_count': 0,
        'letter_erode_count': 0,
        'erode_scaleback_factor': 1,
        'aspect_ratio_scale': 1
    }

    with open('image_sources/' + subject_name + '/config.json') as config_file:
        for key, value in json.load(config_file).items():
            DEFAULT_CONFIG[key] = value

        return DEFAULT_CONFIG

def add_image_to_dictionary(dictionary_data: dict, subject_name: str, image_name: str, config_settings: dict, save_preprocessed: bool) -> None:
    image = Image.open('image_sources/' + subject_name + '/' + image_name)
    image = preprocess_image(image=image, invert=config_settings['invert'], threshold=config_settings['threshold'])
    image = erode_image(image, erode_count=config_settings['word_erode_count'], scaleback_factor=config_settings['erode_scaleback_factor'])

    if save_preprocessed:
        image.save('image_sources/' + subject_name + '/preprocessed/' + image_name)

    words_ocr_results = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    add_words_to_dictionary(dictionary_data=dictionary_data, ocr_results=words_ocr_results, image_name=image_name, min_confidence=config_settings['word_confidence'])

    image = erode_image(image, erode_count=config_settings['letter_erode_count'], scaleback_factor=config_settings['erode_scaleback_factor'])
    letters_ocr_results = pytesseract.image_to_pdf_or_hocr(image, config='-c hocr_char_boxes=1', extension='hocr').decode("utf-8")
    add_letters_to_dictionary(dictionary_data=dictionary_data, ocr_results=letters_ocr_results, image_name=image_name, min_confidence=config_settings['letter_confidence'], aspect_ratio_scale=config_settings['aspect_ratio_scale'])


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

def add_letters_to_dictionary(dictionary_data: dict, ocr_results: str, image_name: str, min_confidence: float, aspect_ratio_scale: float) -> None:             
    
    font = ImageFont.load_default()
    
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

        width = right - left
        height = bottom - top

        if width > 0 and height > 0:
            ocr_results = ocr_results[ocr_results.index('x_conf'):]
            ocr_results = ocr_results[ocr_results.index(' '):]

            confidence_as_string = ocr_results[:ocr_results.index('\'')].strip()
            confidence = float(confidence_as_string)

            if confidence > min_confidence:
                ocr_results = ocr_results[ocr_results.index('>') + 1:]
                letter = ocr_results[:ocr_results.index('<')]

                expected_width, expected_height = font.getsize(letter)
                expected_ratio = expected_width / expected_height
                actual_ratio = width / height

                if abs(expected_ratio - (actual_ratio / aspect_ratio_scale)) / expected_ratio < 0.25:
                    if not letter in dictionary_data['letters']:
                        dictionary_data['letters'][letter] = []

                    dictionary_data['letters'][letter].append({'image_name': image_name, 'left': left, 'top': top, 'right': right, 'bottom': bottom})

def erode_image(image: Image.Image, erode_count: int, scaleback_factor: int) -> Image.Image:
    orig_size = image.size
    image = image.resize((image.width * scaleback_factor, image.height * scaleback_factor))

    for _ in range(erode_count):
        image = image.filter(ImageFilter.MaxFilter(3))

    image = image.resize(orig_size)

    return image

def preprocess_image(image: Image.Image, invert: bool, threshold: int) -> Image.Image:
    image = image.convert('L')

    if invert:
        image = PIL.ImageOps.invert(image)

    image = image.point(lambda pixel: 0 if pixel < threshold else 255)
    return image

if __name__ == '__main__':
    main()