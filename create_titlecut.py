import os
import json
import random

from PIL import Image

def get_subjects() -> list[str]:
    return os.listdir('image_sources')

def create_titlecut(target_text: str, dictionaries: dict[str], ignore_case: bool) -> Image.Image:

    combined_dictionary, space_width = load_dictionaries(dictionaries)

    if ignore_case:
        combined_dictionary = dictionary_lowercase(combined_dictionary)
        target_text = target_text.lower()

    output_image_row_height = 50
    output_image = Image.new(mode='RGB', size=(1, output_image_row_height), color='white')

    cur_x_pos = 0
    cur_y_pos = 0

    for cur_word in target_text.split():
        if cur_word in combined_dictionary['words']:
            # Use a full word
            chosen_word_instance = random.choice(combined_dictionary['words'][cur_word])
            chosen_word_instance_source_image = Image.open('image_sources/'+ chosen_word_instance['subject_name'] + '/' + chosen_word_instance['image_name'])

            # Cut the word out of the source image
            chosen_word_instance_image = image_subsection(chosen_word_instance_source_image, chosen_word_instance['left'], chosen_word_instance['top'], chosen_word_instance['width'], chosen_word_instance['height'])
            # Scale the word image to fit our output image
            chosen_word_instance_image = scale_image_to_height(image=chosen_word_instance_image, height=output_image_row_height)
            # Append the word to the output image
            output_image, cur_x_pos, cur_y_pos = append_image(base_image=output_image, image_to_append=chosen_word_instance_image, append_x=cur_x_pos, append_y=cur_y_pos,  spacing_after=space_width)
        
            if cur_x_pos > 2000:
                cur_x_pos = 0
                cur_y_pos += output_image_row_height
        else:
            # Word doesn't exist, use letters to form word!
            word_length = len(cur_word)
            cur_letter_index = 0
            for cur_letter in cur_word:
                if not cur_letter in combined_dictionary['letters']:
                    raise TitlecutException('The letter "' + cur_letter + '" could not be found in the images selected')

                chosen_letter_instance = random.choice(combined_dictionary['letters'][cur_letter])
                chosen_letter_instance_source_image = Image.open('image_sources/'+ chosen_letter_instance['subject_name'] + '/' + chosen_letter_instance['image_name'])

                chosen_letter_instance_width = chosen_letter_instance['right'] - chosen_letter_instance['left']
                chosen_letter_instance_height = chosen_letter_instance['bottom'] - chosen_letter_instance['top']

                # Cut the letter out of the source image
                chosen_letter_instance_image = image_subsection(chosen_letter_instance_source_image, chosen_letter_instance['left'], chosen_letter_instance['top'], chosen_letter_instance_width, chosen_letter_instance_height)
                # Scale the letter image to fit our output image
                chosen_letter_instance_image = scale_image_to_height(image=chosen_letter_instance_image, height=output_image_row_height)
                # Append the letter to the output image
                if cur_letter_index == word_length - 1:
                    output_image, cur_x_pos, cur_y_pos = append_image(base_image=output_image, image_to_append=chosen_letter_instance_image, append_x=cur_x_pos, append_y=cur_y_pos, spacing_after=space_width)
                
                    if cur_x_pos > 2000:
                        cur_x_pos = 0
                        cur_y_pos += output_image_row_height

                else:
                    output_image, cur_x_pos, cur_y_pos = append_image(base_image=output_image, image_to_append=chosen_letter_instance_image, append_x=cur_x_pos, append_y=cur_y_pos, spacing_after=1)

                cur_letter_index += 1

    return output_image

def image_subsection(image: Image.Image, left: int, top: int, width: int, height: int, padding_percent: float = 0.1) -> Image.Image:
    left -= int(width * padding_percent)
    top -= int(height * padding_percent)
    right = int(left + width + (width * padding_percent * 2))
    bottom = int(top + height + (height * padding_percent * 2))
    return image.crop(box=(max(left, 0), max(top, 0), min(right, image.width), min(bottom, image.height)))


def scale_image_to_height(image: Image.Image, height: int) -> Image.Image:
    scale_factor = height / image.height
    scaled_width = int(image.width * scale_factor)
    scaled_height = int(image.height * scale_factor)
    return image.resize(size=(scaled_width, scaled_height))

def append_image(base_image: Image.Image, image_to_append: Image.Image, append_x: int, append_y: int, spacing_after: int = 0) -> tuple[Image.Image, int, int]:
    new_image = Image.new(mode='RGB', size=(max(append_x + image_to_append.width + spacing_after, base_image.width), append_y + image_to_append.height), color='white')
    new_image.paste(base_image, box=(0, 0))
    new_image.paste(image_to_append, box=(append_x, append_y))

    return (new_image, append_x + image_to_append.width + spacing_after, append_y)

def load_dictionaries(dictionary_names: list[str]) -> tuple[dict, int]:

    combined_dictionary = {'words': {}, 'letters': {}}
    sum_of_letter_widths = 0
    num_of_letter_widths = 0

    for cur_dictionary_name in dictionary_names:
        with open('image_sources/' + cur_dictionary_name + '/dictionary.json') as cur_dictionary:
            cur_dictionary_data = json.load(cur_dictionary)

            for cur_word in cur_dictionary_data['words']:
                if not cur_word in combined_dictionary:
                    combined_dictionary['words'][cur_word] = []
                
                for cur_word_instance in cur_dictionary_data['words'][cur_word]:
                    cur_word_instance['subject_name'] = cur_dictionary_name
                    combined_dictionary['words'][cur_word].append(cur_word_instance)

            for cur_letter in cur_dictionary_data['letters']:
                if not cur_letter in combined_dictionary:
                    combined_dictionary['letters'][cur_letter] = []

                for cur_letter_instance in cur_dictionary_data['letters'][cur_letter]:
                    cur_letter_instance['subject_name'] = cur_dictionary_name
                    combined_dictionary['letters'][cur_letter].append(cur_letter_instance)

                    sum_of_letter_widths += cur_letter_instance['right'] - cur_letter_instance['left'] 
                    num_of_letter_widths += 1

    return (combined_dictionary, sum_of_letter_widths // num_of_letter_widths)

def dictionary_lowercase(dictionary: dict) -> dict:
    lowercase_dictionary = {'words': {}, 'letters': {}}

    for cur_word in dictionary['words']:
        lowercase_dictionary['words'][cur_word.lower()] = dictionary['words'][cur_word]

    for cur_letter in dictionary['letters']:
        lowercase_dictionary['letters'][cur_letter.lower()] = dictionary['letters'][cur_letter]

    return lowercase_dictionary

class TitlecutException(Exception):
    pass


if __name__ == '__main__':
    create_titlecut(target_text='though~ rely on bad ligma!', dictionaries=['azurlane']).save('output.png')