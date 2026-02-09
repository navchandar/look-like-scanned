"""Script to test scanner package"""

import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pypdfium2 as pdfium
import pytest
from PIL import Image

from scanner.scanner import DocumentScanner, get_target_files, human_size


# --- Fixtures for Setup/Teardown ---
@pytest.fixture
def test_env(tmp_path: Path):
    """
    Creates a temporary directory with dummy PDF and Image files.
    Returns the path to the temp directory.
    """
    # Create a dummy PDF
    pdf_path = tmp_path / "test_doc.pdf"
    pdf = pdfium.PdfDocument.new()
    pdf.new_page(100, 100)
    pdf.save(str(pdf_path), version=17)

    # Create a dummy Image
    img_path = tmp_path / "test_img.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)

    # Create a subdirectory with files (for recursion test)
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    (sub_dir / "sub_doc.pdf").write_bytes(pdf_path.read_bytes())

    return tmp_path


def is_valid_pdf(file_path):
    """Check if file is a PDF by reading header."""
    try:
        with open(file_path, "rb") as f:
            return f.read(4) == b"%PDF"
    except Exception:
        return False


# --- Unit Tests ---
def test_human_size():
    assert human_size(0) == "0.0 B"
    assert human_size(1024) == "1.0 KiB"
    assert human_size(1048576) == "1.0 MiB"


def test_get_target_files(test_env):
    """Test file discovery logic."""
    # Test 1: Find PDFs non-recursive
    files, mode = get_target_files(test_env, "pdf", recurse=False, sort_key="name")
    assert mode == "pdf"
    assert len(files) == 1
    assert files[0].name == "test_doc.pdf"

    # Test 2: Find Images
    files, mode = get_target_files(test_env, "image", recurse=False, sort_key="name")
    assert mode == "image"
    assert len(files) == 1
    assert files[0].name == "test_img.jpg"

    # Test 3: Recursive Search
    files, mode = get_target_files(test_env, "pdf", recurse=True, sort_key="name")
    assert len(files) == 2  # One in root, one in sub/

    # Test 4: Specific Filename
    files, mode = get_target_files(
        test_env, "test_doc.pdf", recurse=False, sort_key="name"
    )
    assert len(files) == 1
    assert files[0].name == "test_doc.pdf"


def test_get_target_files_sorting(test_env):
    """Test that file sorting by time and name works correctly."""
    # Create files with distinct timestamps
    file_a = test_env / "a_first.webp"
    file_b = test_env / "b_second.webp"

    file_a.touch()
    # Wait briefly to ensure timestamp difference
    time.sleep(0.5)
    file_b.touch()

    # Test Sort by mtime (Modified Time) - Default is Ascending (Oldest -> Newest)
    files, _ = get_target_files(test_env, "webp", recurse=False, sort_key="mtime")
    assert files == [file_a, file_b]

    #  Test Sort by Name
    files, _ = get_target_files(test_env, "webp", recurse=False, sort_key="name")
    assert files == [file_a, file_b]


def test_extension_filtering(test_env):
    """Test that -f 'png' finds only PNGs and ignores JPGs."""
    (test_env / "test.png").touch()
    # Ask specifically for png
    files, mode = get_target_files(test_env, "png", recurse=False, sort_key="name")

    assert mode == "image"
    assert len(files) == 1
    assert files[0].suffix == ".png"


class TestDocumentScanner:
    """Test the DocumentScanner class logic directly."""

    @pytest.fixture
    def mock_args(self):
        args = MagicMock()
        # Set defaults similar to argparse
        args.file_quality = 95
        args.askew = "yes"
        args.black_and_white = "no"
        args.blur = "no"
        args.contrast = 1.0
        args.sharpness = 1.0
        args.brightness = 1.0
        args.recurse = "no"
        args.sort_by = "name"
        return args

    def test_process_pdf(self, test_env, mock_args):
        """Test converting a single PDF."""
        scanner = DocumentScanner(mock_args)
        input_pdf = test_env / "test_doc.pdf"

        # Run conversion
        pages_processed = scanner.process_pdf(input_pdf)

        assert pages_processed == 1
        output_file = test_env / "test_doc_output.pdf"
        assert output_file.exists()
        assert is_valid_pdf(output_file)

    def test_process_images_to_one_pdf(self, test_env, mock_args):
        """Test combining images into a PDF."""
        scanner = DocumentScanner(mock_args)
        input_img = test_env / "test_img.jpg"

        # Create a second image to test combination
        img2 = test_env / "test_img2.jpg"
        shutil.copy(input_img, img2)

        images = [input_img, img2]
        pages_processed = scanner.process_images_to_one_pdf(images)

        assert pages_processed == 2
        # Output name should derive from first image
        output_file = test_env / "test_img_output.pdf"
        assert output_file.exists()
        assert is_valid_pdf(output_file)

    def test_apply_effects(self, mock_args):
        """Test image manipulation logic (Smoke test)."""
        scanner = DocumentScanner(mock_args)
        # Create a plain white image
        img = Image.new("RGB", (100, 100), "white")
        # Apply effects
        processed_img = scanner._apply_effects(img)
        assert isinstance(processed_img, Image.Image)
        assert processed_img.size == (102, 102)

        mock_args.askew = "no"
        scanner = DocumentScanner(mock_args)
        # Apply effects
        processed_img = scanner._apply_effects(img)
        assert isinstance(processed_img, Image.Image)
        assert processed_img.size == (100, 100)

    def test_rgba_transparency_conversion(self, test_env, mock_args):
        """Test that RGBA images (transparency) are converted to RGB without crashing."""
        scanner = DocumentScanner(mock_args)

        # Create an image with an Alpha channel (RGBA)
        rgba_path = test_env / "transparent.png"
        Image.new("RGBA", (100, 100), (255, 0, 0, 128)).save(rgba_path)

        # Process it
        pages = scanner.process_images_to_one_pdf([rgba_path])

        assert pages == 1
        output_pdf = test_env / "transparent_output.pdf"
        assert output_pdf.exists()

    def test_corrupt_pdf_handling(self, test_env, mock_args):
        """Test that the script handles corrupt PDFs gracefully without crashing."""
        scanner = DocumentScanner(mock_args)

        # Create a fake PDF (just a text file with .pdf extension)
        bad_pdf = test_env / "corrupt.pdf"
        bad_pdf.write_text("This is not a real PDF")

        # Should catch the exception internally and return 0 pages processed
        pages = scanner.process_pdf(bad_pdf)

        assert pages == 0
        # Ensure no output file was generated for the bad input
        assert not (test_env / "corrupt_output.pdf").exists()


# --- CLI Integration Tests ---
def run_cli(args):
    """Helper to run the script via subprocess."""
    # We use sys.executable to ensure we use the same python env running the tests
    cmd = [sys.executable, "-m", "scanner.scanner"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def test_cli_help():
    result = run_cli(["-h"])
    assert result.returncode == 0
    assert "Convert PDF/Images" in result.stdout


def test_cli_convert_pdf(test_env):
    """Test standard PDF conversion via CLI."""
    result = run_cli(["-i", str(test_env), "-f", "pdf"])
    assert result.returncode == 0
    assert "Files Found: 1" in result.stdout
    assert (test_env / "test_doc_output.pdf").exists()


def test_cli_convert_image(test_env):
    """Test image conversion via CLI."""
    result = run_cli(["-i", str(test_env), "-f", "image"])
    assert result.returncode == 0
    assert "Files Found: 1" in result.stdout
    assert (test_env / "test_img_output.pdf").exists()


def test_cli_no_files_found(test_env):
    """Test CLI behavior when no matching files exist."""
    # Search for non-existent PNGs
    result = run_cli(["-i", str(test_env), "-f", ".png", "-r", "no"])
    assert result.returncode == 0
    assert "No matching files found" in result.stdout


def test_cli_energy_savings_output(test_env):
    """Test that energy savings message is printed."""
    result = run_cli(["-i", str(test_env), "-f", "pdf"])
    assert "You just saved" in result.stdout
