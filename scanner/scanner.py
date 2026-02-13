#!/usr/bin/env python
"""
Module to convert PDF/Images to look like they were scanned.
"""
import argparse
import io
import os
import random
import textwrap
from importlib import metadata
from pathlib import Path
from typing import List, Tuple, Union

import pypdfium2 as pdfium
from colorama import Fore, Style, init
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

# Initialize colorama
init()

# Constants
YES_VALUES = {"y", "yes", "t", "true", "1"}
CHOICES = ["y", "n", "yes", "no", "true", "false"]
SUPPORTED_DOCS = {".pdf"}
SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".jp2", ".bmp"}

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    # add  ".heic",".heif" if pillow_heif is imported
    SUPPORTED_IMAGES.update({".heic", ".heif"})
except ImportError:
    pass


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
    msg = textwrap.dedent(
        f"""\
        Convert PDF/Images to look like scanned documents.
        Supported image formats: {', '.join(sorted(SUPPORTED_IMAGES))}
        Supported document formats: {', '.join(sorted(SUPPORTED_DOCS))}"""
    )
    usg = "Example: scanner -i /path/to/folder -f image -q 90 -a yes\
-b no -l yes -v yes -n 10 -c 1.2 -sh 1.3 -br 1.1 -r yes -s mtime"

    parser = argparse.ArgumentParser(
        description=msg, epilog=usg, formatter_class=argparse.RawTextHelpFormatter
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
        help="File types or File name to process.\
Valid value - image, pdf, specific file names. Default: pdf",
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
        "-v",
        "--variation",
        type=str,
        default="no",
        choices=CHOICES,
        help="Apply varying levels of blur/focus (depth of field effect). Default: no",
    )
    parser.add_argument(
        "-n",
        "--noise",
        type=int,
        default=0,
        choices=range(0, 101, 5),
        help="Add random noise to simulate imperfections (0-100). Default: 0",
    )
    parser.add_argument(
        "-c",
        "--contrast",
        type=float,
        default=1.0,
        help="A factor of 0.0 gives a solid gray image. \n\
A factor of 1.0 gives the original image. \n\
Greater values increase the contrast of the image. Default: 1.0",
    )
    parser.add_argument(
        "-sh",
        "--sharpness",
        type=float,
        default=1.0,
        help="A factor of 0.0 gives a blurred image image. \n\
A factor of 1.0 gives the original image. \n\
Greater values increase the sharpness of the image. Default: 1.0",
    )
    parser.add_argument(
        "-br",
        "--brightness",
        type=float,
        default=1.0,
        help="A factor of 0.0 gives a black image. \n\
A factor of 1.0 gives the original image. \n\
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
    Returns: (List of file paths, and 'mode' [image|pdf])
    """
    if not input_dir.exists():
        print_color(f"Error: Input folder path not found: {input_dir}", "red")
        return [], "pdf"

    # Setup Filter Logic
    mode = "pdf"
    target_extensions = set()
    specific_filename = None
    # If set, look for this exact file

    arg_lower = filter_arg.lower()

    # Helper to check if string looks like a supported extension (e.g. "jpg" or ".jpg")
    def clean_ext(val):
        return "." + val.lstrip(".")

    # Case A: Broad Keywords
    if arg_lower == "image":
        mode = "image"
        target_extensions = SUPPORTED_IMAGES
    elif arg_lower == "pdf":
        mode = "pdf"
        target_extensions = SUPPORTED_DOCS

    # Case B: User provided an extension (e.g. "png" or ".png")
    elif clean_ext(arg_lower) in SUPPORTED_IMAGES:
        mode = "image"
        target_extensions = {clean_ext(arg_lower)}
    elif clean_ext(arg_lower) in SUPPORTED_DOCS:
        mode = "pdf"
        target_extensions = {clean_ext(arg_lower)}

    # Case C: User provided a specific filename (e.g. "file.pdf")
    else:
        specific_filename = filter_arg
        # Deduce mode from the specific file's extension for processing later
        sfx = Path(filter_arg).suffix.lower()
        if sfx in SUPPORTED_IMAGES:
            mode = "image"
        elif sfx in SUPPORTED_DOCS:
            mode = "pdf"
        else:
            print_color(
                f"Error: The provided file name does not have a supported extension: {filter_arg}",
                "red",
            )
            return [], "pdf"

    print(f"Processing files from {input_dir} with mode={mode}...")

    # Scan Files in the folders
    files = []
    pattern = "**/*" if recurse else "*"

    try:
        for p in input_dir.glob(pattern):
            if p.is_file():
                match = False

                # STRICT MATCH: If user gave a specific filename, only match that name
                if specific_filename:
                    if p.name == specific_filename:
                        match = True

                # BROAD MATCH: match any file with the target extensions
                elif p.suffix.lower() in target_extensions:
                    match = True

                if match:
                    files.append(p)

    except Exception as e:
        print_color(f"Error searching files: {e}", "red")

    # Primary Sort: User preference (Name, Time)
    if sort_key != "none":  # dont sort at all if "none"
        if sort_key == "ctime":
            files.sort(key=lambda f: f.stat().st_ctime)
        elif sort_key == "mtime":
            files.sort(key=lambda f: f.stat().st_mtime)
        else:  # sort by name
            files.sort(key=lambda f: f.name)

    # Secondary Sort: Directory Depth
    # This keeps top-level files together in the final PDF if merging.
    files.sort(key=lambda f: len(f.parts))

    return files, mode


class DocumentScanner:
    """Handles the conversion of digital documents/images into 'scanned' PDFs"""

    def __init__(self, args: argparse.Namespace):
        self.quality = args.file_quality
        self.askew = args.askew.lower() in YES_VALUES
        self.black_and_white = args.black_and_white.lower() in YES_VALUES
        self.blur = args.blur.lower() in YES_VALUES
        self.blur_variation = args.variation.lower() in YES_VALUES
        self.noise_factor = args.noise
        self.contrast = args.contrast
        self.sharpness = args.sharpness
        self.brightness = args.brightness
        self.recurse = args.recurse.lower() in YES_VALUES
        self.sort_by = args.sort_by.lower()

    def _add_noise(self, image: Image.Image) -> Image.Image:
        """Adds random salt-and-pepper noise using pure Python/PIL."""
        if self.noise_factor == 0:
            return image

        width, height = image.size
        pixels = image.load()

        # Calculate number of noisy pixels (max 50% density)
        density = min(self.noise_factor / 200.0, 0.5)
        total_pixels = width * height
        noise_count = int(total_pixels * density)

        is_rgb = image.mode == "RGB"

        for _ in range(noise_count):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            # 50/50 chance of Salt (255) or Pepper (0)
            val = 255 if random.random() > 0.5 else 0

            if is_rgb:
                pixels[x, y] = (val, val, val)
            else:
                pixels[x, y] = val

        return image

    def _generate_gradient_mask(self, width: int, height: int) -> Image.Image:
        """Generates a gradient mask efficiently to simulate uneven focus for the blur variation effect"""
        # Create a small gradient and resize it to the image size for efficiency.
        # 256 size is enough for a smooth gradient
        mask = Image.new("L", (256, 256))

        direction = random.choice(["horizontal", "vertical", "diagonal"])

        # Draw gradient on small image
        draw = ImageDraw.Draw(mask)

        if direction == "horizontal":
            for x in range(256):
                draw.line([(x, 0), (x, 255)], fill=x)
        elif direction == "vertical":
            for y in range(256):
                draw.line([(0, y), (255, y)], fill=y)
        else:  # diagonal approximation
            for i in range(256):
                # Draw overlapping lines to simulate diagonal
                draw.line([(0, i), (i, 0)], fill=i)  # Top-Left dark
                draw.line([(i, 255), (255, i)], fill=255 - i)  # Bottom-right light

        # Resize to actual image dimensions
        return mask.resize((width, height), Image.Resampling.BILINEAR)

    def _add_blur_variation(self, image: Image.Image) -> Image.Image:
        """
        Simulates an uneven scanner lid by blurring one side of the image.
        """
        if not self.blur_variation:
            return image
        # Create blurred version
        blur_radius = random.uniform(2.0, 5.0)
        blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        # Create Gradient Mask
        mask = self._generate_gradient_mask(image.width, image.height)

        # Randomly invert mask to change direction of blur
        if random.random() > 0.5:
            mask = ImageOps.invert(mask)
        return Image.composite(blurred_image, image, mask)

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
        # Blur Variation (Uneven focus)
        image = self._add_blur_variation(image)
        # Add Noise if specified
        image = self._add_noise(image)

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
                    # Use quality to control image compression in the PDF as well
                    img_obj.save(buf, format="JPEG", quality=self.quality)
                    buf.seek(0)
                    img_data = buf
                else:
                    img_data = img_obj

                pdf_image = pdfium.PdfImage.new(pdf)
                pdf_image.load_jpeg(img_data)

                width, height = pdf_image.get_px_size()
                # Scale down because we render at 2x to improve quality
                # But PDF should be at original size
                width, height = width / 2, height / 2

                matrix = pdfium.PdfMatrix().scale(width, height)
                pdf_image.set_matrix(matrix)

                page = pdf.new_page(width, height)
                page.insert_obj(pdf_image)
                page.gen_content()
                page.close()
                pdf_image.close()

            # version 17 indicates a compatible PDF 1.7 format
            pdf.save(str(output_path), version=17)
            pdf.close()

            file_size = human_size(output_path.stat().st_size)
            print(f"Output: {output_path} ({file_size=})")
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
            # skip if file doesn't exist or is not a valid image
            if not img_path.exists():
                print_color(f"File not found, skipping: {img_path}", "red")
                continue

            try:
                with Image.open(img_path) as img:
                    # load image to catch file corruption/compression errors early
                    img.load()

                    # Get frames safely. Default to 1 if attribute missing
                    n_frames = getattr(img, "n_frames", 1)

                    for i in range(n_frames):
                        img.seek(i)

                        # Create a dedicated copy for this frame to prevents seek() issues
                        # this also allows per-page rotation
                        frame = img.copy()

                        # Apply EXIF rotation to this specific frame
                        try:
                            # use a try-except because some frames might lack EXIF data
                            frame = ImageOps.exif_transpose(frame)
                        except Exception:
                            pass

                        # Handle RGBA/P modes and transparency by compositing onto white background in PDF conversion
                        if frame.mode in ("RGBA", "LA") or (
                            frame.mode == "P" and "transparency" in frame.info
                        ):
                            temp_img = frame.convert("RGBA")
                            bg = Image.new("RGB", temp_img.size, (255, 255, 255))
                            bg.paste(temp_img, mask=temp_img.split()[3])
                            frame = bg
                        else:
                            frame = frame.convert("RGB")

                        processed_images.append(self._apply_effects(frame))

            except Exception as e:
                print_color(f"Skipping file {img_path.name}: {e}", "red")

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
