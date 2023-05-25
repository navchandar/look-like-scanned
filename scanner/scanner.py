#!/usr/bin/env python
"""Module to convert PDF/Images to look like they were scanned"""

import os
import io
import random
import argparse
from PIL import Image
import pypdfium2 as pdfium

parser = argparse.ArgumentParser()
parser.add_argument(
    "-i", "--input_folder", help="The input folder to read files from and convert"
)
parser.add_argument(
    "-f",
    "--file_type_or_name",
    help="The file types to process or file name to process.",
)
parser.add_argument(
    "-q", "--file_quality", help="The quality of the converted output files."
)

SUPPORTED_IMAGES = [".jpg", ".png", ".jpeg", ".webp"]
SUPPORTED_DOCS = [".pdf", ".PDF"]


def _get_args(argument_name):
    """
    Gets the input folder from the command-line argument.
    If no input folder provided, returns the current working directory.
    """

    args = parser.parse_args()
    if not argument_name:
        return ""
    if argument_name == "folder":
        return args.input_folder if args.input_folder else os.getcwd()
    if argument_name == "quality":
        return int(args.file_quality) if args.file_quality else 98
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
            match = ("pdf", SUPPORTED_DOCS)
        return match


def reduce_image_quality(image, quality=100, compression="JPEG"):
    """Reduce quality of a given image object"""
    img_byte_array = io.BytesIO()
    # Save the image to the in-memory file object
    image.save(img_byte_array, quality=quality, format=compression, subsampling=0)

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
    image.save(img_byte_array, format=compression)
    # Reset the file position to the beginning
    img_byte_array.seek(0)
    return img_byte_array


def convert_images_to_pdf(input_image_list, image_quality):
    """Converts all image files in a folder to PDF"""
    images_list = []

    output_pdf_path = os.path.splitext(input_image_list[0])[0] + "_output.pdf"
    for image_path in input_image_list:
        image = Image.open(image_path)
        # reduce image quality a little bit
        image = reduce_image_quality(image, image_quality)
        image = image.convert("RGB")
        image = _change_image_to_byte_buffer(image)
        images_list.append(image)

    _save_image_obj_to_pdf(images_list, output_pdf_path, pdf_version=17)
    return output_pdf_path


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
        bitmap = page.render(scale=1)  # 72dpi resolution
        image = bitmap.to_pil()

        # reduce image quality a little bit
        image = reduce_image_quality(image, image_quality)
        image = image.convert("RGB")

        # Rotate every image by a small random angle
        if askew:
            angle = random.uniform(-0.75, 0.75)
            image = rotate_image(image, angle)
        image = _change_image_to_byte_buffer(image)
        images_list.append(image)
        page.close()
    doc.close()
    return images_list


def _save_image_obj_to_pdf(images_list, output_pdf_path, pdf_version=17):
    """
    Save image objects into output pdf
    """
    output_pdf = pdfium.PdfDocument.new()
    for image_file in images_list:
        pdf_image = pdfium.PdfImage.new(output_pdf)
        pdf_image.load_jpeg(image_file)
        width, height = pdf_image.get_size()

        matrix = pdfium.PdfMatrix().scale(width, height)
        pdf_image.set_matrix(matrix)

        page = output_pdf.new_page(width, height)
        page.insert_obj(pdf_image)
        page.gen_content()
        page.close()
        pdf_image.close()

    output_pdf.save(output_pdf_path, version=pdf_version)
    output_pdf.close()


def convert_pdf_to_scanned(pdf_list, image_quality):
    """
    Converts PDF files into scanned PDF files
    """
    output_file_list = []
    for pdf_path in pdf_list:
        output_path = pdf_path.replace(".pdf", "_output.pdf")
        images = _convert_pdf_pages_to_jpg_list(pdf_path, image_quality, askew=True)
        _save_image_obj_to_pdf(images, output_path)
        output_file_list.append(output_path)
    return output_file_list


def main():
    """Get input arguments and run the script"""

    # Gather input arguments from command-line
    input_folder = _get_args("folder")
    quality = _get_args("quality")
    doc_type, file_type_list = _get_args("file_type")
    print(f"{input_folder=} {quality=} {doc_type=} {file_type_list=}")

    # Gathe input files based on the arguments
    pdf_path = None
    files_list = []
    for file_name in os.listdir(input_folder):
        if any(file_name.endswith(ext) for ext in file_type_list):
            files_list.append(os.path.join(input_folder, file_name))

    # Convert files into output
    print(f"Processing files: {files_list}")
    if doc_type == "image":
        pdf_path = convert_images_to_pdf(files_list, quality)
    elif doc_type == "pdf":
        pdf_path = convert_pdf_to_scanned(files_list, quality)

    if pdf_path:
        print(f"The Output PDF file is saved at {pdf_path}")
    else:
        print("No valid file type found. No output documents generated")


if __name__ == "__main__":
    main()
