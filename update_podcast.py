import os
import xml.etree.ElementTree as ET
from datetime import datetime

# ==================== 配置區域 ====================
PODCAST_TITLE = "危險人物 Dangerous Person 2.0 (Audio)"
PODCAST_DESCRIPTION = "自動將 YouTube 影片轉為 Podcast 訂閱源 (GitHub 本地託管)"
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY', '').split('/')[0]
REPO_NAME = "Podcast_Test"
# ==================================================

BASE_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
RSS_FILE = "podcast.xml"
AUDIO_DIR = "audio"

def generate_rss_from_local():
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = PODCAST_TITLE
    ET.SubElement(channel, "description").text = PODCAST_DESCRIPTION
    ET.SubElement(channel, "link").text = BASE_URL
    ET.SubElement(channel, "language").text = "zh-TW"
    ET.SubElement(channel, "itunes:author").text = "DK & Di掃"
    
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
        
    # 直接掃描本地 audio 資料夾入面由 yt-dlp 下載好嘅實體 m4a 檔案
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.m4a')]
    
    if not audio_files:
        print("⚠️ 本地目前沒有任何音訊檔案，跳過 RSS 生成。")
        return False

    for filename in audio_files:
        video_id = os.path.splitext(filename)[0]
        local_path = os.path.join(AUDIO_DIR, filename)
        
        item = ET.SubElement(channel, "item")
        # 標題暫用 ID 代替，當 App 載入時音訊只要對得準就播得
        ET.SubElement(item, "title").text = f"危險人物 2.0 - 單集 {video_id}"
        ET.SubElement(item, "description").text = "自建實體音訊自主託管"
        ET.SubElement(item, "guid", isPermaLink="false").text = video_id
        
        github_audio_url = f"{BASE_URL}{AUDIO_DIR}/{filename}"
        file_size = str(os.path.getsize(local_path))
        
        pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        ET.SubElement(item, "pubDate").text = pub_date
        
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", github_audio_url)
        enclosure.set("length", file_size) # 精準寫入實體檔案大小，Podcast 播放器最愛
        enclosure.set("type", "audio/mp4")
        
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)
    print(f"🎉 成功根據本地實體音訊生成 {len(audio_files)} 集的 podcast.xml！")
    return True

if __name__ == "__main__":
    generate_rss_from_local()
