# look-like-scanned

[![Pylint](https://github.com/navchandar/look-like-scanned/actions/workflows/pylint.yml/badge.svg)](https://github.com/navchandar/look-like-scanned/actions/workflows/pylint.yml)  [![PyTest](https://github.com/navchandar/look-like-scanned/actions/workflows/tests.yml/badge.svg)](https://github.com/navchandar/look-like-scanned/actions/workflows/tests.yml)
![license](https://img.shields.io/badge/license-MIT-blue.svg)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/navchandar/look-like-scanned/issues)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) 

 - Python script to make documents look like they were scanned.

 - Local, Private, Secure, Open-Source and Transparent!

 - Converts every page of a given PDF file into an image-based page and applies random askew and brightness (very mild) effects to simulate the appearance of scanned documents.
 
 - The resulting pages are then combined back into an Output PDF file.

 - There are options to combine / convert image files into PDF as well.

 - Output PDF files are saved in the same folder with a suffix _"File_Name_output.pdf"_


## Installation

Install from the [Python Package Index (PyPI)](https://pypi.org/project/look-like-scanned/)
```shell
pip install look-like-scanned
```

Or to install latest version from GitHub
```shell
git clone https://github.com/navchandar/look-like-scanned.git
cd look-like-scanned
pip install poetry
poetry install
pip install .
```

### Verify Installation:
```shell
# Print help message and usage options available
scanner -h
```


## Usage

This package uses [PIL](https://pypi.org/project/Pillow/) and [pypdfium2](https://pypi.org/project/pypdfium2/) to convert and manipulate image and pdf objects.

This is extended to provide a command-line interface (CLI) for easy usage.


```shell
# Convert all pdf files in folder to scanned pdf
scanner -i .\tests
scanner -i .\tests -f "pdf"

# Convert all pdf files in folder to scanned pdf, set contrast, sharpness and brightness factors
scanner -i .\tests -c 2 -sh 10 -br 2

# Convert all pdf files in folder to scanned without askew
scanner -i .\tests -a no

# Convert specific pdf file in folder to scanned pdf
scanner -i .\tests -f "test.pdf"

# Convert all jpg, jpeg, png, webp files in folder to one pdf file
scanner -i .\tests -f "image"

# Convert all image files in folder in the order of file names
scanner -i .\tests -f "image" -s "name"

# Convert all png files in folder to pdf with 100% quality to one pdf file
scanner -i .\tests -f "png" -q 100

# Convert specific jpg file in folder to pdf with 75% quality to one pdf file
scanner -i .\tests -f "JPG_Test.jpg" -q 75

# Convert all PDF files including sub folders
scanner -i .\tests -f "pdf" -r yes

# Convert all Images including sub folders into one PDF
scanner -i .\tests -f "image" -r yes

# Convert all PDF files including sub folders and save in black & white format
scanner -i .\tests -f "pdf" -r yes -b yes

# Convert all png files including sub folders and make it a little blurry
scanner -i .\tests -f "png" -r yes -b yes -l yes

```

## Arguments

These are the command-line arguments accepted:

- `-i, --input_folder` : Specifies the input folder to read files from and convert. The default value is the current directory. 
    - Example: `-i /path/to/files` or `-i C:\files\documents`

- `-f, --file_type_or_name` : Specifies the file types to process or the file name to convert. The default value is "pdf" to convert all pdf files in the given input folder.
    - Example: `-f pdf` or `-f image.jpg` or `-f image`

- `-q, --file_quality` : Specifies the quality of the converted output files. The value must be between 50 and 100. The default value is 95. 
    - Example: `-q 90`

- `-a, --askew` : Controls whether to make the output documents slightly askew or slightly tilted. Accepted values are "yes" or "no". The default value is "yes". 
    - Example: `-a yes` or `--askew no`

- `-b, --black_and_white` : Controls whether to save output documents in black and white format (to make it look like a photocopy) . Accepted values are "yes" or "no". The default value is "no". 
    - Example: `-b yes` or `--black_and_white no`

- `-l, --blur` : Controls whether to make the output a little bit blurry. Accepted values are "yes" or "no". The default value is "no". 
    - Example: `-l yes` or `--blur no`

- `-c, --contrast` : Controls contrast factor of the image. A factor of 0.0 gives a solid gray image. A factor of 1.0 gives the original image. Greater values increase the contrast of the image. The default value is 1. 
    - Example: `-c 2`

- `-sh, --sharpness` : Controls sharpness factor of the image. A factor of 0.0 gives a blurred image. A factor of 1.0 gives the original image. Greater values increase the sharpness of the image. The default value is 1. 
    - Example: `-sh 2`

- `-br, --brightness` : Controls brightness factor of the image. A factor of 0.0 gives a black image. A factor of 1.0 gives the original image. Greater values increase the brightness of the image. The default value is 1. 
    - Example: `-br 2`

- `-r, --recurse` : Allows scripts to find all matching files including subdirectories. Accepted values are "yes" or "no". The default value is "yes". 
    - Example: `-r yes` or `--recurse no`

- `-s, --sort_by` : Allows scripts to sort the files based on name, creation time or modified time. Accepted values are "name", "ctime", "mtime", "none". The default value is "name". If "none" is selected, then the default order of files returned by the OS is used for document conversion.
    - Example: `-s name` or `--sort_by none`


❗❗ **Note:** ❗❗

- The supported file types are: ".jpg", ".png", ".jpeg", ".webp", ".pdf".

- The output PDF file size **will be bigger** than the input file because the pages are stored in image format.

- Bookmarks / Links / Metadata will be removed when saving the output file.

- Transparency will be removed from png files when converting to pdf.

- Password protected PDF files are not yet supported.

- [Youtube: How to Insert a Signature on a PDF File](http://www.youtube.com/watch?v=FKlAwFcMutY)


## License
 
 [MIT license](LICENSE)

## Authors
<a href="https://github.com/navchandar/look-like-scanned/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=navchandar/look-like-scanned" />
</a>

## Support This Project

[![Paypal Badge](https://img.shields.io/badge/-Paypal-0070ba?style=for-the-badge&logo=data%3Aimage%2Fjpeg%3Bbase64%2C%2F9j%2F4AAQSkZJRgABAQAAAQABAAD%2F2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz%2F2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz%2FwgARCAAwADADAREAAhEBAxEB%2F8QAHQAAAgIBBQAAAAAAAAAAAAAABwgGCQIAAwQFCv%2FEABwBAAEEAwEAAAAAAAAAAAAAAAYCAwcIAAEFBP%2FaAAwDAQACEAMQAAAAdZSiYpqCdXycvSppyvSMUbKuLEBqPeeyxsX4su2oRUX2QQweZr0j8qBdJUyhfS8vqPk%2FEV3tVbWaafq4naOlKlyuxybCnaAD9sq5XBxxSVysGLjOdMLWa4WvNYLKIfSoU5sq7yAEYZOOCWb7LwozP%2F%2FEAD0QAAAFAwMBBAQJDQAAAAAAAAECAwQFBgcIABESCSExUbUKd5bTExQXIiM4cYGyMjM3QUJHV2GCg5Oh0f%2FaAAgBAQABPwDA%2FBOyVX4SWdlpaztqZKVlKHhHTx68pJg4cO11GCBzqqHMkJjnMYRMYwiOpvA%2FHWnYpZ49srZts2aJmUWWNRkcBCFKG5hH6HuAA30NqsOAP2W%2FsH7IR%2FuNQdjsQaheC1aW3sO4WN3FJSEf7jTXp94%2BuEiGJZGzqhD9oGCjY7tAf7Os7MFLJ0dhFeSWibNWqi5SLoabeNHbOk2CLhmsmwXOmomoVIDEOUxQMBiiA66eX1ArGer%2BA8tQ11vLjrUB0%2Fat%2BKujs3z8SNkxIqKahimHifYQ7e42lq4lEC8jzEmUviLs%2FwD3Ta6Mk0U5pT0omYP2ivVCj%2BLXo4eXVUVjcyq6Cm6gfTER8QTeMwevTKmanKYxRKnyEfyuW466gwGHAC%2BX0n7v5%2Fy1xrp5ciYBWOKHYBbfQHlzfXpM9x14K0Nu4NAwcJp0%2BFwX%2BSZUBLqpltkiE8e3RC8zCBS8x8ADfXSKoCoLP3IYVYJVmK8m7aJtC8vzqQn3NyAB%2FwBDrqF%2FUAvoXwt9PeWrjrp8Bw6fdkDeNvYDy5vr0mWuzvr80NT3MTN2EWq7%2FqUMBR%2FBrFzGSlbuW6WlqgZKulwcCinxUMQOIfZq32CNKtDg8h6QcvBKOxVNlVQ3%2B4dtYOYMzU5WEZUEwzJHQ0SsksVuqUyainEdwKBdg27tdQr5mAV9fV9P%2BWuddPMAPgFY3l%2FD%2BB8uQ11P%2Bjlc7N%2FIY9VRFQQDWNSQM3bJuhUE5CchEAHYNU3jdIYsMho2SdM3r9qqZRRRrv8ABmEw7bBv9msE6EYw2MdLqHj2qbtymdZUTIFBQxvhTB2jtv3AGg7zcdvm9gB%2BouuoaQwYB3z9X0%2F5c41g5nRY%2BlMG7NRMteW1cXLRVEQjV4ydVbHoOGixGCJTpqEOqBiHIYBKJTAGidQ%2BwJQMX5cbPe2kb77U3d%2FDmpZo0k%2BuDYV2%2BOO5llawj%2BRjfcvqDz0x0gYdFmxvVZtq1alEqSZKyjgAgf5tE6h1gOH6c7P%2B2cb77Wc2dllKtwfvHExd5LVyspK0PNs2bJnVrBZw7WUYLkTTTTKqJjnMbYoFKA6%2F%2F8QAJREAAQMDAgYDAAAAAAAAAAAAAQACAwQFEQYhBxASEyIxQVFS%2F9oACAECAQE%2FAPTyVEySeQRsCFhuDvcZTrFVN9xqSLtPDZRhNGHloRHytDUzJ7k1jgjBGwbgLs0rh5ALiJZqQQNqIAnHJ8VnA6VwspuueSX84VwLx8ppL1WWyOS2TOn9Y2VQOlxaz7K9vXC2EMppXfrCgoWTjL06O307vMgFa21tSw0rqGl3JUjhISftAjGXLSesKOgpe28bqxXZtZRiePYFa9uM0t3lLX%2BITnuduTyzhqcD1BoCptWXWKM08cmGKoqHzydx5yTz%2F8QAJREAAQMCBgIDAQAAAAAAAAAAAQACAwQRBQYSISJRBzEQFUET%2F9oACAEDAQE%2FAG%2BrIyCPmUa%2BDtMxCDtMlAFmFWYNym%2Fqx%2BoMVEXD2mTTu9FXqO1lzEJGnROVZhGoot2t0s4TD%2BTG9qhYAdSufZNlmjNx%2B3pqWgfyaTdUz7Qt%2FTYIbut2s3uvI1vSztnWuwiqFPRuspM2ZoxFuhriWnoLxp41r6itbiNe06RvuomiOPirtJ4hYzgdTUPL2ryPSzfdSQyb2svFGERQZchbJGNe97hMY1gs0W%2BOWi9lyMe6rcg4LUzCpliu8%2ByqSmjp4RFELAfP%2F9k%3D&logoColor=white&link=https://paypal.me/navchandar//)](https://paypal.me/navchandar/) 
[![BuymeCoffee Badge](https://img.shields.io/badge/-Buy%20a%20Coffee-ff813f?style=for-the-badge&logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAIAAADYYG7QAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAEnQAABJ0Ad5mH3gAAAP5SURBVFhH7ZdrTFNnGMfftvSUXmTcBtNCWy6mXBRoAZWL1GAgIRnSiGOZkmF0W3YpJEYXtIm3qPEWP%2BgHRRogQLgmEmPiEpOZGBSX%2BAUZLES3%2Bc0PRiMJX5a5ubPnlCMxT9tznrcDYxae%2FD6c0vP%2Bn185p%2B95ysTjnveKFSE1VoTU%2BF8Ina3NIjL4ST5aqwq30K3PCxzpViLVztVouSrcQk1FaSK59Hr93b0ulKAMn9Bs6wboIXcjVGlJcYt7DQpRhiRUk5UAVGfEGwTw4a7sZPNCQkNOMkoOhSQUo9OWlZXV%2FIdqbm622WwNeakoORSqUFdXl3wZoq3GxsalFBIEvdEYC5gAkxEwA2bTIpa3juGthXOAhVWAwSAsmdD%2B8rRUi%2FChWV%2FsENz5zJXHioBcVpjLCnJYgZOtfwO8LARypXfhHDjZ7WDF6UyjYVszEyAHJYdCEgJ2FaRAonh6o%2Fg74yPAnhxhULd3F6LMsFCFTlQ7rHEG6fhRSEsFppl4kf3wtST09EDZ24GRoApNf1cCoT996RJvWXBXBX6UhL4qZ5vSLSgwElShv45WgVCP1yneiMddFbgmCXmyNLtdH6HASFCFAGeyqb0yXey14a4KjEhCKas0Z2oyUVokOIRgn5W2Wq77OsCen5JuoOufUR%2F7JKHLH6%2B1J1kSLUZTrAEO7FaBSrKwOkGAsiaY7fGxKDYsJKHxPUXwKdva2k5EWy6Xy5OdgmLDQhKaO1QBQqOjo%2FJTgL%2Fchet9G60oNizUe2ibM8nr9crxnDUzMwOfZ%2BIL0mBEFfJX2bIz7HIHzhoaGgKheX8lygwLVWhoR64UOj8vN%2BEpv9%2BfnRqPAiNBFZoJ7tQTExNyE56qr6%2F35i%2FDxijE6Do6OuQmPJVhSzvssaO0SHAIua0f%2BHw%2BuQm55ubmpG9oUx5KiwSHUEtRqmdzpdyHXOPj4yA021qK0iLBIQS%2FyCC6s7MTNqTh4eGBgYG%2Bvr6enh6YbuGPcDUDgUB3d3dvb29%2Ff%2F%2Fg4ODIyMjY2FhdXd0GexKKUoBDCAYaEEKl1Wr0MRqDQWuM1QmCVqfTwHCIao%2BbekcDHELAy4MV%2FdtzwOzPB9q%2FH7N%2Ffgt5mgZ5%2FSt7dZ%2F9cYElGnWwy79oL0c5CvAJAb%2F4SqU9V3VMC45m5bZVaLkq3EKvj1V1NRDGtOBoxnWxFuAWAr6vIIxpwdHsXC11LlskGqF6Z5L6mBZgz06yGzvXobWqRCMEX5xXR6rESS2WWGRS%2Bvdc%2FTSqcPSaAgj9%2FG2JeE%2FAHovckYT2bXmHQudrM6eumKZusvBcYlPtrDLzXQmlxRmk%2FY5QaCGFaNY8%2FKaYCFpIIRqhZWVFSI0VIWWOe%2F4FR6A6eCoawHAAAAAASUVORK5CYII%3D&logoColor=white&link=https://www.buymeacoffee.com/navchandar//)](https://www.buymeacoffee.com/navchandar/) 
[![Ko-Fi Badge](https://img.shields.io/badge/-Buy%20a%20KoFi-ff5f5f?style=for-the-badge&logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAIAAADYYG7QAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAEnQAABJ0Ad5mH3gAAAOiSURBVFhH7ZbLTxRBEMb963gkJIRleS4JyyJnDnqFKA%2BREOXAgcAJhAMEL77xoBdEjSQY8II3wchrgQUUdmZnusqvpofZzfDoBdF4mM2XSae3u%2BrXVdU1c4NLSv4rRUAmRUAmRUAmRUAmRUAmRUAmRUAmRUAmGYBo9jVlLfp1REfHfyjOZGjxM93v59JSMa6fp2QC2ssQMTkuuerqyjmQchTr38ICJZrE%2FllMBiB3M02KtEVflp0f2LmLJrUcV2PIwRBsy5bx2ndqTIR8aRmA1JYPpGDXdhxFsJdTFAzYsl1XhSftHNZrGkFc%2BUrLX2g7LSiYPM7K4NMCl5eH3EEmoO0dDQQf8Ef7BzwzQ733qKuLp6Zodw8EqDB%2B8pR6eqi7myYmaGs7h2joOGHLwSE3NIi1eJwnJ1l5GbRzwtTdU%2BhLqzggnNh16fAnd3aqqipqaBBVx%2BjWbZqb47t3KBaj%2BnqZxKC9nTY2XThGbLAXuxL57NDMY0FBkIjow8dgPlBxQFnLgplXs1RdrVpvcipFLS2EZ1OTcCQSMsYM1NaGNfxoAuuxC1R5ICQIVdzcLJcOBQCg9Y1CX1rFAVkWskAjI1RXCxpOJhUE00kPApJx0hcQe3sdrEeEcMUCIH2nYjG1uS0Fjr929wJHgS4RIRobo5oaam3V7uWsAYeewSCVUnV1PDCA0g6n7NojxEtLUiU6JJojJDhD%2FAD95u0ZKfN0TTWEK2PnbAxGR1G2ChVTGJ6ABsHDVerry7cibCm4ZTRxXbfMu%2FbSWrIWP3ioauJ%2BkAImTVNbSx0dlMlIg9BMf6sPedbBhB7IjkNDQ1wTVwFTczODBplCHzo89LrlCY33hHshgJ3jrBwJ49U1bmwM%2BdIyAZ10atiVCHlxkh4zOqpA4DEhg6gb7u%2Fn4ywuF3q3rNTSWLAAkQZjXlzkpqu%2By%2FJAiJD%2FApHTSz2Nj0v9trSAjAcHJX5K5Wm8Lf5gd492dunHOs2%2Fp55en%2BMsGqjYGgp85Jlw1ulpac3DwxI2ZPOEBuh6sezN7EvrQresrMxbPocGMgDRt1W5n8GtKYgTnlK8y8soW0mirvrC2GAXFmxucUWFbxAcZWWB8TNlAGLkBT%2FLCoBCQpyEww7Pi3T9PnsudkwcgUxAFRX0bl7sotPDsf7gKhQcn573ZuQkKytS77Bzfo5CMgFBCPj0NKfTwcdoUcKn5ouXPs1lVATQv1UEZFIEZFIEZFIEZFIEdLFKSn4Dz0s70NgRCBAAAAAASUVORK5CYII%3D&logoColor=1fb3ef&link=https://ko-fi.com/navchandar//)](https://ko-fi.com/navchandar/) 
