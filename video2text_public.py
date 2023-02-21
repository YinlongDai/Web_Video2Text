import whisper
#for reading url
import requests
import re  # 正则表达式
import pprint
import json

import subprocess
import argparse

MODEL = ['tiny','base', 'small','medium', 'large']
STAMP = ['true', 'false']
SAVE = ['true', 'false']

def get_args():
  parser = argparse.ArgumentParser(description='Choose your parameters') 
  parser.add_argument('--model', '-m', default='base', type=str, choices=MODEL, help='model size')
  parser.add_argument('--language', '-l', default= 'NULL', type=str, help='language')
  parser.add_argument('--save', '-s', default='false', type=str, choices=STAMP, help='save to file')
  parser.add_argument('--stamp', '-t', default='true', type=str, choices=STAMP, help='show time stamp in file')
  args = parser.parse_args()
  return args

args = get_args()

#headers are only for BiliBili video url fetching
headers = {
    'user-agent': 'video_web -> F12 -> Network -> Name'}

#Functions for fetching BiliBili video url
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
    if (audio_url[0:27] != "https://upos-hz-mirrorakam.") & (i<3):
        audio_url = json_data['data']['dash']['audio'][i]['baseUrl']
        i+=1
    

    # 提取视频画面的url地址
    video_url = json_data['data']['dash']['video'][0]['baseUrl']
    if (video_url[0:27] != "https://upos-hz-mirrorakam.") & (i<3):
        video_url = json_data['data']['dash']['audio'][i]['baseUrl']
        i+=1
    

    video_data = [title, audio_url, video_url]
    return video_data

#time parsing
def convert(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return '%d:%02d:%02d' % (hour, min, sec)

#Input the webpage url
web_url = input("video_url:")

#check if the video if from Youtube or BiliBili:
if (web_url[0:23] == "https://www.youtube.com"):
    #run Youtuber subprocess
    f = open("youtuber_url.txt", "w")
    #fetch Youtube video url
    subprocess.call(['yt-dlp', '--skip-download','--get-url',web_url],stdout=f)
    f.close()
    f = open("youtuber_url.txt", "r")
    video_data  = f.readlines()
    print('解析到的音频地址:', video_data[1])
    f.close()
elif (web_url[0:24] == "https://www.bilibili.com"):
    html_data = send_request(web_url).text
    video_data = get_video_data(html_data)\
    #We have to keep fetching if the url does not work
    while (video_data[1][0:27]!="https://upos-hz-mirrorakam."):
        video_data = get_video_data(html_data)
    print('解析到的音频地址:', video_data[1])
    print('解析到的视频地址:', video_data[2])
else:
    print("Error: URL not supported.")


#use the models you choose 
model = whisper.load_model(args.model)

audio = whisper.load_audio(video_data[1][:-1])
audio1 = whisper.pad_or_trim(audio)

# make log-Mel spectrogram and move to the same device as the model
mel = whisper.log_mel_spectrogram(audio1).to(model.device)

if args.language == 'NULL':
  # detect the spoken language
  _, probs = model.detect_language(mel)
  language = f"{max(probs, key=probs.get)}"
  print("Detected language:",language)
else:
  language = args.language
  print("Transcribe in:"+language)

# decode the audio
#options = whisper.DecodingOptions()
#result = whisper.decode(model, mel, options)
result = model.transcribe(video_data[1][:-1], verbose = True, language = language)
# print the recognized text
#have to choose whether to include time stamp


if args.save == "true":
  f = open(result['segments'][0]['text'][:30]+".txt", "w", encoding="utf-8")
  if args.stamp == "true":
    for segment in result['segments']:
      start = convert(segment['start'])
      end = convert(segment['end'])
      f.write( '['+start+'-->'+end+']'+segment['text'] +'\n')
  else: 
    for segment in result['segmensts']:
      f.write(segment['text']+ '\n')  
  f.close()