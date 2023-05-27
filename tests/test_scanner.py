"""Script to test scanner package"""
import os
import pytest
from scanner.scanner import convert_images_to_pdf, convert_pdf_to_scanned


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
    output_pdf = convert_images_to_pdf(test_files, 90, False)
    print(output_pdf)
    assert output_pdf.endswith(".pdf")
    assert os.path.exists(output_pdf)
    assert os.stat(output_pdf).st_size > 100
    assert is_pdf_valid(output_pdf)


def test_convert_pdf_to_scanned():
    """Test converting PDF to scanned output"""
    test_files = ["./tests/Test_pdf.pdf", "./tests/Test_pdf_A4.PDF"]
    output_files = convert_pdf_to_scanned(test_files, 90, False)
    for i, output_pdf in enumerate(output_files):
        assert output_pdf.lower().endswith(".pdf")
        assert os.path.exists(output_pdf)
        assert os.stat(output_pdf).st_size > 100
        assert os.stat(output_pdf).st_size > os.stat(test_files[i]).st_size
        assert is_pdf_valid(output_pdf)


# Run the tests
if __name__ == "__main__":
    pytest.main()
