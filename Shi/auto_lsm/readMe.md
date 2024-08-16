“A template of how to write a readMe.md file lol, this sentence need to be deleted later!”

# Auto LSM System User Manual

Foobar is a Python library for dealing with word pluralization.

## Installation
Make sure the local machine has following packages installed:
1. [pyautogui](https://pyautogui.readthedocs.io/en/latest/)
2. [Pillow](https://pypi.org/project/pillow/)
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install those packages stated above
If unsure, please use following code to check if the proper packages are installed
```bash
pip show pyautogui
```
```bash
pip show Pillow
```
If the package is not installed, please use the following code to install
```
pip install package_name
```

## Usage

```python
import foobar

# returns 'words'
foobar.pluralize('word')

# returns 'geese'
foobar.pluralize('goose')

# returns 'phenomenon'
foobar.singularize('phenomena')
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
