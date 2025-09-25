import streamlit as st
import pickle
import joblib
import pandas as pd
import numpy as np
import requests
import isodate
from urllib.parse import urlparse, parse_qs
from streamlit_option_menu import option_menu   

# -----------------------------
# Load Models (trained & saved from notebook)
# -----------------------------
# Load lr and scaler
with open("linear_model.pkl", "rb") as f:
    gb = pickle.load(f)
with open("scaler.pkl", "rb") as f:
    scaler = pickle.load(f)    

# -----------------------------
# YouTube API Setup
# -----------------------------
API_KEY = "AIzaSyDFe8IoerY7fXqxNDC8b1Vc4LVBuAXqsng"

class categoryMap:
    category = {
        "Education": "27",
        "Tech": "28",
        "Music": "10",
        "Entertainment": "24",
        "Gaming": "20",
        "Lifestyle": "22"
    }


def getVideoAnalytics(video_url):

    def extract_video_id(url):
        parsed = urlparse(url)
        if "youtube.com" in parsed.netloc:
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [None])[0]
            elif "/shorts/" in parsed.path:
                return parsed.path.split("/shorts/")[1].split("?")[0]
        if "youtu.be" in parsed.netloc:
            return parsed.path.lstrip("/").split("?")[0]
        return None
    
    # Extract video ID
    video_id = extract_video_id(video_url)

    # Get video statistics
    video_stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet,contentDetails&id={video_id}&key={API_KEY}"
    video_data = requests.get(video_stats_url).json()

    if video_data["items"]:
        item = video_data["items"][0]
        stats = item["statistics"]
        snippet = item["snippet"]
        

        likes = stats.get("likeCount", "0")
        views = stats.get("viewCount", "0")
        comments = stats.get("commentCount", "0")
        date=snippet.get("publishedAt", "")
        details = item["contentDetails"]
        duration = isodate.parse_duration(details["duration"])
        video_length_minutes = round(duration.total_seconds() / 60, 2)
        category_id = snippet.get("categoryId", "")
        channel_id = snippet.get("channelId", "")

        mapCategory = categoryMap.category

        category = [key for key,value in mapCategory.items() if value==category_id]

        # 2. Get channel subscribers
        channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_id}&key={API_KEY}"
        channel_data = requests.get(channel_url).json()
        subscribers = channel_data["items"][0]["statistics"].get("subscriberCount", "0")
        video_date={'date':date}
        video_info = {
            'views' : views,
            'likes' : likes,
            'comments': comments,
            'watch_time_minutes': 0,  
            'video_length_minutes' : video_length_minutes,
            'subscribers' : subscribers,
            'category' : category[0],
            'engagement_rate': 0,
            'avg_watch_time_per_view': 0          

            
        }

        video_info['watch_time_minutes'] = round((video_length_minutes * int(views)) / 60, 2) 
        date=pd.to_datetime(date).date()       
        encode={'Education':0, 'Tech':1, 'Music':2, 'Entertainment':3, 'Gaming':4, 'Lifestyle':5}
        video_info['category'] = encode[video_info['category']]
        video_info['engagement_rate'] = (int(likes) + int(comments)) / int(views)
        video_info['avg_watch_time_per_view'] = video_info['watch_time_minutes'] / int(views) 
        
        # lf={'views': int(video_info['views']),
        #     'likes': int(video_info['likes']),
        #     'comments': int(video_info['comments']),
        #     'watch_time_minutes': video_info['watch_time_minutes'],
        #     'video_length_minutes': video_info['video_length_minutes'],
        #     'subscribers': int(video_info['subscribers']),
        #     'category': video_info['category'],        #     
        #     'engagement_rate': video_info['engagement_rate'],
        #     'avg_watch_time_per_view': video_info['avg_watch_time_per_view']
        #     }
        
        

        return video_info
    else:
        print("Video not found.")
    

st.set_page_config(layout='wide')
st.title('Youtube Video Ad revenue predictor')  

col1,col2 = st.columns(2)

with col1:
    with st.form('my_form'):
        st.subheader('paste the video link')
        video_url = st.text_input('video_url')
        submitted  = st.form_submit_button('Check')
        # st.video(video_url)
        if submitted:
            output = getVideoAnalytics(video_url)
        else : 
            output = None
    with st.container():
        if video_url:
            st.video(video_url)
        else:
            st.error("Video URL is missing.")

with col2:

    menu = option_menu(
        menu_title=None,
        options=[ "Linear Regression"],
        orientation="horizontal"
  )
    if menu == "Linear Regression":
        st.write("You selected:", menu)
        if output is not None:
            with st.container():
                st.subheader('Video Information')
                st.write(output)
                video_df = pd.DataFrame([output])
                video_df_scaled = scaler.transform(video_df)                
                prediction = gb.predict(video_df)
                st.subheader('Predicted Ad Revenue (USD)')
                data_frame=pd.DataFrame(prediction,columns=['Ad Revenue (USD)'])                
                st.write(f"${prediction[0]:.2f}")
                # st.subheader('Video Information')

                # st.text_area(label='Video_info',value=output)

    else:
        st.write("You selected:", menu)
        if output is not None:
            with st.container(height='content',border=True):
                st.subheader('Video Information')
                st.write(output)
                video_df = pd.DataFrame([output])
                video_df_scaled = scaler.transform(video_df)
                prediction = lr.predict(video_df)
                st.subheader('Predicted Ad Revenue (USD)')
                st.write(f"${prediction[0]:.2f}")
                # st.subheader('Video Information')

                # st.text_area(label='Video_info',value=output)
        else:
            st.info("Please select a regression model to see the prediction after submitting the video URL.")