"""Script to test scanner package"""
import os
import pytest
import subprocess
from scanner.scanner import convert_images_to_pdf, convert_pdf_to_scanned, _add_suffix, human_size

test_dir = "./tests"


def test_add_suffix():
    assert _add_suffix("document.pdf") == "document_output.pdf"
    assert _add_suffix("report") == "report_output.pdf"


def test_human_size():
    assert human_size(0) == "0 B"
    assert human_size(1024) == "1.0KiB"
    assert human_size(1048576) == "1.0MiB"


def is_pdf_valid(file_path):
    """Check if given PDF file is valid by checking the header of the PDF file"""
    try:
        with open(file_path, "rb") as file:
            header = file.read(4)
            return header == b"%PDF"
    except IOError:
        return False


def test_convert_images_to_pdf():
    """Test converting images to PDF"""
    test_files = ["./tests/Test_image_JPG.jpg", "./tests/Test_image_Webp.webp"]
    output_pdf = convert_images_to_pdf(test_files, 90, False, False, False, 0.5, 0.75, 2)
    print(output_pdf)
    assert output_pdf.endswith(".pdf")
    assert os.path.exists(output_pdf)
    assert os.stat(output_pdf).st_size > 100
    assert is_pdf_valid(output_pdf)


def test_convert_pdf_to_scanned():
    """Test converting PDF to scanned output"""
    test_files = [
        os.path.join(test_dir, file)
        for file in os.listdir(test_dir)
        if file.lower().endswith(".pdf")
    ]
    output_files = convert_pdf_to_scanned(test_files, 90, True, True, True, 0.5, 0.75, 2)
    assert len(output_files) > 1
    for i, output_pdf in enumerate(output_files):
        assert output_pdf.lower().endswith(".pdf")
        assert os.path.exists(output_pdf)
        assert os.stat(output_pdf).st_size > 100
        assert is_pdf_valid(output_pdf)


def test_cli_convert_pdf_to_scanned():
    """Test CLI for converting PDFs in a folder"""
    result = subprocess.run(
        ["scanner", "-i", test_dir, "-f", "pdf"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Matching Files Found" in result.stdout
    assert any("output.pdf" in line for line in result.stdout.splitlines())


def test_cli_convert_images_to_pdf():
    """Test CLI for converting images in a folder"""
    result = subprocess.run(
        ["scanner", "-i", test_dir, "-f", "image"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Matching Files Found" in result.stdout


def test_cli_with_image_enhancements():
    result = subprocess.run(
        ["scanner", "-i", "./tests", "-f", "pdf", "-c", "2", "-sh", "10", "-br", "2"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Matching Files Found" in result.stdout


def test_cli_bw_and_blur():
    result = subprocess.run(
        ["scanner", "-i", "./tests", "-f", "pdf", "-r", "yes", "-b", "yes", "-l", "yes"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0


def test_cli_without_askew():
    result = subprocess.run(
        ["scanner", "-i", "./tests", "-f", "pdf", "-a", "no"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0


def test_cli_specific_file():
    result = subprocess.run(
        ["scanner", "-i", "./tests", "-f", "test.pdf"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0


def test_cli_image_sorting():
    result = subprocess.run(
        ["scanner", "-i", "./tests", "-f", "image", "-s", "name"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0


def test_cli_recursive_pdf():
    result = subprocess.run(
        ["scanner", "-i", ".", "-f", "pdf", "-r", "yes"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0


# Run the tests
if __name__ == "__main__":
    pytest.main()
