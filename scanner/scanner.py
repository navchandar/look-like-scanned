#!/usr/bin/env python
"""
Module to convert PDF/Images to look like they were scanned.
"""
import argparse
import io
import os
import random
from importlib import metadata
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pypdfium2 as pdfium
from colorama import Fore, Style, init
from PIL import Image, ImageEnhance, ImageFilter

# Initialize colorama
init()

# Constants
SUPPORTED_IMAGES = {".jpg", ".png", ".jpeg", ".webp"}
SUPPORTED_DOCS = {".pdf"}
YES_VALUES = {"y", "yes", "t", "true", "on", "1"}
CHOICES = ["y", "n", "yes", "no", "true", "false"]


def print_color(text: str, color: str = "white") -> None:
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
    print(f"{color_map.get(color.lower(), Fore.RESET)}{text}{Style.RESET_ALL}")


def human_size(size_in_bytes: int) -> str:
    """Return human readable file size."""
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if abs(size_in_bytes) < 1024.0:
            return f"{size_in_bytes:3.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PiB"


def print_version():
    """Prints the version of the script. Version might fail if not installed as package"""
    try:
        version = metadata.version("look-like-scanned")
        print_color(f"Scanner version: {version}", "green")
    except:
        pass


def parse_arguments() -> argparse.Namespace:
    """Parses command line arguments and returns the parser Namespace object."""
    parser = argparse.ArgumentParser(
        description="Convert PDF/Images to look like scanned documents."
    )

    parser.add_argument(
        "-i",
        "--input_folder",
        type=str,
        help="Input folder to read files from. Default: current directory",
    )
    parser.add_argument(
        "-f",
        "--file_type_or_name",
        type=str,
        default="pdf",
        help="File types or File name to process. Valid value - image, pdf, specific file names. Default: pdf",
    )
    parser.add_argument(
        "-q",
        "--file_quality",
        type=int,
        default=95,
        choices=range(50, 101, 5),
        help="Quality of converted output. Valid range - 50 to 100. Default: 95",
    )
    parser.add_argument(
        "-a",
        "--askew",
        type=str,
        default="yes",
        choices=CHOICES,
        help="Make output documents slightly askew or slightly tilted. Default: yes",
    )
    parser.add_argument(
        "-b",
        "--black_and_white",
        type=str,
        default="no",
        choices=CHOICES,
        help="Make output documents black and white. Make it look like a photocopy. Default: no",
    )
    parser.add_argument(
        "-l",
        "--blur",
        type=str,
        default="no",
        choices=CHOICES,
        help="Make output documents look a little bit blurry. Default: no",
    )
    parser.add_argument(
        "-c",
        "--contrast",
        type=float,
        default=1.0,
        help="A factor of 0.0 gives a solid gray image. \
A factor of 1.0 gives the original image. \
Greater values increase the contrast of the image. Default: 1.0",
    )
    parser.add_argument(
        "-sh",
        "--sharpness",
        type=float,
        default=1.0,
        help="A factor of 0.0 gives a blurred image image. \
A factor of 1.0 gives the original image. \
Greater values increase the sharpness of the image. Default: 1.0",
    )
    parser.add_argument(
        "-br",
        "--brightness",
        type=float,
        default=1.0,
        help="A factor of 0.0 gives a black image.\
A factor of 1.0 gives the original image. \
Greater values increase the brightness of the image. Default: 1.0",
    )
    parser.add_argument(
        "-r",
        "--recurse",
        type=str,
        default="no",
        choices=CHOICES,
        help="Recurse in all sub folders to find matching files to convert them. Default: no",
    )
    parser.add_argument(
        "-s",
        "--sort_by",
        type=str,
        default="name",
        choices=["name", "ctime", "mtime", "none"],
        help="Sort the list of files in order by name or creation time or modified time. Default: name",
    )

    return parser.parse_args()


def get_target_files(
    input_dir: Path, filter_arg: str, recurse: bool, sort_key: str
) -> Tuple[List[Path], str]:
    """
    Scans directory for matching files based on input arguments.
    If no extension, assume partial match name, default to pdf unless logic dictates otherwise
    Returns: (List of file paths, and 'mode' [image|pdf])
    """
    if not input_dir.exists():
        print_color(f"Error: Input folder path not found: {input_dir}", "red")
        return [], "pdf"

    # Determine processing mode - default to PDF
    mode = "pdf"
    target_extensions = SUPPORTED_DOCS

    # Check if filter_arg is a keyword ('image', 'pdf') or a filename
    if filter_arg.lower() == "image":
        mode = "image"
        target_extensions = SUPPORTED_IMAGES
    elif filter_arg.lower() == "pdf":
        mode = "pdf"
        target_extensions = SUPPORTED_DOCS
    else:
        # If it is a specific filename or extension
        suffix = Path(filter_arg).suffix.lower()
        if suffix in SUPPORTED_IMAGES:
            mode = "image"
            target_extensions = {suffix}
        elif suffix in SUPPORTED_DOCS:
            mode = "pdf"
            target_extensions = {suffix}

    print(f"Processing files from {input_dir} with mode={mode}...")

    files = []
    pattern = "**/*" if recurse else "*"

    try:
        for p in input_dir.glob(pattern):
            if p.is_file():
                # Check extension match
                is_ext_match = p.suffix.lower() in target_extensions

                # Check exact name match if filter_arg is not a generic keyword
                is_name_match = True
                if filter_arg.lower() not in [
                    "image",
                    "pdf",
                ] and not filter_arg.startswith("."):
                    is_name_match = p.name == filter_arg

                if is_ext_match and is_name_match:
                    files.append(p)
    except Exception as e:
        print_color(f"Error searching files: {e}", "red")

    # Sort Logic
    if sort_key != "none":
        if sort_key == "ctime":
            files.sort(key=lambda f: f.stat().st_ctime)
        elif sort_key == "mtime":
            files.sort(key=lambda f: f.stat().st_mtime)
        else:  # name
            files.sort(key=lambda f: f.name)

        # Secondary sort by directory depth to keep folders together during recursion
        files.sort(key=lambda f: len(f.parts))

    return files, mode


class DocumentScanner:
    """Handles the conversion of digital documents/images into 'scanned' PDFs"""

    def __init__(self, args: argparse.Namespace):
        self.quality = args.file_quality
        self.askew = args.askew.lower() in YES_VALUES
        self.black_and_white = args.black_and_white.lower() in YES_VALUES
        self.blur = args.blur.lower() in YES_VALUES
        self.contrast = args.contrast
        self.sharpness = args.sharpness
        self.brightness = args.brightness
        self.recurse = args.recurse.lower() in YES_VALUES
        self.sort_by = args.sort_by.lower()

    def _apply_effects(self, image: Image.Image) -> Image.Image:
        """Applies configured visual effects to a single image object."""

        # Reduce Image Quality (Simulate compression artifacts)
        img_buffer = io.BytesIO()
        image.save(img_buffer, quality=self.quality, format="JPEG")
        # Rewind the file object to the beginning
        img_buffer.seek(0)
        # Open the image from the in-memory file object
        image = Image.open(img_buffer).convert("RGB")

        # Random Brightness Jitter (Simulate scanner light fluctuation)
        jitter = random.uniform(1.01, 1.02)
        image = ImageEnhance.Brightness(image).enhance(jitter)

        # Rotation (Askew) by a small angle in any direction
        if self.askew:
            angle = random.uniform(-0.55, 0.55)
            image = image.rotate(
                angle,
                resample=Image.Resampling.BICUBIC,
                expand=True,
                fillcolor=(255, 255, 255),
            )

        # Black and White to look like a photocopy
        if self.black_and_white:
            image = image.convert("L")
            # Adjust the contrast level
            contrast = random.uniform(1.2, 1.5)
            image = ImageEnhance.Contrast(image).enhance(contrast)
            image = image.convert("RGB")

        # Blur slightly
        if self.blur:
            blur = random.uniform(1.1, 1.4)
            image = image.filter(ImageFilter.GaussianBlur(blur))

        # User Adjustments for contrast, sharpness, brightness
        if self.contrast != 1.0:
            image = ImageEnhance.Contrast(image).enhance(self.contrast)
        if self.sharpness != 1.0:
            image = ImageEnhance.Sharpness(image).enhance(self.sharpness)
        if self.brightness != 1.0:
            image = ImageEnhance.Brightness(image).enhance(self.brightness)

        return image

    def _save_images_to_pdf(
        self, images: List[Union[Image.Image, io.BytesIO]], output_path: Path
    ) -> int:
        """Saves a list of images to a single PDF."""
        if not images:
            return 0

        try:
            pdf = pdfium.PdfDocument.new()
            for img_obj in images:
                if isinstance(img_obj, Image.Image):
                    buf = io.BytesIO()
                    img_obj.save(buf, format="JPEG")
                    buf.seek(0)
                    img_data = buf
                else:
                    img_data = img_obj

                pdf_image = pdfium.PdfImage.new(pdf)
                pdf_image.load_jpeg(img_data)

                width, height = pdf_image.get_px_size()
                # Scale down because we render at 2x
                width, height = width / 2, height / 2

                matrix = pdfium.PdfMatrix().scale(width, height)
                pdf_image.set_matrix(matrix)

                page = pdf.new_page(width, height)
                page.insert_obj(pdf_image)
                page.gen_content()
                page.close()
                pdf_image.close()

            pdf.save(str(output_path), version=17)
            pdf.close()
            print(f"{output_path} ({human_size(output_path.stat().st_size)})")
            return len(images)

        except Exception as e:
            print_color(f"Failed to save PDF {output_path}: {e}", "red")
            return 0

    def process_pdf(self, file_path: Path) -> int:
        """Converts a real PDF into a scanned-look PDF (One-to-One)."""
        output_path = file_path.with_name(f"{file_path.stem}_output.pdf")
        images = []

        try:
            doc = pdfium.PdfDocument(str(file_path))
            if doc.get_formtype():
                doc.init_forms()

            for page in doc:
                bitmap = page.render(scale=2)
                pil_image = bitmap.to_pil().convert("RGB")
                processed_img = self._apply_effects(pil_image)
                images.append(processed_img)
                page.close()
            doc.close()

            return self._save_images_to_pdf(images, output_path)

        except Exception as e:
            print_color(f"Error processing PDF {file_path}: {e}", "red")
            return 0

    def process_images_to_one_pdf(self, image_paths: List[Path]) -> int:
        """Converts a list of images into a SINGLE scanned-look PDF (Many-to-One)."""
        if not image_paths:
            return 0

        # Output pdf name will be based on the first Image's name
        first_image = image_paths[0]
        output_path = first_image.with_name(f"{first_image.stem}_output.pdf")

        processed_images = []
        for img_path in image_paths:
            if img_path.exists():
                try:
                    with Image.open(img_path) as img:
                        img = img.convert("RGB")
                        processed_images.append(self._apply_effects(img))
                except Exception as e:
                    print_color(f"Skipping {img_path}: {e}", "red")

        return self._save_images_to_pdf(processed_images, output_path)

    @staticmethod
    def calculate_energy_savings(total_pages: int) -> None:
        """
        Calculate theoretical energy savings generated by preventing the printing and scanning
        Approx energy required for production of 1 A4 sheet of paper = 50 Watt Hours

        Sources:
        https://www.apc.org/sites/default/files/SustainableITtips5_0.pdf
        https://www.lowtechmagazine.com/what-is-the-embodied-energy-of-materials.html

        Energy per capita usage: https://ourworldindata.org/grapher/per-capita-energy-use?tab=table
        """

        if total_pages == 0:
            return
        energy_req_for_one_page = 50
        wh_saved = total_pages * energy_req_for_one_page

        if wh_saved < 1000:
            saved = f"{wh_saved} Wh"
        elif wh_saved < 1_000_000:
            saved = f"{wh_saved / 1000:.2f} kWh"
        else:
            saved = f"{wh_saved / 1_000_000:.2f} MWh"

        msg = f"\nYou just saved {saved} energy by not printing {total_pages} pages of paper!\n"
        print_color(msg, "green")


def main():
    """Get input arguments and run the script"""
    print_version()
    args = parse_arguments()

    # If Input folder not provided, default to current working directory
    input_folder = args.input_folder if args.input_folder else os.getcwd()
    input_path = Path(input_folder).resolve()

    # Initialize the DocumentScanner with the provided arguments
    scanner = DocumentScanner(args)

    # Fetch files list based on input arguments
    files_list, doc_type = get_target_files(
        input_path, args.file_type_or_name, scanner.recurse, scanner.sort_by
    )
    print_color(f"\nFiles Found: {len(files_list)}", "blue")
    if not files_list:
        print_color("No matching files found. No output documents generated!", "red")
        return

    # Process files
    total_pages = 0
    if doc_type == "image":
        # Combine all images into ONE output PDF
        total_pages += scanner.process_images_to_one_pdf(files_list)
    else:
        # Convert each PDF individually
        for pdf_file in files_list:
            total_pages += scanner.process_pdf(pdf_file)

    DocumentScanner.calculate_energy_savings(total_pages)


if __name__ == "__main__":
    main()
