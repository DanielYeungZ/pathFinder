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

7. **deploymenty command**:
   ```bash
   eb init -p python-3.11 flask-api
   eb create flask-api-env

   mv Procfile.api Procfile
   eb deploy flask-api-env --staged
   mv Procfile Procfile.api
   
   eb init -p python-3.11 flask-celery-worker

   eb create celery-worker-env --tier worker

   mv Procfile.worker Procfile
   rm -rf .ebextensions
   cp -r .ebextensions-worker .ebextensions

   eb deploy celery-worker-env --staged

   # Restore
   mv Procfile Procfile.worker
   rm -rf .ebextensions
   ```

   ```
   eb init -p python-3.11 flask-api
   mv Procfile.api Procfile
   git add -A
   eb deploy flask-api-env --staged
   mv Procfile Procfile.api
   git add -A

   # Celery Worker
   eb init -p python-3.11 flask-celery-worker
     eb init -p python-3.11 flask-celery-worker-prod
   mv Procfile.worker Procfile
   rm -rf .ebextensions && cp -r .ebextensions-worker .ebextensions
   git add -A
   eb deploy celery-worker-env --staged
   mv Procfile Procfile.worker && rm -rf .ebextensions
   git add -A
   ```
   ```
   git add -A
   eb deploy --staged


  eb init -p python-3.11 flask-api-prod
   mv Procfile.api Procfile
   git add -A
   eb deploy Flask-api-prod-env --staged
   mv Procfile Procfile.api
   git add -A

   ```

   worker: celery -A factory.celery worker --loglevel=info
   web: gunicorn main:app --timeout 3000
   pip freeze > requirements.txt
   eb logs > worker_logs.txt    
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


