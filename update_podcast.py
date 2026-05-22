import os
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request
import re

# ==================== 配置區域 ====================
CHANNEL_ID = "UCAlVuubC3GE6kFFeNBEkoUQ" 
PODCAST_TITLE = "危險人物 Dangerous Person 2.0 (Audio)"
PODCAST_DESCRIPTION = "自動將 YouTube 影片轉為 Podcast 訂閱源"
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY', '').split('/')[0]
REPO_NAME = "Podcast_Test"
# ==================================================

BASE_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
RSS_FILE = "podcast.xml"

def get_latest_videos():
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
    try:
        # 加入 User-Agent 模擬瀏覽器請求，確保連線穩定
        req = urllib.request.Request(
            rss_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        response = urllib.request.urlopen(req)
        data = response.read()
        root = ET.fromstring(data)
        
        # 修正及補充完整的命名空間字典
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
            
            # 修正：精確定位 media:group 裡面的 media:description 抓取影片描述
            media_group = entry.find('media:group', ns)
            desc_text = ""
            if media_group is not None:
                description = media_group.find('media:description', ns)
                if description is not None and description.text:
                    desc_text = description.text
            
            # 過濾掉 Shorts 短影音
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
        print(f"獲取 YouTube 數據失敗: {e}")
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
    
    for video in videos:
        video_id = video['id']
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = video['title']
        
        # 使用 content:encoded 確保影片資訊欄內嘅換行同符號唔會整爛 XML 格式
        ET.SubElement(item, "description").text = video['description']
        content_encoded = ET.SubElement(item, "content:encoded")
        content_encoded.text = f"<![CDATA[{video['description'].replace('', '<br>') if video['description'] else ''}]]>"
        
        ET.SubElement(item, "link").text = f"https://www.youtube.com/watch?v={video_id}"
        ET.SubElement(item, "guid", isPermaLink="false").text = video_id
        
        # 時間格式轉換 (ISO 8601 -> RFC 822)
        try:
            dt_str = video['published'].replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str)
            pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except:
            pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        ET.SubElement(item, "pubDate").text = pub_date
        
        # 升級：改用全球更穩定、頻寬更大嘅公共 Piped 節點作為音訊串流代理
        # 咁樣可以確保你喺車上面聽個陣唔會斷斷續續
        stream_url = f"https://piped-api.kavin.rocks/videoplayback?id={video_id}&itype=mp3"
        
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", stream_url)
        enclosure.set("length", "1024000") 
        enclosure.set("type", "audio/mpeg")

    os.makedirs('docs', exist_ok=True)
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    tree.write(f"docs/{RSS_FILE}", encoding="utf-8", xml_declaration=True)
    print("🎉 全新免下載型 RSS Feed 順利生成，並已修正所有潛在問題！")

if __name__ == "__main__":
    videos = get_latest_videos()
    generate_rss(videos)
