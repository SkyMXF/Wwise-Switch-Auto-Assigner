# Wwise-Switch-Auto-Assigner


## Environment

python 3.11
```
python -m venv .\venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Package with PyInstaller

```
python package_with_installer.py
```

## Running args

```
usage: main.py [-h] [--project_root PROJECT_ROOT] [--object_id OBJECT_ID] [--match_method {tfidf,levenshtein,inclusion}] [--recursive] [--user_config USER_CONFIG]

options:
  -h, --help            show this help message and exit
  --project_root PROJECT_ROOT
                        Project root path to check if WAAPI is connected to the correct project.
  --object_id OBJECT_ID
                        Object ID to handle.
  --match_method {tfidf,levenshtein,inclusion,special_foley}
                        Method to match names of switch and switch container child. Choices: tfidf, levenshtein, inclusion, special_foley.
  --recursive           Handle object recursively.
  --user_config USER_CONFIG
                        User config file path.
```
