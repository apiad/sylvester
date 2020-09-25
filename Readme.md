# Sylvester

> ### A streamlit-based Twitter analysis tool for hackers

This is a very simple project to analyze your Twitter data. 
There is no sign-up, user management, etc.
Nothing is stored on the server.

For this reason, you will need to [create a Twitter developer account](https://developer.twitter.com), create an application, and upload your own credentials.

## Deploying the application locally

> ### [🖥️ apiad/sylvester](https://github.com/apiad/sylvester)

This is a simple [streamlit](https://streamlit.io) app, so you know the drill.

```bash
# clone

$ git clone https://github.com/apiad/sylvester
$ cd sylvester

# create a virtualenv unless you want to unleash chaos
# ... choose your favourite virtualenv manager

$ pip install -r requirements.txt
$ streamlit run app.py 
```

## Using the application

> ### [🔗 sylvester-demo.herokuapp.com](https://sylvester-demo.herokuapp.com)

You will need to save your Twitter developer credentials in a `.json` file with this structure:

```json
{
    "api_key": "...",
    "api_key_secret": "...",
    "access_token": "...",
    "access_token_secret": "..."
}
```

On the application sidebar, select `🔽 Pull Data`. Upload your JSON credentials files and you will be able to download all your messages. Store this JSON file somewhere, it's your data!

Once your data is down, selected `📊 Analyze Data` and upload your JSON file again. This application stores NOTHING in the server filesystem, not even temporarily, so it doesn't matter if you just downloaded your data, it's already been deleted.

## Collaboration

👍 All code is MIT, so fork, modify, and pull-request. All contributions are greatly appreciated!
