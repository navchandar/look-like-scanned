#!/usr/bin/env python
"""Module to convert PDF/Images to look like they were scanned"""

import os
import io
import random
import argparse
from pprint import pprint
import pypdfium2 as pdfium
from PIL import Image, ImageEnhance

SUPPORTED_IMAGES = [".jpg", ".png", ".jpeg", ".webp"]
SUPPORTED_DOCS = [".pdf", ".PDF"]
CHOICES = ["y", "yes", "n", "no"]


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
        help="The file types to process or file name to process. Valid value - image, pdf, file names (default: pdf)",
    )
    parser.add_argument(
        "-q",
        "--file_quality",
        type=int,
        choices=range(50, 101, 5),
        default=95,
        help="The quality of the converted output files. Valid range - 50 to 100 increment in steps of 5 (default: 95)",
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

    return parser.parse_args()


def get_argument(argument_name):
    """
    Gets the input folder from the command-line argument.
    If no input folder provided, returns the current working directory.
    """
    args = parse_args()
    if argument_name == "folder":
        input_folder = os.getcwd()
        if args.input_folder:
            input_folder = args.input_folder
        else:
            print("Defaulting to current directory")
        input_folder = os.path.abspath(input_folder)

        # check if folder path exists
        if os.path.exists(input_folder):
            print(f"Processing files from {input_folder=}")
        else:
            print(f"Error: Input folder path not found: {input_folder}")
        return input_folder

    if argument_name == "quality":
        return int(args.file_quality) if args.file_quality else 95

    if argument_name == "askew":
        return args.askew.lower().startswith("y") if args.askew else True

    if argument_name == "recurse":
        return args.recurse.lower().startswith("y") if args.recurse else True

    if argument_name == "file_type":
        match = (None, None)
        if args.file_type_or_name:
            file = args.file_type_or_name.lower()
            if file == "image":
                match = ("image", SUPPORTED_IMAGES)
            elif any(f.endswith(file) or file.endswith(f) for f in SUPPORTED_IMAGES):
                match = ("image", [args.file_type_or_name])
            elif any(f.endswith(file) or file.endswith(f) for f in SUPPORTED_DOCS):
                match = ("pdf", [args.file_type_or_name])
            else:
                print("Defaulting to find pdf files")
        else:
            match = ("pdf", SUPPORTED_DOCS)
        return match


def human_size(num, suffix="B"):
    """Return file size in a human readable format"""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def get_file_size(file_path):
    """Get file size for a given file path"""
    return human_size(os.stat(file_path).st_size)


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
        angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255)
    )
    return rotated_image


def _convert_pdf_pages_to_jpg_list(pdf_path, image_quality=100, askew=True):
    """
    Reads given pdf file and reads all pages and converts them to image objects
    """
    images_list = []
    doc = pdfium.PdfDocument(pdf_path)
    for page in doc:
        # increase render resolution for better scanned image quality
        bitmap = page.render(scale=2)
        image = bitmap.to_pil()

        # Reduce image quality a little bit
        image = reduce_image_quality(image, image_quality)
        image = image.convert("RGB")

        # increase brightness a little bit
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(random.uniform(1.01, 1.02))

        # Rotate every image by a small random angle
        if askew:
            image = rotate_image(image, random.uniform(-0.55, 0.55))

        image = _change_image_to_byte_buffer(image)
        images_list.append(image)
        page.close()
    doc.close()
    return images_list


def _save_image_obj_to_pdf(images_list, output_pdf_path, pdf_version=17):
    """
    Save image objects into output pdf
    """
    pages_scanned = 0
    output_pdf = pdfium.PdfDocument.new()
    for image_file in images_list:
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

    output_pdf.save(output_pdf_path, version=pdf_version)
    output_pdf.close()
    file_size = get_file_size(output_pdf_path)
    print(f"{output_pdf_path=} {file_size=}")
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

    savings = f"You just saved {energy_saved} energy by avoiding printing {pages_scanned} pages of paper!"
    print(savings)


def convert_images_to_pdf(input_image_list, image_quality, askew):
    """Converts all image files in a folder to PDF"""
    images_list = []

    # Output pdf name will be the fetched from first Image's name
    output_pdf_path = os.path.splitext(input_image_list[0])[0] + "_output.pdf"
    for image_path in input_image_list:
        try:
            image = Image.open(image_path)
            # reduce image quality a little bit
            image = reduce_image_quality(image, image_quality)
            image = image.convert("RGB")

            # Rotate every image by a small random angle
            if askew:
                image = rotate_image(image, random.uniform(-0.75, 0.75))

            image = _change_image_to_byte_buffer(image)
            images_list.append(image)
        except Exception as e:
            print(f"Error converting file {image_path} :-", e)

    pages_scanned = _save_image_obj_to_pdf(images_list, output_pdf_path, pdf_version=17)
    _calc_energy_savings(pages_scanned)
    return output_pdf_path


def convert_pdf_to_scanned(pdf_list, image_quality, askew):
    """
    Converts PDF files into scanned PDF files
    """
    output_file_list = []
    pages_scanned = 0
    for pdf_path in pdf_list:
        try:
            output_path = _add_suffix(pdf_path)
            images = _convert_pdf_pages_to_jpg_list(pdf_path, image_quality, askew)
            pages_scanned += _save_image_obj_to_pdf(images, output_path)
            output_file_list.append(output_path)
        except Exception as e:
            print(f"Error converting file {pdf_path} :-", e)

    _calc_energy_savings(pages_scanned)
    return output_file_list


def find_matching_files(input_folder, file_type_list, recurse=False):
    """
    Find files in given input folder and filter only matching file types.
    If recurse is True, this method will identify all matching files in all sub directories.
    """
    files_list = []
    try:
        for file in os.listdir(input_folder):
            path = os.path.join(input_folder, file)
            if os.path.isfile(path) and any(
                file.endswith(ext) for ext in file_type_list
            ):
                files_list.append(path)
            if recurse and os.path.isdir(path):
                files_list.extend(find_matching_files(path, file_type_list, recurse))
    except Exception as e:
        print("Error when searching for files :-", e)
    return files_list


def sort_by_top_level_directory(path):
    """Method to help sort file paths based on level"""
    directories = path.split(os.path.sep)
    return len(directories)


def main():
    """Get input arguments and run the script"""

    # Gather input arguments from command-line
    input_folder = get_argument("folder")
    quality = get_argument("quality")
    askew = get_argument("askew")
    recurse = get_argument("recurse")
    doc_type, file_type_list = get_argument("file_type")
    print(f"{quality=} {recurse=} {askew=} {doc_type=} {file_type_list=}")

    # Gather the input files based on the arguments
    files_list = find_matching_files(input_folder, file_type_list, recurse)
    # Sort file paths so output gets saved in top level directory
    files_list = sorted(files_list, key=sort_by_top_level_directory)

    print(f"Matching Files Found: {len(files_list)}")
    pprint(files_list)

    # Convert the files found into output files
    pdf_path = None
    if doc_type == "image":
        pdf_path = convert_images_to_pdf(files_list, quality, askew)
    elif doc_type == "pdf":
        pdf_path = convert_pdf_to_scanned(files_list, quality, askew)
    else:
        print("Error: Unsupported file format!")

    if pdf_path:
        pprint(f"The Output PDF files saved at {pdf_path}")
    else:
        print("No valid file type found. No output documents generated")


if __name__ == "__main__":
    main()
