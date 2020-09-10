from PIL import Image
from argparse import ArgumentParser
import io
import os
import requests
import time


def parse_args():
    parser = ArgumentParser(description='Options for the fragmented emoji')
    parser.add_argument('path', action='store', help='path to the image')
    parser.add_argument('--rows', action='store', type=int, default=4, help='number of rows')
    parser.add_argument('--cols', action='store', type=int, default=4, help='number of columns')
    parser.add_argument('--token', action='store', help='API token')
    return parser.parse_args()


def validate_args(m, n, rows, cols):
    if rows < 1 or cols < 1:
        raise ValueError('number of rows and columns must be positive integers')

    if m % rows != 0:
        raise ValueError('number of rows must divide the height of the image')

    if n % cols != 0:
        raise ValueError('number of rows must divide the width of the image')

    if m // rows != n // cols:
        raise ValueError('size of the fragment must be square')

def upload_emoji(file_obj, name, token, trial=1, default_timeout=30):
    headers = {
        'Authorization': 'Bearer {}'.format(token),
    }

    file_obj.seek(0);

    files = {
        'image': file_obj,
    }

    data = {
        'mode': 'data',
        'name': name,
    }

    resp = requests.post(
        'https://slack.com/api/emoji.add',
        headers=headers,
        data=data,
        files=files
    )

    if resp.status_code == 200:
        resp = resp.json()

        if not resp.get('ok'):
            print('Upload {} failed:\n{}'.format(name, resp))

        return bool(resp.get('ok'))
    elif resp.status_code == 429:
        if trial < 3:
            retry_sec = resp.headers.get('Retry-After', default_timeout)
            print('Rate limit exceeded. Retrying in {} seconds... ({} / 3)'.format(retry_sec, trial))
            time.sleep(retry_sec)
            return upload_emoji(file_obj, name, token, trial + 1, retry_sec * 2)
        else:
            print('Rate limit retry failed')

    return False


def remove_emoji(name, token):
    headers = {
        'Authorization': 'Bearer {}'.format(token),
    }

    data = {
        'name': name,
    }

    if not requests.post(
        'https://slack.com/api/emoji.remove',
        headers=headers,
        data=data
    ).json().get('ok'):
        print('Remove {} failed'.format(name))


def main():
    args = parse_args()
    path = args.path
    rows = args.rows
    cols = args.cols
    token = args.token

    directory = os.path.dirname(path)
    img_name = '.'.join(os.path.basename(path).split('.')[:-1])
    extension = os.path.basename(path).split('.')[-1]

    img = Image.open(path)
    m, n = img.size
    validate_args(m, n, rows, cols)

    height = m // rows
    width = n // cols

    slack_text_list = []
    for y in range(cols):
        slack_text_row = ''
        for x in range(rows):
            frag_name = '{}_{}_{}'.format(img_name, y, x)
            frag_filename = '{}.{}'.format(frag_name, extension)
            frag_path = os.path.join(directory, frag_filename)

            file_obj = io.BytesIO() if token else open(frag_path, 'wb')

            crop_region = (x * height, y * width, (x + 1) * height, (y + 1) * width)

            img.seek(0);
            new_img_base = img.crop(crop_region)
            append_images = []
            try:
                while True:
                    img.seek(img.tell() + 1)
                    sub_img = img.crop(crop_region)
                    append_images.append(sub_img)
            except EOFError:
                pass

            if extension == 'gif':
                new_img_base.save(
                    file_obj,
                    format=img.format,
                    save_all=True,
                    append_images=append_images
                )
            else:
                new_img_base.save(
                    file_obj,
                    format=img.format
                )


            if token:
                upload_emoji(file_obj, frag_name, token)

            file_obj.close()

            slack_text_row += ':{}:'.format(frag_name)

        slack_text_list.append(slack_text_row)

    print('\n'.join(slack_text_list))


if __name__ == '__main__':
    main()
