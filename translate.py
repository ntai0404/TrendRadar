import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

splitter_path = r'c:\SINHVIEN\myprocj\AAA-temp\26-5-26\TrendRadar\trendradar\notification\splitter.py'
splitter_replacements = [
    ("General news:", "Tổng tin tức:"),
    ("General News", "Tổng tin tức"),
    ("(New", " (Mới "),
    ("Tin Hot:", "Tin Hot:"),
    ("(", " (Nền tảng "),
    ("RSS：", "RSS:"),
    ("(Source", " (Nguồn "),
    ("Independent display:", "Nguồn độc lập:"),
    ("AI Analysis:", "AI Phân tích:"),
    ("all-day summary", "Tổng hợp ngày"),
    ("Current List", "Bảng xếp hạng hiện tại"),
    ("incremental analysis", "Phân tích mới"),
    ("Type:", "Loại:"),
    ("Time:", "Thời gian:"),
    ("Hot topic:", "Chủ đề hot nhất:"),
    ("Update time:", "Cập nhật lúc:"),
    ("TrendRadar discovered new version", "TrendRadar có phiên bản mới"),
    ("current", "hiện tại"),
    ("Hot word statistics", "Thống kê từ khóa hot"),
    ("Hot news statistics", "Thống kê tin hot"),
    ("No matching hot words", "Không có từ khóa hot nào phù hợp"),
    ("There are no new matching hot words in incremental mode", "Không có tin mới nào phù hợp"),
    ("There is no matching hot word in the current list mode", "Không có tin nào phù hợp"),
    ("New hot news this time", "Tin hot mới cập nhật"),
    ("AI Hotspot Analysis", "AI Phân tích điểm nóng"),
    ("article)", "tin)"),
    ("article)", "tin)"),
    ("article\n", "tin\n"),
    ("article\r\n", "tin\r\n"),
    ("Tiao", "tin"),
    ("( ", "(Tổng "),
    ("📰", "📰"),
    ("RSS Subscription Statistics", "Thống kê RSS"),
    ("Tin Hot")
]
replace_in_file(splitter_path, splitter_replacements)

batch_path = r'c:\SINHVIEN\myprocj\AAA-temp\26-5-26\TrendRadar\trendradar\notification\batch.py'
batch_replacements = [
    ("[{batch_num}/{total_batches} batches]", "[Phần {batch_num}/{total_batches}]")
]
replace_in_file(batch_path, batch_replacements)

print("Translation applied.")
