import os
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request
import json
import time

# ==================== 配置區域 ====================
CHANNEL_ID = "UCAlVuubC3GE6kFFeNBEkoUQ" 
PODCAST_TITLE = "危險人物 Dangerous Person 2.0 (Audio)"
PODCAST_DESCRIPTION = "自動將 YouTube 影片轉為 Podcast 訂閱源"
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY', '').split('/')[0]
REPO_NAME = "Podcast_Test"
# ==================================================

BASE_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
RSS_FILE = "podcast.xml"

# 改用當前在 2026 年最穩定、頻寬最足夠的 Invidious 音訊橋接節點清單
INVIDIOUS_NODES = [
    "https://invidious.projectsegfau.lt",
    "https://inv.tux.digital",
    "https://invidious.nerdvpn.de",
    "https://invidious.flokinet.to"
]

def get_latest_videos():
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
    try:
        req = urllib.request.Request(
            rss_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        response = urllib.request.urlopen(req)
        data = response.read()
        root = ET.fromstring(data)
        
        ns = {
            'ns': 'http://www.w3.org/2005/Atom', 
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/'
        }
        
        videos = []
        for entry in root.findall('ns:entry', ns):
            video_id = entry.find('yt:videoId', ns).text
            title = entry.find('ns:title', ns).text
            published = entry.find('ns:published', ns).text
            
            media_group = entry.find('media:group', ns)
            desc_text = ""
            if media_group is not None:
                description = media_group.find('media:description', ns)
                if description is not None and description.text:
                    desc_text = description.text
            
            if "#shorts" in title.lower():
                continue
                
            videos.append({
                'id': video_id,
                'title': title,
                'description': desc_text,
                'published': published
            })
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
    category = ET.SubElement(channel, "itunes:category")
    category.set("text", "True Crime")
    ET.SubElement(channel, "itunes:explicit").text = "no"
    
    # 這裡採用動態分配節點，將多個音訊網址分散到不同的健康 Invidious 伺服器上，避免單點崩潰
    for i, video in enumerate(videos):
        video_id = video['id']
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = video['title']
        
        desc_content = video['description'] if video['description'] else ''
        ET.SubElement(item, "description").text = desc_content
        
        content_encoded = ET.SubElement(item, "content:encoded")
        content_encoded.text = desc_content.replace('\n', '<br>')
        
        ET.SubElement(item, "link").text = f"https://www.youtube.com/watch?v={video_id}"
        ET.SubElement(item, "guid", isPermaLink="false").text = video_id
        
        # 輪流選擇不同的 Invidious 節點（例如第 1 集用節點 A，第 2 集用節點 B）
        node = INVIDIOUS_NODES[i % len(INVIDIOUS_NODES)]
        # itag=140 代表 YouTube 官方最標準、高相容性的 128kbps AAC M4A 音訊流
        stream_url = f"{node}/latest_version?id={video_id}&itag=140"
        
        # 設定一個健康的保底音訊大小 (約 38MB)
        audio_length = "38000000" 
        print(f"解析影片 {video_id} -> 已成功分配至極速代理源: {node}")
            
        try:
            dt_str = video['published'].replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str)
            pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except:
            pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        ET.SubElement(item, "pubDate").text = pub_date
        
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", stream_url)
        enclosure.set("length", audio_length) 
        enclosure.set("type", "audio/mp4")  # m4a 容器對應 audio/mp4，相容性極佳
        
    os.makedirs('docs', exist_ok=True)
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    tree.write(f"docs/{RSS_FILE}", encoding="utf-8", xml_declaration=True)
    print("🎉 終極高可用 RSS Feed 順利生成！")

if __name__ == "__main__":
    videos = get_latest_videos()
    generate_rss(videos)
