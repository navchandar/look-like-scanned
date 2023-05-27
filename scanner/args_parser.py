import os
import argparse

SUPPORTED_IMAGES = [".jpg", ".png", ".jpeg", ".webp"]
SUPPORTED_DOCS = [".pdf", ".PDF"]
CHOICES = ["y", "yes", "n", "no", "true", "false"]


def parse_args():
    """Parse input command-line arguments for the script"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input_folder",
        type=str,
        help="The input folder to read files from and convert (default: current directory)",
    )
    parser.add_argument(
        "-f",
        "--file_type_or_name",
        type=str,
        help="The file types to process or file name to process. Valid value - image, pdf, file names (default: pdf)",
    )
    parser.add_argument(
        "-q",
        "--file_quality",
        type=int,
        choices=range(50, 101, 5),
        default=95,
        help="The quality of the converted output files. Valid range - 50 to 100 increment in steps of 5 (default: 95)",
    )
    parser.add_argument(
        "-a",
        "--askew",
        type=str.lower,
        choices=CHOICES,
        default="yes",
        help="Make output documents slightly askew or slightly tilted (default: yes)",
    )
    parser.add_argument(
        "-r",
        "--recurse",
        type=str.lower,
        choices=CHOICES,
        default="no",
        help="Recurse in all sub folders to find matching files and convert them (default: no)",
    )

    return parser.parse_args()


def get_argument(argument_name):
    """
    Gets the input folder from the command-line argument.
    If no input folder provided, returns the current working directory.
    """
    args = parse_args()
    if argument_name == "folder":
        input_folder = os.getcwd()
        if args.input_folder:
            input_folder = args.input_folder
        else:
            print("Defaulting to current directory")
        input_folder = os.path.abspath(input_folder)

        # check if folder path exists
        if os.path.exists(input_folder):
            print(f"Processing files from {input_folder=}")
        else:
            print(f"Error: Input folder path not found: {input_folder}")
        return input_folder

    if argument_name == "quality":
        return int(args.file_quality) if args.file_quality else 95

    if argument_name == "askew":
        return args.askew.lower().startswith("y") if args.askew else True

    if argument_name == "recurse":
        return args.recurse.lower().startswith("y") if args.recurse else True

    if argument_name == "file_type":
        match = (None, None)
        if args.file_type_or_name:
            file = args.file_type_or_name.lower()
            if file == "image":
                match = ("image", SUPPORTED_IMAGES)
            elif any(f.endswith(file) or file.endswith(f) for f in SUPPORTED_IMAGES):
                match = ("image", [args.file_type_or_name])
            elif any(f.endswith(file) or file.endswith(f) for f in SUPPORTED_DOCS):
                match = ("pdf", [args.file_type_or_name])
            else:
                print("Defaulting to find pdf files")
        else:
            match = ("pdf", SUPPORTED_DOCS)
        return match
