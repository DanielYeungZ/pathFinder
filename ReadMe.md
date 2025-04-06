# PathFinder Project

## Setup Instructions

Follow these steps to set up the project:

1. **Activate the Virtual Environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **install packages**:

   ```bash
   pip3 install -r requirements.txt
   ```

3. **run tests**:

   ```bash
   PYTHONWARNINGS=ignore python3 -m unittest discover -s ./tests -v
   ```

4. **run main**:

   ```bash
   python3 main.py
   ```

5. **use Makefile**:
   ```bash
   make venv
   make install
   make run
   ```


6. **useful command**:
   ```bash
   pip freeze > requirements.txt    
   python --version
   eb logs
   ```

## Project Structure

```bash
pathFinder/
├── config.py
├── models/
│   ├── __init__.py
│   ├── building.py
│   └── image.py
├── routes/
│   ├── __init__.py
│   ├── buildingRoute.py
│   └── imageRoute.py
├── tests/
│   ├── __init__.py
│   ├── test_buildingRoute.py
│   └── test_imageRoute.py
├── venv/
├── auth.py
├── main.py
└── requirements.txt
```
