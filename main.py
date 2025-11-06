import requests
import re
from pathlib import Path
import time
import os
import json
from tqdm import tqdm
def indexM3U8(domain,videoid,fanclubname):    
    url=f"https://api.{domain}/fc/video_pages/{videoid}/session_ids"
    if fanclubname==0:
        FCdata = requests.get(f"https://{domain}/site/settings.json").json()
        FCid= FCdata["fanclub_site_id"]
    else:
        FCid=str(requests.get("https://api.nicochannel.jp/fc/content_providers/channel_domain?current_site_domain=https://nicochannel.jp/"+fanclubname).json()["data"]["content_providers"]["id"])
    headers = {
        "Accept":"application/json, text/plain, */*",
        "Accept-Encoding":"gzip, deflate, br, zstd",
        "Cache-Control":"no-cache",
        "Connection":"keep-alive",
        "Content-Length":"2",
        "Content-Type":"application/json",
        "fc_site_id":FCid,
        "fc_use_device":"null",
        "Origin":f"https://{domain}",
        "Pragma":"no-cache",
        "Priority":"u=4",
        "Referer":f"https://{domain}",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-site",
        "TE":"trailers"
    }
    time.sleep(0.25)
    res = requests.post(url,headers=headers,json={})
    if res.status_code==200:
        session_id=res.json()["data"]["session_id"]
        indexm3u8url=f"https://hls-auth.cloud.stream.co.jp/auth/index.m3u8?session_id={session_id}"
        return [indexm3u8url,session_id,domain,videoid,fanclubname]
    else:
        return 0

def M3U8encode(url,session_id,domain,videoid,fanclubname):
    m3u8 = requests.get(url).text
    FullQualityURL=m3u8[m3u8.find("https://"):m3u8.find("#",m3u8.find("https://"))]                    
    media_view_id=FullQualityURL[FullQualityURL.find("media_view_id=")+14:FullQualityURL.find('"',FullQualityURL.find("media_view_id=")+14)]
    headers={
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Origin": f"https://{domain}",
    "Connection": "keep-alive",
    "Referer": f"https://{domain}",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "TE": "trailers"
    }
    keyurl = f"https://hls-auth.cloud.stream.co.jp/key?session_id={session_id}&media_view_id={media_view_id}"
    key = requests.get(keyurl,headers=headers).content
    Fullm3u8 = requests.get(FullQualityURL).text
    if fanclubname!=0:
        os.makedirs(f"./{domain}/{fanclubname}",exist_ok=True)
        KEY = open(f"./{domain}/{fanclubname}/{videoid}.bin","wb")
        KEY.write(key)
        KEY.close()
        M3U8 = open(f"./{domain}/{fanclubname}/{videoid}.m3u8","w")
        M3U8.write(Fullm3u8.replace(keyurl,f'./{videoid}.bin"\n').replace('.key"A"','.key"'))
        M3U8.close()
    else:
        os.makedirs(f"./{domain}",exist_ok=True)
        KEY = open(f"./{domain}/{videoid}.bin","wb")
        KEY.write(key)
        KEY.close()
        M3U8 = open(f"./{domain}/{videoid}.m3u8","w")
        M3U8.write(Fullm3u8.replace(keyurl,f'./{videoid}.bin"\n').replace('.key"A"','.key"'))
        M3U8.close()

    return [key,keyurl,Fullm3u8,videoid] 


def getvideopage(domain,fcname):
 if fcname!=0:
    FCid=str(requests.get(f"https://api.nicochannel.jp/fc/content_providers/channel_domain?current_site_domain=https://nicochannel.jp/{fcname}").json()["data"]["content_providers"]["id"])
    p = Path(f"./{domain}/{fcname}")
    file = [f.stem for f in p.glob("*.m3u8")]
 else:
     FCid=requests.get("https://"+domain+"/site/settings.json").json()["fanclub_site_id"]
     p = Path(f"./{domain}")
     file = [f.stem for f in p.glob("*.m3u8")]
 headers = {
        "Cache-Control":"no-cache",
        "Connection":"keep-alive",
        "Content-Length":"2",
        "Content-Type":"application/json",
        "fc_use_device":"null",
        "Origin":"https://"+domain,
        "Pragma":"no-cache",
        "Priority":"u=4",
        "Referer":"https://"+domain,
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-site",
        "TE":"trailers"
    }

 videoidlist=[]
 videoinfos=[]
 x=1
 while True:
        videoinfo=  requests.get(f"https://api.{domain}/fc/v2/fanclub_sites/{FCid}/video_pages?sort=-display_date&vod_type=0&per_page=100&page={x}",headers=headers,json={}).json()         
        for i in range(len(videoinfo["data"]["video_pages"]["list"])):
            freeflg = str(videoinfo["data"]["video_pages"]["list"][i]["start_with_free_part_flg"])#'False'
            freeper = str(videoinfo["data"]["video_pages"]["list"][i]["video_free_periods"])#"[]"
            videodel = str(videoinfo["data"]["video_pages"]["list"][i]["video_delivery_target"]["id"])#"vod_origin":

            if freeflg=="True" or freeper!="[]" or videodel =="2":
                videoinfos.append(videoinfo["data"]["video_pages"]["list"][i])  
                if videoinfo["data"]["video_pages"]["list"][i]["content_code"] not in file:
                   
                   videoidlist.append(videoinfo["data"]["video_pages"]["list"][i]["content_code"]) 
                 
        x+=1
        if len(videoinfo["data"]["video_pages"]["list"])<100:break
 return [videoidlist,videoinfos]

def start(url):
 spliturl=[p for p in url.split('/') if p]
 spliturl.remove("https:")
 if len(spliturl)==2:
   domain = spliturl[0]
   fanclubname=spliturl[1]
   videoidinfo=getvideopage(domain,fanclubname)
 else:
   domain = spliturl[0]
   fanclubname=0
   videoidinfo=getvideopage(domain,fanclubname)
 time.sleep(0.5)
 #videoidlist = [v for v in videoidinfo[0] if v not in file]
 for i in tqdm(range(len(videoidinfo[0]))):
     if fanclubname!=0:
        indexm3u8=indexM3U8(domain,videoidinfo[0][i],fanclubname)
        if indexm3u8!=0:
            M3U8encode(*indexm3u8)
     else:
        indexm3u8=indexM3U8(domain,videoidinfo[0][i],fanclubname)
        if indexm3u8!=0:
           M3U8encode(*indexm3u8)
 if fanclubname==0:
      JSON = open("./"+domain+".json","w")
      MAP = open("jsonmap.txt","a")
      MAP.write("/"+domain+"\n")
      JSON.write(json.dumps(videoidinfo[1]))
      JSON.close()
      MAP.close()
 else:
     JSON = open("./"+domain+"/"+fanclubname+".json","w")
     MAP = open("jsonmap.txt","a")
     JSON.write(json.dumps(videoidinfo[1]))
     MAP.write("/"+domain+"/"+fanclubname+"\n")
     JSON.close()  
     MAP.close()


URL = open("url.txt","r")
all=URL.read().split("\n")
for i in range(len(all)):
    if all[i].strip():
        print(all[i])
        start(all[i])