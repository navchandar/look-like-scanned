"""Script to test scanner package"""
import os
import glob
import pytest
import subprocess
from scanner.scanner import convert_images_to_pdf, convert_pdf_to_scanned, _add_suffix, human_size

TEST_DIR = "./tests"


def cleanup_output_files(directory):
    """Delete all *_output*.pdf files in the given directory"""
    for file in glob.glob(os.path.join(directory, "*_output*.pdf")):
        try:
            os.remove(file)
            print(f"\nDeleted file: {file}")
        except Exception as e:
            print(f"\nFailed to delete {file}: {e}")


@pytest.fixture(autouse=True)
def cleanup_after_test():
    yield
    cleanup_output_files(TEST_DIR)


def test_add_suffix():
    err = "Suffix not added correctly to 'document.pdf'"
    assert _add_suffix("document.pdf") == "document_output.pdf", err
    assert _add_suffix("report") == "report_output.pdf", err


def test_human_size():
    assert human_size(0) == "0 B", "Expected '0 B' for input 0"
    assert human_size(1024) == "1.0KiB", "Expected '1.0KiB' for input 1024"
    assert human_size(1048576) == "1.0MiB", "Expected '1.0MiB' for input 1048576"


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
    assert output_pdf.endswith(".pdf"), "Output file does not have a .pdf extension"
    assert os.path.exists(output_pdf), f"Output PDF file does not exist: {output_pdf}"
    assert os.stat(output_pdf).st_size > 100, f"Output PDF file is blank: {output_pdf}"
    assert is_pdf_valid(output_pdf), f"Output PDF file is not valid: {output_pdf}"


def test_convert_pdf_to_scanned():
    """Test converting PDF to scanned output"""
    test_files = [
        os.path.join(TEST_DIR, file)
        for file in os.listdir(TEST_DIR)
        if file.lower().endswith(".pdf")
    ]
    output_files = convert_pdf_to_scanned(test_files, 90, True, True, True, 0.5, 0.75, 2)
    assert len(output_files) > 1, "Expected more than one output PDF file"
    for i, output_pdf in enumerate(output_files):
        assert output_pdf.lower().endswith(".pdf"), f"Output file {i} does not have a .pdf extension"
        assert os.path.exists(output_pdf), f"Output file {i} does not exist: {output_pdf}"
        assert os.stat(output_pdf).st_size > 100, f"Output file {i} is blank: {output_pdf}"
        assert is_pdf_valid(output_pdf), f"Output file {i} is not a valid PDF: {output_pdf}"


# Define test name id and CLI parameters used for testing
cli_test_cases = {
    "convert_multi_pdf": ["-i", TEST_DIR, "-f", "pdf"],
    "convert_multi_image": ["-i", TEST_DIR, "-f", "image"],
    "convert_single_pdf": ["-i", TEST_DIR, "-f", "Test_pdf.pdf"],
    "convert_single_image": ["-i", TEST_DIR, "-f", "Test_image_PNG.png"],
    "enhanced_pdf": ["-i", TEST_DIR, "-f", "pdf", "-c", "2", "-sh", "10", "-br", "2"],
    "bw_blur_pdf": ["-i", TEST_DIR, "-f", "pdf", "-r", "yes", "-b", "yes", "-l", "yes"],
    "no_askew_pdf": ["-i", TEST_DIR, "-f", "pdf", "-a", "no"],
    "image_sort_by_name": ["-i", TEST_DIR, "-f", "image", "-s", "name"],
    "pdf_sort_by_ctime": ["-i", TEST_DIR, "-f", "pdf", "-s", "ctime"],
    "pdf_sort_by_mtime": ["-i", TEST_DIR, "-f", "pdf", "-s", "mtime"],
    "recursive_pdf": ["-i", ".", "-f", "pdf", "-r", "yes"]
}


def run_cli_command(args):
    """Function to run and check the scanner CLI"""
    result = subprocess.run(
        ["scanner"] + args,
        capture_output=True,
        text=True,
        check=True
    )
    print(f"\n[CLI STDOUT]\n{result.stdout}")
    print(f"\n[CLI STDERR]\n{result.stderr}")
    return result


@pytest.mark.parametrize("test_case", cli_test_cases.items(), ids=list(cli_test_cases.keys()))
def test_scanner_cli(test_case):
    name, args = test_case
    result = run_cli_command(args)
    code = result.returncode
    assert code == 0, f"CLI test '{name}' failed with return code: {code}"
    assert "Matching Files Found" in result.stdout, f"'Matching Files Found' not in CLI output for test '{name}'"
    assert "Output PDF" in result.stdout, f"'Output PDF' not in CLI output for test '{name}'"


# Run the tests
if __name__ == "__main__":
    pytest.main()
