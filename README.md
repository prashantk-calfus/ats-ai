# AI HR APP

### Prerequisite:
Please get the GEMINI_API_KEY and put it in your .env file

### Setup Instructions

Run the below cmds on terminal for local dev:
```commandline
 make local
```
Or run it from containers:
```commandline
 make prod
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


### Useful Makefile commands to run separately
```commandline
 make backend
```
```commandline
 make ui
```
For more commands refer the Makefile.