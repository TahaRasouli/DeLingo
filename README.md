# DeLingo
An app for learning and reviewing German vocabulary. The app is currently in its inital stage of development, but even now, it can assist you with your learning journey. To fully understand how the app is initialized, please do check the rest of README file. Finally, don't forget to star the repo, otherwise the ghost of the writer of the code will hunt you forever and after. 👻

## Initializing the app:
clone the repo using the following command:
```
git clone https://github.com/TahaRasouli/DeLingo/
```

Whne inside the code's directory, install the dependencies:
```
pip install -r requirements.txt
```

Then visit the following website and register for an API key:
```
https://console.groq.com
```

After receiving the API key, apply it using the following command:
```
export GROQ_API_KEY=<your-api-key-here>
```

Finally run the app using the following streamlit command:
```
streamlit run main.py
```
