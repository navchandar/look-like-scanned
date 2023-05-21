# look-like-scanned
Python script to make documents look like they were scanned


## Installation

```
git clone https://github.com/navchandar/look-like-scanned.git
pip install poetry
poetry install
```


## Example Usage

```shell
#Convert all pdf files in folder to scanned pdf
.\scanner\scanner.py -i .\tests

#Convert specific pdf file in folder to scanned pdf
.\scanner\scanner.py -i .\tests -f "test_A4.pdf"

#Convert all png files in folder to pdf
.\scanner\scanner.py -i .\tests -f "png" -q 100

#Convert specific jpg file in folder to pdf
.\scanner\scanner.py -i .\tests -f "JPG_Test.jpg" -q 95

```

## License
 - [MIT license](LICENSE)

