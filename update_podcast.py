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
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for video in videos:
        video_id = video['id']
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = video['title']
        
        desc_content = video['description'] if video['description'] else ''
        ET.SubElement(item, "description").text = desc_content
        
        content_encoded = ET.SubElement(item, "content:encoded")
        content_encoded.text = desc_content.replace('\n', '<br>')
        
        ET.SubElement(item, "link").text = f"https://www.youtube.com/watch?v={video_id}"
        ET.SubElement(item, "guid", isPermaLink="false").text = video_id
        
        # ───【方案 B 核心：動態獲取直連音訊與真實長度】───
        piped_info_url = f"https://pipedapi.adminforge.de/streams/{video_id}"
        stream_url = ""
        audio_length = "1024000"  # 預設保底 1MB
        
        print(f"正在解析影片音訊網址: {video_id}...")
        try:
            info_req = urllib.request.Request(piped_info_url, headers=headers)
            # 設定 8 秒 timeout 避免卡死
            with urllib.request.urlopen(info_req, timeout=8) as inf_res:
                video_data = json.loads(inf_res.read().decode('utf-8'))
                
                # 尋找可用的音訊串流
                if 'audioStreams' in video_data and len(video_data['audioStreams']) > 0:
                    # 優先取第一條音訊（通常是合適的 M4A 或 MP3 串流）
                    best_audio = video_data['audioStreams'][0]
                    stream_url = best_audio.get('url', '')
                    if 'contentLength' in best_audio and best_audio['contentLength']:
                        audio_length = str(best_audio['contentLength'])
                        print(f"  -> 成功獲取直連 URL，檔案長度: {audio_length} bytes")
        except Exception as e:
            print(f"  -> 請求 Piped API 失敗 ({e})，將採用保底代理解析網址。")
            
        # 如果 API 查不到或失敗，使用原保底網址
        if not stream_url:
            stream_url = f"https://pipedapi.adminforge.de/videoplayback?id={video_id}&itype=mp3"
        # ──────────────────────────────────────────────
        
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
        enclosure.set("type", "audio/mpeg")
        
        # 稍微緩衝 0.5 秒，避免連續高頻請求被 Piped 伺服器封鎖
        time.sleep(0.5)

    os.makedirs('docs', exist_ok=True)
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    tree.write(f"docs/{RSS_FILE}", encoding="utf-8", xml_declaration=True)
    print("🎉 方案 B RSS Feed 順利生成！音訊網址與長度已動態優化。")

if __name__ == "__main__":
    videos = get_latest_videos()
    generate_rss(videos)
