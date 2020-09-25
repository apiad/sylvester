from pathlib import Path
import streamlit as st
import altair as alt
import json
import pandas as pd
import tweepy
import io
import base64

from pydantic import BaseModel

st.beta_set_page_config(page_title="Sylvester")
st.set_option("deprecation.showfileUploaderEncoding", False)


class Auth(BaseModel):
    api_key: str
    api_key_secret: str
    access_token: str
    access_token_secret: str


def load_file():
    fp = st.file_uploader("📄 Upload JSON file (one tweet per line)", key="twitter-data")

    if fp is None:
        return []

    results = []

    for line in fp:
        results.append(json.loads(line))

    return results


def load_credentials():
    fp = st.file_uploader("🔑 Upload JSON file with credentials", key="credentials-data")

    if fp is None:
        return None

    return Auth.parse_raw(fp.read())


@st.cache
def load_tweets(tweets_list):
    tweets = []

    for item in tweets_list:
        data = dict(
            timestamp=pd.to_datetime(item["created_at"]),
            is_reply=item["in_reply_to_status_id"] is not None,
            is_quote=item["is_quote_status"],
        )

        data["date"] = data["timestamp"].date()
        tweets.append(data)

    tweets = pd.DataFrame(tweets)
    return tweets


@st.cache
def load_mentions(tweets_list):
    mentions = []

    for item in tweets_list:
        for entity in item["entities"]["user_mentions"]:
            data = dict(
                timestamp=pd.to_datetime(item["created_at"]),
                user=entity["screen_name"],
            )

            data["date"] = data["timestamp"].date()
            mentions.append(data)

    return pd.DataFrame(mentions)


@st.cache
def load_mention_pairs(tweets_list):
    pairs = []

    for item in tweets_list:
        for i, entity1 in enumerate(item["entities"]["user_mentions"]):
            for j, entity2 in enumerate(item["entities"]["user_mentions"]):
                if i == j:
                    continue

                data = dict(
                    timestamp=pd.to_datetime(item["created_at"]),
                    user1=entity1["screen_name"],
                    user2=entity2["screen_name"],
                )

                data["date"] = data["timestamp"].date()
                pairs.append(data)

    return pd.DataFrame(pairs)


def authenticate(credentials: Auth):
    # authorize twitter, initialize tweepy
    auth = tweepy.OAuthHandler(credentials.api_key, credentials.api_key_secret)
    auth.set_access_token(credentials.access_token, credentials.access_token_secret)
    api = tweepy.API(auth)

    return api


def download_tweets(api: tweepy.API, total_tweets: int):
    current_text = st.empty()
    progress = st.progress(0)
    stream = io.StringIO()

    for i, tweet in enumerate(
        tweepy.Cursor(api.user_timeline, tweet_mode="extended").items(total_tweets)
    ):
        data = dict(tweet._json)
        stream.write(json.dumps(data) + "\n")
        current_text.markdown(f"⌛ Downloading messages: {i+1}/{total_tweets}")
        progress.progress((i + 1) / total_tweets)

    current_text.empty()
    progress.empty()

    stream.seek(0)
    return stream


def main():
    functions = {"⚠️ Information": info, "🔽 Pull Data": pull_data, "📊 Analyze Data": analyze_data}
    function = functions[st.sidebar.selectbox("Function", list(functions))]
    function()


def info():
    with open(Path(__file__).parent / "Readme.md") as fp:
        st.write(fp.read())


def pull_data():
    credentials = load_credentials()

    if credentials is None:
        st.warning("⚠️ You need to upload your API credentials in a JSON file.")
        return

    api = authenticate(credentials)

    st.success("✔️ Credentials loaded succesfully!")

    user = api.me()

    st.info(
        f"""
    - 😃 {user.name} ([**@{user.screen_name}**](https://twitter.com/{user.screen_name}))
    - 🤩 {user.followers_count} followers
    - 😎 {user.friends_count} friends
    - 🗨️ {user.statuses_count} tweets
    """
    )

    total_tweets = st.sidebar.number_input(
        "🗨️ Total messages to download",
        min_value=0,
        max_value=user.statuses_count,
        value=user.statuses_count,
        step=100,
    )

    if not st.button("🔽 Download data"):
        return

    stream = download_tweets(api, total_tweets=total_tweets)
    b64 = base64.b64encode(stream.read().encode("utf8"))
    link = f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{user.screen_name}_{total_tweets}.jsonl">📄 Download JSON file</a>'

    st.markdown(link, unsafe_allow_html=True)


def analyze_data():
    tweets_list = load_file()

    if not tweets_list:
        st.warning("⚠️ You need to upload a JSON file with Twitter data.")
        return

    st.success(f"✔️ Loaded {len(tweets_list)} tweets.")

    st.write("### 🗓️ Evolution of tweets over time")

    tweets = load_tweets(tweets_list)

    min_date, max_date = tweets["date"].min(), tweets["date"].max()
    min_date = st.sidebar.date_input("📆 Start date", min_date, min_date, max_date)
    max_date = st.sidebar.date_input("📆 End date", max_date, min_date, max_date)

    tweets = tweets[(min_date <= tweets["date"]) & (tweets["date"] <= max_date)]

    if not st.checkbox("👁️‍🗨️ Include replies"):
        tweets = tweets[tweets["is_reply"] == False]

    if st.checkbox("🗃️ Show raw tweets data"):
        st.write(tweets)

    date_format = st.sidebar.selectbox("📆 Date format", ["Year/Month", "Year/Month/Day"])
    date_filter = "yearmonth" if date_format == "Year/Month" else "yearmonthdate"

    st.altair_chart(
        alt.Chart(tweets)
        .mark_bar()
        .encode(
            x=alt.X(f"{date_filter}(date)", title="Date"),
            color=alt.Color("is_reply", title="Is reply?"),
            y=alt.Y("count()", title="No. of tweets"),
        ),
        use_container_width=True,
    )

    st.write("### 🕰️ Most common days and hours")

    st.altair_chart(
        alt.Chart(tweets)
        .mark_bar()
        .encode(
            x=alt.X("hours(timestamp)", title="Hour"),
            color=alt.Color("count()", title="Total tweets"),
            y=alt.Y("day(date):N", title="Day pf the week"),
        ),
        use_container_width=True,
    )

    st.write("### 💁 Top mentioned users")

    mentions = load_mentions(tweets_list)

    mentions = mentions[(mentions["date"] >= min_date) & (mentions["date"] <= max_date)]

    if st.checkbox("🗃️ Show raw mentions data"):
        st.write(mentions)

    mentions_by_user = (
        mentions.groupby("user")
        .agg(count=("date", "count"))
        .sort_values("count", ascending=False)
        .reset_index()
    )

    max_interactions = st.number_input(
        "Max number of users to show",
        min(10, len(mentions_by_user)),
        len(mentions_by_user),
        min(10, len(mentions_by_user)),
    )
    mentions_by_user = mentions_by_user[:max_interactions]

    st.write(mentions_by_user.set_index("user"))

    st.altair_chart(
        alt.Chart(mentions_by_user)
        .mark_bar()
        .encode(
            x=alt.X("user", title="Username"),
            y=alt.Y("count", title="No. of mentions"),
        ),
        use_container_width=True,
    )

    st.write("### 👪 Users often mentioned together")

    pairs = load_mention_pairs(tweets_list)
    pairs = pairs[(pairs["date"] >= min_date) & (pairs["date"] <= max_date)]
    pairs = pairs[
        (pairs["user1"].isin(mentions_by_user["user"]))
        & (pairs["user2"].isin(mentions_by_user["user"]))
    ]

    if st.checkbox("🗃️ Show raw mention pairs data"):
        st.write(pairs)

    st.altair_chart(
        alt.Chart(pairs)
        .mark_circle()
        .encode(
            x=alt.X("user1", title="Username"),
            y=alt.Y("user2", title="Username"),
            size=alt.Size("count()", title="Mentions"),
            color=alt.Color("count()", title=""),
        ),
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
