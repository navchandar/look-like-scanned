import os
import pytest
from scanner.scanner import convert_images_to_pdf, convert_pdf_to_scanned


# Test converting images to PDF
def test_convert_images_to_pdf():
    test_files = ["./tests/Test_image_JPG.jpg", "./tests/Test_image_Webp.webp"]
    output_pdf = convert_images_to_pdf(test_files, 90, False)
    print(output_pdf)
    assert output_pdf.endswith(".pdf")
    assert os.path.exists(output_pdf)


# Test converting PDF to scanned output
def test_convert_pdf_to_scanned():
    test_files = ["./tests/Test_pdf.pdf", "./tests/Test_pdf_A4.PDF"]
    output_files = convert_pdf_to_scanned(test_files, 90, False)
    for output_pdf in output_files:
        assert output_pdf.lower().endswith(".pdf")
        assert os.path.exists(output_pdf)


# Run the tests
if __name__ == "__main__":
    pytest.main()
