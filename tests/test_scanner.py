"""Script to test scanner package"""

import shutil
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pypdfium2 as pdfium
import pytest
from PIL import Image

from scanner.scanner import DocumentScanner, get_target_files, human_size

TEST_DIR = Path("tests")


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


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Delete all *_output*.pdf files in the given directory"""
    yield
    files = list(TEST_DIR.glob("*_output*.pdf"))
    for file in files:
        try:
            if Path(file).exists():
                Path(file).unlink()
            print(f"\nDeleted file: {file}")
        except Exception as e:
            print(f"\nFailed to delete {file}: {e}")


def _is_valid_pdf(file_path):
    """Check if file is a PDF by reading header."""
    try:
        with open(file_path, "rb") as f:
            return f.read(4) == b"%PDF"
    except:
        return False


class TestDocumentScanner:
    """Test the DocumentScanner class logic directly."""

    @pytest.fixture
    def mock_args(self) -> MagicMock:
        """Mock args with default values for testing. Adjust as needed for specific tests"""
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
        args.noise = 10
        args.blur_variation = "no"
        args.password = "kanbanery"
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
        assert _is_valid_pdf(output_file)

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
        assert _is_valid_pdf(output_file)

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

    def test_heic_processing(self, tmp_path, mock_args):
        """
        Verifies we can open, process, and save a real HEIC file.
        """
        # Locate the HEIC file
        heic_files = list(TEST_DIR.glob("*.heic"))
        heic_files += list(TEST_DIR.glob("*.heif"))
        if not heic_files:
            pytest.skip("No .heic files found in tests folder. Skipping test.")

        for input_file in heic_files:
            scanner = DocumentScanner(mock_args)

            # Process the file
            temp_input = tmp_path / input_file.name
            shutil.copy(input_file, temp_input)

            scanner.process_images_to_one_pdf([temp_input])

            # Validate ouput file
            output_pdf = tmp_path / f"{temp_input.stem}_output.pdf"
            assert output_pdf.exists(), "HEIC output PDF was not created"
            assert output_pdf.stat().st_size > 1000, "Output PDF seems too small/empty"

    def test_multipage_tiff_processing(self, tmp_path, mock_args):
        """
        Loops over ALL .tiff files in tests/.
        - If valid: Ensures all pages are extracted.
        - If invalid (e.g. JPEG2000): Ensures tool skips gracefully.
        """
        tiff_files = list(TEST_DIR.glob("*.tif*"))
        if not tiff_files:
            pytest.skip("No .tiff files found. Skipping test.")

        scanner = DocumentScanner(mock_args)

        for input_file in tiff_files:
            print(f"\nTesting file: {input_file.name}")

            # Determine if this file is valid
            is_valid_file = True
            expected_pages = 0

            try:
                with Image.open(input_file) as img:
                    # Force load to check for compression errors (KeyError 34712)
                    img.load()
                    expected_pages = getattr(img, "n_frames", 1)
            except Exception as e:
                print(f" -> Unsupported file format (Pillow cannot read it): {e}")
                is_valid_file = False

            # Step 2: Run the scanner on this file
            temp_input = tmp_path / input_file.name
            shutil.copy(input_file, temp_input)

            # Capture output to ensure no crashes
            with patch.object(
                scanner, "_save_images_to_pdf", side_effect=scanner._save_images_to_pdf
            ) as mock_save:
                # test call must NOT crash, even for bad files
                scanner.process_images_to_one_pdf([temp_input])

                if is_valid_file:
                    # ASSERTION FOR GOOD FILES
                    assert (
                        mock_save.called
                    ), f"Scanner should have processed valid file {input_file.name}"
                    processed_imgs = mock_save.call_args[0][0]
                    msg = f"Missed pages in {input_file.name}.\n\
                        {expected_pages=}, got {len(processed_imgs)}"
                    assert len(processed_imgs) == expected_pages, msg
                else:
                    # ASSERTION FOR BAD FILES
                    # Critical check to run without an Exception being raised.
                    if mock_save.called:
                        processed_imgs = mock_save.call_args[0][0]
                        msg = f"Scanner processed data from a broken file {input_file.name}? Expected 0 pages."
                        assert len(processed_imgs) == 0, msg

    def test_transparency_on_png(self, tmp_path, mock_args):
        """
        Verifies that transparent pixels turn WHITE, not BLACK.
        Uses a synthetic image to guarantee consistency and disables random effects.
        """
        # Disable all random effects to prevent flakiness
        mock_args.noise = 0
        mock_args.askew = "no"
        mock_args.blur = "no"
        mock_args.variation = "no"
        mock_args.file_quality = 100

        scanner = DocumentScanner(mock_args)

        # Generate a synthetic 50x50 fully transparent image
        input_file = tmp_path / "synthetic_transparent.png"
        img = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
        img.save(input_file)

        scanner.process_images_to_one_pdf([input_file])

        output_pdf = tmp_path / f"{input_file.stem}_output.pdf"
        assert output_pdf.exists()

        # Verify the generated PDF
        pdf = pdfium.PdfDocument(str(output_pdf))
        pil_image = pdf[0].render().to_pil()

        # Get actual dimensions of the rendered PDF page
        width, height = pil_image.size
        # Calculate the center point dynamically
        center_x = width // 2
        center_y = height // 2
        # Check the center pixel
        r, g, b = pil_image.getpixel((center_x, center_y))[:3]

        assert (
            r > 250 and g > 250 and b > 250
        ), f"Background turned dark ({r},{g},{b}). Transparency fix failed."


class TestEncryptedPDF:
    """Tests for Password Protected PDF handling."""

    @pytest.fixture
    def mock_args(self):
        args = MagicMock()
        # Default settings
        args.file_quality = 95
        args.askew = "no"
        args.black_and_white = "no"
        args.blur = "no"
        args.contrast = 1.0
        args.sharpness = 1.0
        args.brightness = 1.0
        args.recurse = "no"
        args.sort_by = "name"
        args.noise = 0
        args.blur_variation = "no"
        args.password = None
        return args

    def get_encrypted_file(self):
        # Locate the specific encrypted file
        files = list(TEST_DIR.glob("*Encrypted*.pdf"))
        if not files:
            pytest.skip("Encrypted PDF file not found.")
        return files[0]

    def test_cli_password_success(self, tmp_path, mock_args):
        """
        Scenario 1: User provides correct password via CLI flag (-p).
        The scanner should open it immediately without prompting.
        """
        input_file = self.get_encrypted_file()

        # SETUP: Provide correct password in args
        mock_args.password = "kanbanery"

        scanner = DocumentScanner(mock_args)
        temp_input = tmp_path / input_file.name
        shutil.copy(input_file, temp_input)

        # patch 'input' to ensure it is NEVER called. If it asks for input, test fails.
        with patch(
            "builtins.input", side_effect=Exception("Should not prompt!")
        ) as mock_input:
            pages = scanner.process_pdf(temp_input)

        # ASSERT successful conversion without any prompt
        assert pages > 0
        assert (tmp_path / f"{temp_input.stem}_output.pdf").exists()

    def test_interactive_password_success(self, tmp_path, mock_args):
        """
        Scenario 2: User provides NO password via CLI, but enters it when prompted.
        """
        input_file = self.get_encrypted_file()

        # SETUP: No password in args
        mock_args.password = None

        scanner = DocumentScanner(mock_args)
        temp_input = tmp_path / input_file.name
        shutil.copy(input_file, temp_input)

        # Mock the user typing the password and hitting Enter
        with patch("builtins.input", return_value="kanbanery") as mock_input:
            pages = scanner.process_pdf(temp_input)

        # ASSERT successful conversion after correct password entry
        assert pages > 0
        assert (tmp_path / f"{temp_input.stem}_output.pdf").exists()
        # Verify prompt was actually called
        mock_input.assert_called_once()

    def test_interactive_skip(self, tmp_path, mock_args):
        """
        Scenario 3: User doesn't know password and hits Enter to skip.
        """
        input_file = self.get_encrypted_file()
        mock_args.password = None

        scanner = DocumentScanner(mock_args)
        temp_input = tmp_path / input_file.name
        shutil.copy(input_file, temp_input)

        # Mock user hitting Enter (empty string)
        with patch("builtins.input", return_value="") as mock_input:
            pages = scanner.process_pdf(temp_input)

        # ASSERT no pages converted
        assert pages == 0
        assert not (tmp_path / f"{temp_input.stem}_output.pdf").exists()

    def test_wrong_password_retry_fail(self, tmp_path, mock_args):
        """
        Scenario 4: User types wrong password 3 times. Should eventually skip.
        """
        input_file = self.get_encrypted_file()
        mock_args.password = None

        scanner = DocumentScanner(mock_args)
        temp_input = tmp_path / input_file.name
        shutil.copy(input_file, temp_input)

        # Mock user typing "wrong" 3 times
        with patch(
            "builtins.input", side_effect=["wrong", "123", "abcd", "wrong"]
        ) as mock_input:
            pages = scanner.process_pdf(temp_input)

        # ASSERT no pages converted
        assert pages == 0
        assert not (tmp_path / f"{temp_input.stem}_output.pdf").exists()


# --- Unit Tests ---
def test_human_size():
    """Test method calculation"""
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


# --- CLI Integration Tests ---
def run_cli(args):
    """Helper to run the script via subprocess."""
    cmd = ["scanner"] + args + ["-p", "kanbanery"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print(f"\n[CLI STDOUT]\n{result.stdout}")
    print(f"\n[CLI STDERR]\n{result.stderr}")
    return result


CLI_TEST_CASES = [
    ("convert_multi_pdf", ["-i", TEST_DIR, "-f", "pdf"]),
    ("convert_multi_image", ["-i", TEST_DIR, "-f", "image"]),
    ("convert_single_pdf", ["-i", TEST_DIR, "-f", "Test_pdf.pdf"]),
    ("convert_form_pdf", ["-i", TEST_DIR, "-f", "Test_pdf_FillForm.pdf"]),
    ("convert_single_jpg", ["-i", TEST_DIR, "-f", "Test_image_JPG.jpg"]),
    ("convert_single_png", ["-i", TEST_DIR, "-f", "Test_image_PNG.png"]),
    ("enhanced_pdf", ["-i", TEST_DIR, "-f", "pdf", "-c", "2", "-sh", "10", "-br", "2"]),
    ("bw_blur_pdf", ["-i", TEST_DIR, "-f", "image", "-b", "yes", "-l", "yes"]),
    ("askew_pdf", ["-i", TEST_DIR, "-f", "Test_pdf.pdf", "-a", "true"]),
    ("no_askew_pdf", ["-i", TEST_DIR, "-f", "Test_pdf.pdf", "-a", "no"]),
    ("image_sort_by_name", ["-i", TEST_DIR, "-f", "image", "-s", "name"]),
    ("pdf_sort_by_ctime", ["-i", TEST_DIR, "-f", "pdf", "-s", "ctime"]),
    ("recursive_pdf", ["-f", "pdf", "-r", "y"]),
    ("recursive_image", ["-f", "image", "-r", "y"]),
]


@pytest.mark.parametrize("name, args", CLI_TEST_CASES)
def test_scanner_cli(name, args, test_env):
    """
    Runs the CLI against the test_env with various arguments.
    """
    result = run_cli(args)
    assert (
        "Files Found" in result.stdout
    ), f"'Files Found' not in CLI output for test '{name}'"
    # Ensure at least one output PDF was created in the temp dir
    output_files = list(TEST_DIR.rglob("*_output.pdf"))
    assert len(output_files) > 0, f"Test '{name}' did not generate any output PDF"
    assert (
        "output.pdf" in result.stdout
    ), f"'output.pdf' not in CLI output for test '{name}'"


def test_cli_help():
    """Check CLI help message"""
    result = run_cli(["-h"])
    assert result.returncode == 0
    assert "Convert PDF/Images" in result.stdout
    assert "Supported image" in result.stdout
    assert "Supported document" in result.stdout


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
    result = run_cli(["-f", "ABCD.pdf", "-r", "no"])
    assert result.returncode == 0
    assert "No matching files found" in result.stdout


def test_cli_energy_savings_output(test_env):
    """Test that energy savings message is printed."""
    result = run_cli(["-i", str(test_env), "-f", "image"])
    assert "You just saved" in result.stdout
