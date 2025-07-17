# AI HR APP

### Setup Instructions

Run the below cmds on terminal for local dev:
```commandline
 make all
 ./start.sh
```
Or run it from containers:
```commandline
 docker compose up -d
```

This will spin up the local ollama model and backend service container along with web ui app.
The API service will be running on: 
``
    http://localhost:8000
``

And the UI will run on below url:

### Navigate to UI:
``
    http://0.0.0.0:8501
``


### Useful Makefile commands
```commandline
 make all_backend
```
```commandline
 make all_ui
```
For more commands refer the Makefile.