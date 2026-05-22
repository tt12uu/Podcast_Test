import os
import xml.etree.ElementTree as ET
from datetime import datetime
import yt_dlp

# ==================== 已為你完成配置 ====================
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@DangerousPerson2.0" 
PODCAST_TITLE = "危險人物 Dangerous Person 2.0 (Audio)"
PODCAST_DESCRIPTION = "自動將 YouTube 頻道轉換為 iPhone Podcast 訂閱源"
# 這裡會自動抓取你 GitHub 的用戶名和倉庫名
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY', '').split('/')[0]
REPO_NAME = "dangerous-person-podcast"
MAX_EPISODES = 5 
# =======================================================

BASE_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
RSS_FILE = "podcast.xml"

def download_latest_videos():
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'docs/audio/%(id)s.%(ext)s',
        'playlistend': MAX_EPISODES,
        'ignoreerrors': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
    }
    
    os.makedirs('docs/audio', exist_ok=True)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(YOUTUBE_CHANNEL_URL, download=True)
        return info.get('entries', [])

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
    category = ET.SubElement(channel, "itunes:category")
    category.set("text", "True Crime")
    ET.SubElement(channel, "itunes:explicit").text = "yes"
    
    for video in videos:
        if not video: continue
        video_id = video.get('id')
        mp3_file = f"docs/audio/{video_id}.mp3"
        
        if os.path.exists(mp3_file):
            file_size = os.path.getsize(mp3_file)
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = video.get('title')
            ET.SubElement(item, "description").text = video.get('description', '無描述')
            ET.SubElement(item, "link").text = f"https://www.youtube.com/watch?v={video_id}"
            ET.SubElement(item, "guid", isPermaLink="false").text = video_id
            
            upload_date = video.get('upload_date')
            if upload_date:
                try:
                    dt = datetime.strptime(upload_date, "%Y%m%d")
                    pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
                except:
                    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
            else:
                pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
            ET.SubElement(item, "pubDate").text = pub_date
            
            enclosure = ET.SubElement(item, "enclosure")
            enclosure.set("url", f"{BASE_URL}audio/{video_id}.mp3")
            enclosure.set("length", str(file_size))
            enclosure.set("type", "audio/mpeg")
            
            duration = video.get('duration')
            if duration:
                ET.SubElement(item, "itunes:duration").text = str(int(duration))

    os.makedirs('docs', exist_ok=True)
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    tree.write(f"docs/{RSS_FILE}", encoding="utf-8", xml_declaration=True)
    print("🎉 RSS Feed Generated Successfully!")

if __name__ == "__main__":
    downloaded_entries = download_latest_videos()
    generate_rss(downloaded_entries)
