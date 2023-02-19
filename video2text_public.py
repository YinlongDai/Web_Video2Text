#for reading url
import requests
import re  # 正则表达式
import pprint
import json
#for parse video
import speechmatics
from urllib.request import urlopen

headers = {
    'user-agent': 'video_web -> F12 -> Network -> Name'}

def send_request(url):
    response = requests.get(url=url, headers=headers)
    return response

def get_video_data(html_data):
    """解析视频数据"""

    # 提取视频的标题
    title = re.findall('<span class="tit">(.*?)</span>', html_data)
    #print(len(title))
    # print(title)

    # 提取视频对应的json数据
    json_data = re.findall('<script>window\.__playinfo__=(.*?)</script>', html_data)[0]
    # print(json_data)  # json_data 字符串
    json_data = json.loads(json_data)
    #pprint.pprint(json_data)

    # 提取音频的url地址
    audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
    i=1
    if (audio_url[0:27] != "https://upos-hz-mirrorakam.") & (i<2):
        audio_url = json_data['data']['dash']['audio'][i]['baseUrl']
    

    # 提取视频画面的url地址
    video_url = json_data['data']['dash']['video'][0]['baseUrl']
    if (video_url[0:27] != "https://upos-hz-mirrorakam.") & (i<2):
        video_url = json_data['data']['dash']['audio'][i]['baseUrl']
    

    video_data = [title, audio_url, video_url]
    return video_data

web_url = input("video_url:")
html_data = send_request(web_url).text
print('no problem')
video_data = get_video_data(html_data)
while (video_data[1][0:27]!="https://upos-hz-mirrorakam." or video_data[2][0:27]!="https://upos-hz-mirrorakam."):
    video_data = get_video_data(html_data)

print('解析到的音频地址:', video_data[1])
print('解析到的视频地址:', video_data[2])

#your own token
AUTH_TOKEN = 'Get your token from https://portal.speechmatics.com/home/'
LANGUAGE = "cmn"
CONNECTION_URL = f"wss://eu2.rt.speechmatics.com/v2/{LANGUAGE}"

# The raw audio stream will be a few seconds ahead of the radio
AUDIO_STREAM=video_data[1]  # LBC Radio stream

response = urlopen(AUDIO_STREAM)

# Create a transcription client
ws = speechmatics.client.WebsocketClient(
  speechmatics.models.ConnectionSettings(
    url=CONNECTION_URL,
    auth_token=AUTH_TOKEN,
    generate_temp_token=True, # Enterprise customers don't need to provide this parameter
  )
)

# Define an event handler to print the partial transcript
def print_partial_transcript(msg):
  print(f"(PART) {msg['metadata']['transcript']}")


# Define an event handler to print the full transcript
def print_transcript(msg):
  print(f"(FULL) {msg['metadata']['transcript']}")


# Register the event handler for partial transcript
ws.add_event_handler(
  event_name=speechmatics.models.ServerMessageType.AddPartialTranscript,
  event_handler=print_partial_transcript,
)

# Register the event handler for full transcript
ws.add_event_handler(
  event_name=speechmatics.models.ServerMessageType.AddTranscript,
  event_handler=print_transcript,
)

settings = speechmatics.models.AudioSettings()

# Define transcription parameters
conf = speechmatics.models.TranscriptionConfig(
  language=LANGUAGE,
  enable_partials=False,
)


ws.run_synchronously(response, conf, settings)