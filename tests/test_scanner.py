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
    output_pdf = convert_images_to_pdf(test_files, 90, False, False, False, 0.5, 0.75, 2)
    print(output_pdf)
    assert output_pdf.endswith(".pdf")
    assert os.path.exists(output_pdf)
    assert os.stat(output_pdf).st_size > 100
    assert is_pdf_valid(output_pdf)


def test_convert_pdf_to_scanned():
    """Test converting PDF to scanned output"""
    test_files = [
        os.path.join("./tests", file)
        for file in os.listdir("./tests")
        if file.lower().endswith(".pdf")
    ]
    output_files = convert_pdf_to_scanned(test_files, 90, True, True, True, 0.5, 0.75, 2)
    assert len(output_files) > 1
    for i, output_pdf in enumerate(output_files):
        assert output_pdf.lower().endswith(".pdf")
        assert os.path.exists(output_pdf)
        assert os.stat(output_pdf).st_size > 100
        assert is_pdf_valid(output_pdf)


# Run the tests
if __name__ == "__main__":
    pytest.main()
