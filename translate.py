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
    ("总新闻：", "Tổng tin tức:"),
    ("总新闻", "Tổng tin tức"),
    ("（新增", " (Mới "),
    ("热榜：", "Tin Hot:"),
    ("（平台", " (Nền tảng "),
    ("RSS：", "RSS:"),
    ("（源", " (Nguồn "),
    ("独立展示：", "Nguồn độc lập:"),
    ("AI 分析：", "AI Phân tích:"),
    ("全天汇总", "Tổng hợp ngày"),
    ("当前榜单", "Bảng xếp hạng hiện tại"),
    ("增量分析", "Phân tích mới"),
    ("类型：", "Loại:"),
    ("时间：", "Thời gian:"),
    ("最热话题：", "Chủ đề hot nhất:"),
    ("更新时间：", "Cập nhật lúc:"),
    ("TrendRadar 发现新版本", "TrendRadar có phiên bản mới"),
    ("当前", "hiện tại"),
    ("热点词汇统计", "Thống kê từ khóa hot"),
    ("热点新闻统计", "Thống kê tin hot"),
    ("暂无匹配的热点词汇", "Không có từ khóa hot nào phù hợp"),
    ("增量模式下暂无新增匹配的热点词汇", "Không có tin mới nào phù hợp"),
    ("当前榜单模式下暂无匹配的热点词汇", "Không có tin nào phù hợp"),
    ("本次新增热点新闻", "Tin hot mới cập nhật"),
    ("AI 热点分析", "AI Phân tích điểm nóng"),
    ("条）", "tin)"),
    ("条)", "tin)"),
    ("条\n", "tin\n"),
    ("条\r\n", "tin\r\n"),
    ("条", "tin"),
    ("(共 ", "(Tổng "),
    ("📰", "📰"),
    ("RSS 订阅统计", "Thống kê RSS"),
    ("热榜", "Tin Hot")
]
replace_in_file(splitter_path, splitter_replacements)

batch_path = r'c:\SINHVIEN\myprocj\AAA-temp\26-5-26\TrendRadar\trendradar\notification\batch.py'
batch_replacements = [
    ("[第 {batch_num}/{total_batches} 批次]", "[Phần {batch_num}/{total_batches}]")
]
replace_in_file(batch_path, batch_replacements)

print("Translation applied.")
