import os, io
import random
import argparse
from PIL import Image
import pypdfium2 as pdfium

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input_folder", help="The input folder to read files.")
parser.add_argument("-f", "--file_type_or_name", help="The file types to process or file name to process.")
parser.add_argument("-q", "--file_quality", help="The quality of the converted output files.")

SUPPORTED_IMAGES = [".jpg", ".png", ".jpeg", ".webp"]
SUPPORTED_DOCS = [".pdf", ".PDF"]


def get_args(argument_name):
    """
    Gets the input folder from the command-line argument.
    If no input folder provided, returns the current working directory.
    """

    args = parser.parse_args()

    if argument_name == "folder":
        return args.input_folder if args.input_folder else os.getcwd()
    if argument_name == "quality":
        return int(args.file_quality) if args.file_quality else 98
    if argument_name == "file_type":
        if args.file_type_or_name:
            file_type = args.file_type_or_name.lower()
            if file_type == "image":
                return ("image", SUPPORTED_IMAGES)
            elif any(ext.endswith(file_type) for ext in SUPPORTED_IMAGES):
                return ("image", [args.file_type_or_name])
            elif any(ext.endswith(file_type) for ext in SUPPORTED_DOCS):
                return ("pdf", [args.file_type_or_name])
            else:
                return (None, None)
        else:
            return ("pdf", SUPPORTED_DOCS)


def reduce_image_quality(image, quality=100, format='JPEG'):
    """Reduce quality of a given image object"""
    img_byte_array = io.BytesIO()
    # Save the image to the in-memory file object
    image.save(img_byte_array, quality=quality, format=format, subsampling=0)

    # Rewind the file object to the beginning
    img_byte_array.seek(0)
    # Open the image from the in-memory file object
    reduced_image = Image.open(img_byte_array)
    return reduced_image


def change_image_to_byte_buffer(image, format='JPEG'):
    # Save the image data to an in-memory file-like object
    img_byte_array = io.BytesIO()
    image.save(img_byte_array, format=format)
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
        image = change_image_to_byte_buffer(image)
        images_list.append(image)
    
    save_image_obj_to_pdf(images_list, output_pdf_path, pdf_version=17)
    return output_pdf_path


def rotate_image(image, angle):
    """Rotate PIL Image object with given angle value"""
    rotated_image = image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
    return rotated_image


def convert_pdf_pages_to_jpg_list(pdf_path, image_quality=100, askew=True):
    images_list = []
    doc = pdfium.PdfDocument(pdf_path)
    for i in range(len(doc)):
        page = doc[i]
        bitmap = page.render(scale=1)  # 72dpi resolution
        image = bitmap.to_pil()

        # reduce image quality a little bit
        image = reduce_image_quality(image, image_quality)
        image = image.convert("RGB")

        # Rotate every image by a small random angle
        if askew:
            angle = random.uniform(-0.75, 0.75)
            image = rotate_image(image, angle)
        image = change_image_to_byte_buffer(image)
        images_list.append(image)
        page.close()
    doc.close()
    return images_list


def save_image_obj_to_pdf(images_list, output_pdf_path, pdf_version=17):
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
    output_file_list = []
    for pdf_path in pdf_list:
        output_path = pdf_path.replace(".pdf", "_output.pdf")
        images = convert_pdf_pages_to_jpg_list(pdf_path, image_quality, askew=True)
        save_image_obj_to_pdf(images, output_path)
        output_file_list.append(output_path)
    return output_file_list


def main():
    """Get input arguments and run the script"""

    input_folder = get_args("folder")
    quality = get_args("quality")
    doc_type, file_type_list = get_args("file_type")
    print(f"{input_folder=} {quality=} {doc_type=} {file_type_list=}")
    pdf_path = os.path.join(input_folder, "Output.pdf")
    files_list = []
    for file_name in os.listdir(input_folder):
        if any(file_name.endswith(ext) for ext in file_type_list):
            files_list.append(os.path.join(input_folder, file_name))

    print(f"Processing files: {files_list}")
    if doc_type == "image":
        pdf_path = convert_images_to_pdf(files_list, quality)
    if doc_type == "pdf":
        pdf_path = convert_pdf_to_scanned(files_list, quality)

    print(f"The Output PDF file is saved at {pdf_path}")


if __name__ == "__main__":
    main()
