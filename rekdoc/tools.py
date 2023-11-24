import json
import logging
import click
import sys, re, io, os, subprocess
from textwrap import wrap
# try:
from PIL import Image
from PIL import ImageColor
from PIL import ImageDraw
from PIL import ImageFont
# # except:
#     from pil import Image
#     from pil import ImageColor
#     from pil import ImageDraw
# from pil import ImageFont


##### JSON #####
# get a dictionary as input and dump it to a json type file
def save_json(file, content):
    if not content:
        click.echo("No content from input to save!")
        return -1
    try:
        with open(file, "w") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    except OSError as err:
        logging.error("OS error: ", err)
        raise RuntimeError("Cannot save JSON") from err


def read_json(file):
    try:
        with open(file, "r") as f:
            content = json.load(f)
        return content
    except FileNotFoundError as err:
        logging.error("Input file not found!")
        raise RuntimeError("JSON file must be exist") from err
    except ValueError as err:
        logging.error("Invalid JSON file")
        raise RuntimeError("Cannot read JSON file") from err


def join_json(content_files, output):
    try:
        with open(output, "w+") as file:
            x = {}
            for i in content_files:
                path = "./output/" + i.split(".")[0]
                path = os.path.normpath("".join(path).split("_")[0] + "/" + i + ".json")
                buffer = read_json(path)
                key = list(buffer)[0]
                x[key] = buffer[key]
            json.dump(x, file, indent=4, ensure_ascii=False)
    except OSError as err:
        logging.error("OS error: ", err)
        raise RuntimeError("Cannot write contents to JSON file") from err


##### END JSON #####


def save_file(file, content):
    try:
        with open(file, "w") as f:
            f.write(content)
    except OSError as err:
        logging.error("OS error: ", err)
        raise RuntimeError("Cannot save file: ") from err


def rm_ext(file, ext):
    return file[: -len(ext) - 1]


##### IMAGE GENERATE METHOD #####
# transform text to a png image file
def drw_text_image(text, file):
    size = 14
    try:
        font = ImageFont.truetype(
            "DejaVuSansMono", size=size, layour_engine=ImageFont.Layout.BASIC
        )
    except OSError:
        font = ImageFont.load_default(size)
    except:
        font = ImageFont.load_default()
    with Image.new("RGB", (1000, 1000)) as img:
        d1 = ImageDraw.Draw(img)
        # left, top, right, bottom = 1
        left, top, right, bottom = d1.textbbox((10, 10), text.getvalue(), font=font)
        w = int(right * 1.1) + 10
        h = int(bottom * 1.1) + 10
        img_resize = img.crop((0, 0, w, h))
        d2 = ImageDraw.Draw(img_resize)
        x = 10
        y = 10
        left, top, right, bottom = font.getbbox(text.getvalue())
        attSpacing = bottom
        for line in text.getvalue().split("\n"):
            d2.text((x, y), line.strip("\r"), font=font)
            y = y + attSpacing
        img_resize.save(file, format="PNG")


##### END OF IMAGE #####


##### BASE ######
def run(command, tokenize):
    try:
        process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                )
    except FileNotFoundError as err:
        click.echo()
        click.echo("Command not found: " + command[0])
        raise RuntimeError(err)
    stdout_stream, stderr_stream = process.communicate()
    returncode = process.wait()

    if not isinstance(stdout_stream, str):
        stdout_stream = stdout_stream.decode("utf-8")
    if not isinstance(stderr_stream, str):
        stderr_stream = stderr_stream.decode("utf-8")

    if tokenize:
        stdout = stdout_stream.splitlines()
        stderr = stderr_stream.splitlines()
    else:
        stdout = stdout_stream
        stderr = stderr_stream

    return stdout, stderr, returncode


def cat(file, stdout=False):
    try:
        command = ["cat", file]
        stdout, stderr, code = run(command, False)
    except RuntimeError:
        click.echo("Cannot cat file: " + file)
        raise
    # except Exception as err:
    #     raise RuntimeError("Cat command failed.")
    logging.debug(stdout)
    return stdout


def grep(path, regex, single_match, next=0):
    command = ["grep", "-e", regex]

    if single_match:
        command.extend(["-m1"])
        command.extend(["-A", str(next)])
    else:
        command.extend(["-A", str(next)])
    command.extend([path])

    stdout, stderr, code = run(command, False)

    logging.debug(stdout)
    return stdout


##### END BASE #####
