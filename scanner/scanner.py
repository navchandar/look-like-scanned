#!/usr/bin/env python
"""Module to convert PDF/Images to look like they were scanned"""

import os
import io
import random
import argparse
from pathlib import Path
from importlib import metadata
from pprint import pprint as pretty_print
from PIL import Image, ImageEnhance, ImageFilter
import pypdfium2 as pdfium
from colorama import Fore, Style, init

SUPPORTED_IMAGES = ["jpg", "png", "jpeg", "webp"]
SUPPORTED_DOCS = ["pdf", "PDF"]
CHOICES = ["y", "yes", "n", "no", "true", "false"]


def print_color(text, color):
    """
    Print the specified text in the given color.
    Available colors: 'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'.
    """
    color_map = {
        "black": Fore.BLACK,
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE,
    }
    color_code = color_map.get(color.lower(), Fore.RESET)
    print(color_code + text + Style.RESET_ALL)


# Initialize colorama
init()


def parse_args():
    """Parse input command-line arguments for the script"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input_folder",
        type=str,
        help="The input folder to read files from and convert (default: current directory)",
    )
    parser.add_argument(
        "-f",
        "--file_type_or_name",
        type=str,
        help="The file types to process or file name to process.\
    Valid value - image, pdf, file names (default: pdf)",
    )
    parser.add_argument(
        "-q",
        "--file_quality",
        type=int,
        choices=range(50, 101, 5),
        default=95,
        help="The quality of the converted output files.\
    Valid range - 50 to 100 increment in steps of 5 (default: 95)",
    )
    parser.add_argument(
        "-a",
        "--askew",
        type=str.lower,
        choices=CHOICES,
        default="yes",
        help="Make output documents slightly askew or slightly tilted (default: yes)",
    )
    parser.add_argument(
        "-r",
        "--recurse",
        type=str.lower,
        choices=CHOICES,
        default="no",
        help="Recurse in all sub folders to find matching files and convert them (default: no)",
    )
    parser.add_argument(
        "-s",
        "--sort_by",
        type=str.lower,
        choices=["name", "ctime", "mtime", "none"],
        default="name",
        help="Sort the list of files in order by name or creation time or modified time (default: name)",
    )
    parser.add_argument(
        "-b",
        "--black_and_white",
        type=str.lower,
        choices=CHOICES,
        default="no",
        help="Make output documents black and white. Make it look like a photocopy (default: no)",
    )
    parser.add_argument(
        "-l",
        "--blur",
        type=str.lower,
        choices=CHOICES,
        default="no",
        help="Make output documents look blurry. (default: no)",
    )
    parser.add_argument(
        "-c",
        "--contrast",
        type=float,
        default=1.0,
        help="A factor of 0.0 gives a solid gray image.\
    A factor of 1.0 gives the original image. \
    Greater values increase the contrast of the image",
    )
    parser.add_argument(
        "-sh",
        "--sharpness",
        type=float,
        default=1.0,
        help="A factor of 0.0 gives a blurred image image.\
    A factor of 1.0 gives the original image. \
    Greater values increase the sharpness of the image",
    )
    parser.add_argument(
        "-br",
        "--brightness",
        type=float,
        default=1.0,
        help="A factor of 0.0 gives a black image.\
    A factor of 1.0 gives the original image. \
    Greater values increase the brightness of the image",
    )
    return parser.parse_args()


def get_input_folder(args):
    """
    Gets the input folder from the command-line argument.
    If argument not provided, returns current working directory as input folder
    """
    input_folder = (
        os.path.abspath(args.input_folder) if args.input_folder else os.getcwd()
    )
    if os.path.exists(input_folder):
        print(f"Processing files from {input_folder=}")
    else:
        print_color(f"Error: Input folder path not found: {input_folder}", "Red")
    return input_folder


def get_quality(args):
    """Return the output file quality from command-line argument"""
    return args.file_quality


def _is_true(arg):
    """Return True in boolean type if given argument string is true or yes"""
    return arg.lower().startswith(("y", "t"))


def get_askew(args):
    """Return if output file should have skewed pages"""
    return _is_true(args.askew)


def get_recurse(args):
    """Return if input files should be searched within sub folders"""
    return _is_true(args.recurse)


def get_blackandwhite(args):
    """Return if output files should look like a photocopy"""
    return _is_true(args.black_and_white)

def get_blur(args):
    """Return if output files should be blurry"""
    return _is_true(args.blur)


def get_contrast(args):
    """Return the output file contrast from command-line argument"""
    return args.contrast


def get_sharpness(args):
    """Return the output file sharpness from command-line argument"""
    return args.sharpness


def get_brightness(args):
    """Return the output file brightness from command-line argument"""
    return args.brightness


def get_sort_key(args):
    """Return the key with which files should be sorted and then coverted"""
    sort_by = args.sort_by.lower().strip()
    key_map = {"name": os.path.abspath, "ctime": os.path.getctime, "mtime": os.path.getmtime}
    return key_map.get(sort_by)

def get_file_type(args):
    """Get file type and supported documents based on input arguments"""
    if args.file_type_or_name:
        file_type = args.file_type_or_name.lower()
        if file_type == "image":
            return "image", SUPPORTED_IMAGES
        if any(
            f.endswith(file_type) or file_type.endswith(f) for f in SUPPORTED_IMAGES
        ):
            return "image", [args.file_type_or_name]
        if any(f.endswith(file_type) or file_type.endswith(f) for f in SUPPORTED_DOCS):
            return "pdf", [args.file_type_or_name]
    # if none of the above scenarios match, default to PDFs
    print("Defaulting to find pdf files")
    return "pdf", SUPPORTED_DOCS


def human_size(size_in_bytes, base=1024.0, suffix="B"):
    """Return input file size in bytes in a human readable format like KiB, MiB, etc."""
    if size_in_bytes == 0:
        return f"0 {suffix}"
    units = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]
    for unit in units:
        if abs(size_in_bytes) < base:
            return f"{size_in_bytes:3.1f}{unit}{suffix}"
        size_in_bytes /= base
    return f"{size_in_bytes:.1f}Yi{suffix}"


def get_file_size(file_path):
    """Get file size for a given file path"""
    return human_size(os.stat(file_path).st_size)


def files_exists(file_path):
    """Check if given file path exists in the file system"""
    if os.path.exists(file_path):
        return True
    print_color(f"File doesn't exist or incorrect path: {file_path}", "Red")
    return False


def reduce_image_quality(image, quality=100, compression="JPEG"):
    """Reduce quality of a given image object"""
    img_byte_array = io.BytesIO()
    # Save the image to the in-memory file object
    image.save(img_byte_array, quality=quality, format=compression)

    # Rewind the file object to the beginning
    img_byte_array.seek(0)
    # Open the image from the in-memory file object
    reduced_image = Image.open(img_byte_array)
    return reduced_image


def _change_image_to_byte_buffer(image, compression="JPEG"):
    """
    Save the image data to an in-memory file-like object
    """
    img_byte_array = io.BytesIO()
    image.save(img_byte_array, quality=95, format=compression)
    # Reset the file position to the beginning
    img_byte_array.seek(0)
    return img_byte_array


def rotate_image(image, angle):
    """Rotate PIL Image object with given angle value"""
    rotated_image = image.rotate(
        angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255)
    )
    return rotated_image


def black_and_white_image(image):
    """Make image black and white like a photocopy"""
    bw_image = image.convert("L")
    # Adjust the contrast level
    enhancer = ImageEnhance.Contrast(bw_image)
    bw_image = enhancer.enhance(random.uniform(1.2, 1.5))
    return bw_image


def blur_image(image):
    """Blur a PIL Image object"""
    blurred_image = image.filter(ImageFilter.GaussianBlur(random.uniform(1.2, 1.4)))
    return blurred_image


def change_contrast(image, contrast_factor):
    """Change contrast of a PIL Image object"""
    return ImageEnhance.Contrast(image).enhance(contrast_factor)


def change_sharpness(image, sharpness_factor):
    """Change sharpness of a PIL Image object"""
    return ImageEnhance.Sharpness(image).enhance(sharpness_factor)


def change_brightness(image, brightness_factor):
    """Change brightness of a PIL Image object"""
    return ImageEnhance.Brightness(image).enhance(brightness_factor)


def _convert_pdf_pages_to_jpg_list(
    pdf_path,
    image_quality=100,
    askew=True,
    black_and_white=False,
    blur=False,
    contrast=1.0,
    sharpness=1.0,
    brightness=1.0,
):
    """Reads given PDF file and converts all pages to image objects"""
    images_list = []
    try:
        doc = pdfium.PdfDocument(pdf_path)

        # If pdf contains forms, initiate form fields to render on output
        if doc.get_formtype():
            doc.init_forms()

        for page in doc:
            try:
                # increase render resolution for better scanned image quality
                bitmap = page.render(scale=2)
                image = bitmap.to_pil().convert("RGB")
                image = reduce_image_quality(image, image_quality)
                image = ImageEnhance.Brightness(image).enhance(random.uniform(1.01, 1.02))

                # Rotate every image by a small random angle
                if askew:
                    image = rotate_image(image, random.uniform(-0.55, 0.55))

                # Make image black and white like a photocopy
                if black_and_white:
                    image = black_and_white_image(image)

                # Make image blurry
                if blur:
                    image = blur_image(image)

                # Adjust image constrast
                if contrast != 1.0:
                    image = change_contrast(image, contrast)

                # change image sharpness
                if sharpness != 1.0:
                    image = change_sharpness(image, sharpness)

                # change image brightness
                if brightness != 1.0:
                    image = change_brightness(image, brightness)

                image = _change_image_to_byte_buffer(image)
                if image:
                    images_list.append(image)
                else:
                    print_color(f"Error processing page: No Image content", "Red")
            except Exception as page_err:
                print_color(f"Error processing page: {page_err}", "Red")
            finally:
                page.close()

        doc.close()
    except Exception as err:
        print_color(f"Failed to convert PDF to images: {err}", "Red")

    return images_list

def _save_image_obj_to_pdf(images_list, output_pdf_path, pdf_version=17):
    """Save image objects into output PDF"""
    pages_scanned = 0
    if not images_list:
        return pages_scanned

    try:
        output_pdf = pdfium.PdfDocument.new()
        for image_file in images_list:
            try:
                pdf_image = pdfium.PdfImage.new(output_pdf)
                pdf_image.load_jpeg(image_file)
                width, height = pdf_image.get_size()
                # since render size increased by 2, decrease by same amount
                width = width / 2
                height = height / 2

                matrix = pdfium.PdfMatrix().scale(width, height)
                pdf_image.set_matrix(matrix)

                page = output_pdf.new_page(width, height)
                page.insert_obj(pdf_image)
                page.gen_content()
                page.close()
                pdf_image.close()
                pages_scanned += 1
            except Exception as img_err:
                print_color(f"Error adding image to PDF: {img_err}", "Red")

        output_pdf.save(output_pdf_path, version=pdf_version)
        output_pdf.close()
        file_size = get_file_size(output_pdf_path)
        print(f"{output_pdf_path=} {file_size=}")
    except Exception as err:
        print_color(f"Failed to save PDF: {err}", "Red")

    return pages_scanned


def _add_suffix(filename):
    """Adds output suffix to given file name"""
    extension = "pdf"
    suffix = "_output"
    if "." in filename:
        base_name, extension = filename.rsplit(".", 1)
    else:
        base_name = filename
    # Add the suffix to the base name
    new_base_name = base_name + suffix
    # Combine the new base name and original extension to form the new filename
    new_filename = new_base_name + "." + extension if extension else new_base_name
    return new_filename


def _calc_energy_savings(pages_scanned):
    """
    Calculate energy savings generated by preventing the printing and scanning
    Approx energy required for production of 1 A4 sheet of paper = 50 Watt Hours

    Sources:
    https://www.apc.org/sites/default/files/SustainableITtips5_0.pdf
    https://www.lowtechmagazine.com/what-is-the-embodied-energy-of-materials.html

    Energy per capita usage: https://ourworldindata.org/grapher/per-capita-energy-use?tab=table
    """

    energy_req_for_one_page = 50
    energy_saved = pages_scanned * energy_req_for_one_page

    if energy_saved < 1000:
        energy_saved = f"{energy_saved} Watt hours"
    elif energy_saved < 1000000:
        energy_saved = energy_saved / 1000
        energy_saved = f"{energy_saved:.2f} kilo Watt hours"
    else:
        energy_saved = energy_saved / 1000000
        energy_saved = f"{energy_saved:.2f} Mega Watt hours"

    savings = f"\nYou just saved {energy_saved} energy by not printing \
{pages_scanned} pages of paper!\n"
    if pages_scanned > 0:
        print_color(savings, "Green")


def convert_images_to_pdf(
    input_image_list,
    image_quality,
    askew,
    black_and_white,
    blur,
    contrast,
    sharpness,
    brightness
):
    """Converts all image files in a folder to PDF"""
    images_list = []
    output_pdf_path = None
    if input_image_list:
        # Output pdf name will be the fetched from first Image's name
        output_pdf_path = os.path.splitext(input_image_list[0])[0] + "_output.pdf"
        for image_path in input_image_list:
            if files_exists(image_path):
                try:
                    image = Image.open(image_path)
                    image = image.convert("RGB")

                    # reduce image quality a little bit
                    image = reduce_image_quality(image, image_quality)

                    # Rotate every image by a small random angle
                    if askew:
                        image = rotate_image(image, random.uniform(-0.75, 0.75))

                    # Make image black and white like a photocopy
                    if black_and_white:
                        image = black_and_white_image(image)

                    # Make image blurry
                    if blur:
                        image = blur_image(image)
                    
                    # change image contrast
                    if contrast != 1.0:
                        image = change_contrast(image, contrast)
                    
                    # change image sharpness
                    if sharpness != 1.0:
                        image = change_sharpness(image, sharpness)
                        
                    # change image brightness
                    if brightness != 1.0:
                        image = change_brightness(image, brightness)

                    image = _change_image_to_byte_buffer(image)
                    images_list.append(image)
                except Exception as err:
                    print_color(f"Error converting file {image_path} :- {err}", "Red")

        pages_scanned = _save_image_obj_to_pdf(images_list, output_pdf_path)
        _calc_energy_savings(pages_scanned)
    return output_pdf_path


def convert_pdf_to_scanned(pdf_list, image_quality, askew, black_and_white, blur, contrast, sharpness, brightness):
    """
    Converts PDF files into scanned PDF files
    """
    output_file_list = []
    pages_scanned = 0
    for pdf_path in pdf_list:
        if files_exists(pdf_path):
            try:
                output_path = _add_suffix(pdf_path)
                images = _convert_pdf_pages_to_jpg_list(
                    pdf_path, image_quality, askew, black_and_white, blur, contrast, sharpness, brightness
                )
                pages_scanned += _save_image_obj_to_pdf(images, output_path)
                if images and pages_scanned:
                    output_file_list.append(output_path)
            except Exception as err:
                print_color(f"Error converting file {pdf_path} :- {err}", "Red")

    _calc_energy_savings(pages_scanned)
    return output_file_list


def print_version():
    """prints the version number of the module"""
    version = metadata.version("look-like-scanned")
    print_color(f"Scanner version: {version}", "Green")


def find_matching_files(input_folder, file_type_list, recurse=False, sort_key=None):
    """
    Find files in the given input folder and filter only matching file types.
    If recurse is True, this method will identify all matching files in all subdirectories.
    """
    files_list = []
    try:
        path = Path(input_folder)
        for file in path.iterdir():
            if file.is_file():
                # checks if file in given folder contains expected file types
                sfx = file.suffix.lower().lstrip(".")
                file_in_list = (file.name in file_type_list) or (sfx in file_type_list)
                if file_in_list:
                    files_list.append(str(file.absolute()))
            elif recurse and file.is_dir():
                files_list.extend(find_matching_files(file, file_type_list, recurse))
    except FileNotFoundError:
        print_color(f"Input folder not found: {input_folder}", "red")
    except PermissionError:
        print_color(f"Permission denied: {input_folder}", "red")
    except Exception as err:
        print_color(f"Error when searching for files: {err}", "red")

    # Sort the list of files if sorting is requested by user
    if sort_key:
        files_list.sort(key=sort_key)
    # if not, return files based on the order returned by the OS
    return files_list


def sort_by_top_level_directory(path):
    """Method to help sort file paths based on level"""
    directories = path.split(os.path.sep)
    return len(directories)


def convert_and_save(files_list, doc_type, quality, askew, black_and_white, blur, contrast, sharpness, brightness):
    """Convert input files into necessary output document format"""
    pdf_path = None

    print_color(f"\nMatching Files Found: {len(files_list)}", "Blue")
    pretty_print(files_list)

    # Convert the files found into output files
    if doc_type == "image":
        pdf_path = convert_images_to_pdf(
            files_list, quality, askew, black_and_white, blur, contrast, sharpness, brightness
        )
    elif doc_type == "pdf":
        pdf_path = convert_pdf_to_scanned(
            files_list, quality, askew, black_and_white, blur, contrast, sharpness, brightness
        )
    else:
        print_color("Error: Unsupported file format!", "Red")

    if pdf_path:
        print("The Output PDF files saved at:")
        pretty_print(pdf_path)
    else:
        print_color("No matching files found. No output documents generated!\n", "Red")


def main():
    """Get input arguments and run the script"""
    print_version()
    args = parse_args()

    # Gather input arguments from command-line
    input_folder = get_input_folder(args)
    quality = get_quality(args)
    askew = get_askew(args)
    recurse = get_recurse(args)
    black_and_white = get_blackandwhite(args)
    blur = get_blur(args)
    contrast = get_contrast(args)
    sharpness = get_sharpness(args)
    brightness = get_brightness(args)
    sort_key = get_sort_key(args)
    doc_type, file_type_list = get_file_type(args)

    print_color(
        f"{quality=} {recurse=} {askew=} "
        f"{black_and_white=} {blur=} {contrast=} "
        f"{sharpness=} {brightness=} {doc_type=} "
        f"{sort_key=} {file_type_list=}",
        "Cyan",
    )

    # Gather the input files based on the arguments
    files_list = find_matching_files(input_folder, file_type_list, recurse, sort_key)
    # Sort file paths so output gets saved in top level directory
    files_list = sorted(files_list, key=sort_by_top_level_directory)

    # Convert input files to look like scanned
    convert_and_save(files_list, doc_type, quality, askew, black_and_white, blur, contrast, sharpness, brightness)


if __name__ == "__main__":
    main()
