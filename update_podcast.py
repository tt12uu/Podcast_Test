import os
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request

# ==================== 配置區域 ====================
CHANNEL_ID = "UCAlVuubC3GE6kFFeNBEkoUQ" 
PODCAST_TITLE = "危險人物 Dangerous Person 2.0 (Audio)"
PODCAST_DESCRIPTION = "自動將 YouTube 影片轉為 Podcast 訂閱源 (GitHub 本地託管)"
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY', '').split('/')[0]
REPO_NAME = "Podcast_Test"
# ==================================================

BASE_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
RSS_FILE = "podcast.xml"
AUDIO_DIR = "audio"

def get_latest_videos():
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        root = ET.fromstring(response.read())
        
        ns = {'ns': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015', 'media': 'http://search.yahoo.com/mrss/'}
        videos = []
        
        # 每次只取最新 3 集，防止 GitHub 空間爆炸
        for entry in root.findall('ns:entry', ns)[:3]:
            video_id = entry.find('yt:videoId', ns).text
            title = entry.find('ns:title', ns).text
            published = entry.find('ns:published', ns).text
            
            media_group = entry.find('media:group', ns)
            desc_text = media_group.find('media:description', ns).text if media_group is not None else ""
            
            if "#shorts" in title.lower():
                continue
                
            videos.append({'id': video_id, 'title': title, 'description': desc_text, 'published': published})
        return videos
    except Exception as e:
        print(f"❌ 獲取 YouTube 數據失敗: {e}")
        return []

def generate_rss(videos):
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = PODCAST_TITLE
    ET.SubElement(channel, "description").text = PODCAST_DESCRIPTION
    ET.SubElement(channel, "link").text = BASE_URL
    ET.SubElement(channel, "language").text = "zh-TW"
    ET.SubElement(channel, "itunes:author").text = "DK & Di掃"
    
    for video in videos:
        video_id = video['id']
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = video['title']
        ET.SubElement(item, "description").text = video['description']
        ET.SubElement(item, "guid", isPermaLink="false").text = video_id
        
        local_audio_filename = f"{video_id}.m4a"
        local_audio_path = os.path.join(AUDIO_DIR, local_audio_filename)
        github_audio_url = f"{BASE_URL}{AUDIO_DIR}/{local_audio_filename}"
        
        # 獲取檔案大小，如果 Actions 還沒下載完，先給個預設大小
        file_size = str(os.path.getsize(local_audio_path)) if os.path.exists(local_audio_path) else "35000000"
        
        try:
            dt = datetime.fromisoformat(video['published'].replace('Z', '+00:00'))
            pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except:
            pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
            
        ET.SubElement(item, "pubDate").text = pub_date
        
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", github_audio_url)
        enclosure.set("length", file_size)
        enclosure.set("type", "audio/mp4")
        
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)
    print("🎉 podcast.xml 骨架生成完畢！")

if __name__ == "__main__":
    videos = get_latest_videos()
    if videos:
        generate_rss(videos)
    else:
        print("⚠️ 無法取得 YouTube 影片清單，不進行更新。")
