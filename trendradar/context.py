# coding=utf-8
"""
Module ngữ cảnh ứng dụng

Cung cấp lớp ngữ cảnh cấu hình, đóng gói tất cả các thao tác phụ thuộc vào cấu hình, loại bỏ trạng thái toàn cục và các hàm bao bọc.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from trendradar.utils.time import (
    DEFAULT_TIMEZONE,
    get_configured_time,
    format_date_folder,
    format_time_filename,
    get_current_time_display,
    convert_time_for_display,
    format_iso_time_friendly,
    is_within_days,
)
from trendradar.core import (
    load_frequency_words,
    matches_word_groups,
    read_all_today_titles,
    detect_latest_new_titles,
    count_word_frequency,
    Scheduler,
)
from trendradar.report import (
    prepare_report_data,
    generate_html_report,
    render_html_content,
)
from trendradar.notification import (
    render_feishu_content,
    render_dingtalk_content,
    split_content_into_batches,
    NotificationDispatcher,
)
from trendradar.ai import AITranslator
from trendradar.ai.filter import AIFilter, AIFilterResult
from trendradar.storage import get_storage_manager


class AppContext:
    """
    Lớp ngữ cảnh ứng dụng

    Đóng gói tất cả các thao tác phụ thuộc vào cấu hình, cung cấp một giao diện thống nhất.
    Loại bỏ sự phụ thuộc vào CONFIG toàn cục, cải thiện khả năng kiểm thử.

    Ví dụ sử dụng:
        config = load_config()
        ctx = AppContext(config)

        # Thao tác thời gian
        now = ctx.get_time()
        date_folder = ctx.format_date()

        # Thao tác lưu trữ
        storage = ctx.get_storage_manager()

        # Tạo báo cáo
        html = ctx.generate_html_report(stats, total_titles, ...)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Khởi tạo ngữ cảnh ứng dụng

        Args:
            config: Từ điển cấu hình hoàn chỉnh
        """
        self.config = config
        self._storage_manager = None
        self._scheduler = None

    # === Truy cập cấu hình ===

    @property
    def timezone(self) -> str:
        """Lấy múi giờ đã cấu hình"""
        return self.config.get("TIMEZONE", DEFAULT_TIMEZONE)

    @property
    def rank_threshold(self) -> int:
        """Lấy ngưỡng xếp hạng"""
        return self.config.get("RANK_THRESHOLD", 50)

    @property
    def weight_config(self) -> Dict:
        """Lấy cấu hình trọng số"""
        return self.config.get("WEIGHT_CONFIG", {})

    @property
    def platforms(self) -> List[Dict]:
        """Lấy danh sách cấu hình nền tảng"""
        return self.config.get("PLATFORMS", [])

    @property
    def platform_ids(self) -> List[str]:
        """Lấy danh sách ID nền tảng"""
        return [p["id"] for p in self.platforms]

    @property
    def rss_config(self) -> Dict:
        """Lấy cấu hình RSS"""
        return self.config.get("RSS", {})

    @property
    def rss_enabled(self) -> bool:
        """RSS có được bật hay không"""
        return self.rss_config.get("ENABLED", False)

    @property
    def rss_feeds(self) -> List[Dict]:
        """Lấy danh sách nguồn RSS"""
        return self.rss_config.get("FEEDS", [])

    @property
    def display_mode(self) -> str:
        """Lấy chế độ hiển thị (keyword | platform)"""
        return self.config.get("DISPLAY_MODE", "keyword")

    @property
    def show_new_section(self) -> bool:
        """Có hiển thị khu vực điểm nóng mới hay không"""
        return self.config.get("DISPLAY", {}).get("REGIONS", {}).get("NEW_ITEMS", True)

    @property
    def region_order(self) -> List[str]:
        """Lấy thứ tự hiển thị khu vực"""
        default_order = ["hotlist", "rss", "new_items", "standalone", "ai_analysis"]
        return self.config.get("DISPLAY", {}).get("REGION_ORDER", default_order)

    @property
    def filter_method(self) -> str:
        """Lấy chiến lược lọc: keyword | ai"""
        return self.config.get("FILTER", {}).get("METHOD", "keyword")

    @property
    def ai_priority_sort_enabled(self) -> bool:
        """Công tắc sắp xếp thẻ chế độ AI (tách biệt với sort_by_position_first của keyword)"""
        return self.config.get("FILTER", {}).get("PRIORITY_SORT_ENABLED", False)

    @property
    def ai_filter_config(self) -> Dict:
        """Lấy cấu hình lọc AI"""
        return self.config.get("AI_FILTER", {})

    @property
    def ai_filter_enabled(self) -> bool:
        """Lọc AI có được bật hay không (dựa trên filter.method)"""
        return self.filter_method == "ai"

    # === Thao tác thời gian ===

    def get_time(self) -> datetime:
        """Lấy thời gian của múi giờ được cấu hình hiện tại"""
        return get_configured_time(self.timezone)

    def format_date(self) -> str:
        """Định dạng thư mục ngày (YYYY-MM-DD)"""
        return format_date_folder(timezone=self.timezone)

    def format_time(self) -> str:
        """Định dạng tên tệp thời gian (HH-MM)"""
        return format_time_filename(self.timezone)

    def get_time_display(self) -> str:
        """Lấy hiển thị thời gian (HH:MM)"""
        return get_current_time_display(self.timezone)

    @staticmethod
    def convert_time_display(time_str: str) -> str:
        """Chuyển đổi HH-MM thành HH:MM"""
        return convert_time_for_display(time_str)

    # === Thao tác lưu trữ ===

    def get_storage_manager(self):
        """Lấy trình quản lý lưu trữ (khởi tạo trễ, singleton)"""
        if self._storage_manager is None:
            storage_config = self.config.get("STORAGE", {})
            remote_config = storage_config.get("REMOTE", {})
            local_config = storage_config.get("LOCAL", {})
            pull_config = storage_config.get("PULL", {})

            self._storage_manager = get_storage_manager(
                backend_type=storage_config.get("BACKEND", "auto"),
                data_dir=local_config.get("DATA_DIR", "output"),
                enable_txt=storage_config.get("FORMATS", {}).get("TXT", True),
                enable_html=storage_config.get("FORMATS", {}).get("HTML", True),
                remote_config={
                    "bucket_name": remote_config.get("BUCKET_NAME", ""),
                    "access_key_id": remote_config.get("ACCESS_KEY_ID", ""),
                    "secret_access_key": remote_config.get("SECRET_ACCESS_KEY", ""),
                    "endpoint_url": remote_config.get("ENDPOINT_URL", ""),
                    "region": remote_config.get("REGION", ""),
                },
                local_retention_days=local_config.get("RETENTION_DAYS", 0),
                remote_retention_days=remote_config.get("RETENTION_DAYS", 0),
                pull_enabled=pull_config.get("ENABLED", False),
                pull_days=pull_config.get("DAYS", 7),
                timezone=self.timezone,
            )
        return self._storage_manager

    def get_output_path(self, subfolder: str, filename: str) -> str:
        """Lấy đường dẫn đầu ra (cấu trúc phẳng: output/loại/ngày/tên_tệp)"""
        output_dir = Path("output") / subfolder / self.format_date()
        output_dir.mkdir(parents=True, exist_ok=True)
        return str(output_dir / filename)

    # === Xử lý dữ liệu ===

    def read_today_titles(
        self, platform_ids: Optional[List[str]] = None, quiet: bool = False
    ) -> Tuple[Dict, Dict, Dict]:
        """Đọc tất cả tiêu đề trong ngày"""
        return read_all_today_titles(self.get_storage_manager(), platform_ids, quiet=quiet)

    def detect_new_titles(
        self, platform_ids: Optional[List[str]] = None, quiet: bool = False
    ) -> Dict:
        """Phát hiện các tiêu đề mới thêm của đợt mới nhất"""
        return detect_latest_new_titles(self.get_storage_manager(), platform_ids, quiet=quiet)

    def is_first_crawl(self) -> bool:
        """Kiểm tra xem có phải là lần thu thập dữ liệu đầu tiên trong ngày hay không"""
        return self.get_storage_manager().is_first_crawl_today()

    # === Xử lý từ tần suất ===

    def load_frequency_words(
        self, frequency_file: Optional[str] = None
    ) -> Tuple[List[Dict], List[str], List[str]]:
        """Tải cấu hình từ tần suất"""
        return load_frequency_words(frequency_file)

    def matches_word_groups(
        self,
        title: str,
        word_groups: List[Dict],
        filter_words: List[str],
        global_filters: Optional[List[str]] = None,
    ) -> bool:
        """Kiểm tra xem tiêu đề có khớp với quy tắc cụm từ không"""
        return matches_word_groups(title, word_groups, filter_words, global_filters)

    # === Phân tích thống kê ===

    def count_frequency(
        self,
        results: Dict,
        word_groups: List[Dict],
        filter_words: List[str],
        id_to_name: Dict,
        title_info: Optional[Dict] = None,
        new_titles: Optional[Dict] = None,
        mode: str = "daily",
        global_filters: Optional[List[str]] = None,
        quiet: bool = False,
    ) -> Tuple[List[Dict], int]:
        """Thống kê tần suất từ"""
        return count_word_frequency(
            results=results,
            word_groups=word_groups,
            filter_words=filter_words,
            id_to_name=id_to_name,
            title_info=title_info,
            rank_threshold=self.rank_threshold,
            new_titles=new_titles,
            mode=mode,
            global_filters=global_filters,
            weight_config=self.weight_config,
            max_news_per_keyword=self.config.get("MAX_NEWS_PER_KEYWORD", 0),
            sort_by_position_first=self.config.get("SORT_BY_POSITION_FIRST", False),
            is_first_crawl_func=self.is_first_crawl,
            convert_time_func=self.convert_time_display,
            quiet=quiet,
        )

    # === Tạo báo cáo ===

    def prepare_report(
        self,
        stats: List[Dict],
        failed_ids: Optional[List] = None,
        new_titles: Optional[Dict] = None,
        id_to_name: Optional[Dict] = None,
        mode: str = "daily",
        frequency_file: Optional[str] = None,
    ) -> Dict:
        """Chuẩn bị dữ liệu báo cáo"""
        return prepare_report_data(
            stats=stats,
            failed_ids=failed_ids,
            new_titles=new_titles,
            id_to_name=id_to_name,
            mode=mode,
            rank_threshold=self.rank_threshold,
            matches_word_groups_func=self.matches_word_groups,
            load_frequency_words_func=lambda: self.load_frequency_words(frequency_file),
            show_new_section=self.show_new_section,
        )

    def generate_html(
        self,
        stats: List[Dict],
        total_titles: int,
        failed_ids: Optional[List] = None,
        new_titles: Optional[Dict] = None,
        id_to_name: Optional[Dict] = None,
        mode: str = "daily",
        update_info: Optional[Dict] = None,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[Any] = None,
        standalone_data: Optional[Dict] = None,
        frequency_file: Optional[str] = None,
        report_metadata: Optional[Dict] = None,
    ) -> str:
        """Tạo báo cáo HTML"""
        return generate_html_report(
            stats=stats,
            total_titles=total_titles,
            failed_ids=failed_ids,
            new_titles=new_titles,
            id_to_name=id_to_name,
            mode=mode,
            update_info=update_info,
            rank_threshold=self.rank_threshold,
            output_dir="output",
            date_folder=self.format_date(),
            time_filename=self.format_time(),
            render_html_func=lambda *args, **kwargs: self.render_html(*args, rss_items=rss_items, rss_new_items=rss_new_items, ai_analysis=ai_analysis, standalone_data=standalone_data, **kwargs),
            matches_word_groups_func=self.matches_word_groups,
            load_frequency_words_func=lambda: self.load_frequency_words(frequency_file),
            report_metadata=report_metadata,
        )

    def render_html(
        self,
        report_data: Dict,
        total_titles: int,
        mode: str = "daily",
        update_info: Optional[Dict] = None,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[Any] = None,
        standalone_data: Optional[Dict] = None,
    ) -> str:
        """Render nội dung HTML"""
        return render_html_content(
            report_data=report_data,
            total_titles=total_titles,
            mode=mode,
            update_info=update_info,
            region_order=self.region_order,
            get_time_func=self.get_time,
            rss_items=rss_items,
            rss_new_items=rss_new_items,
            display_mode=self.display_mode,
            ai_analysis=ai_analysis,
            show_new_section=self.show_new_section,
            standalone_data=standalone_data,
        )

    # === Render nội dung thông báo ===

    def render_feishu(
        self,
        report_data: Dict,
        update_info: Optional[Dict] = None,
        mode: str = "daily",
    ) -> str:
        """Render nội dung Feishu"""
        return render_feishu_content(
            report_data=report_data,
            update_info=update_info,
            mode=mode,
            separator=self.config.get("FEISHU_MESSAGE_SEPARATOR", "---"),
            region_order=self.region_order,
            get_time_func=self.get_time,
            show_new_section=self.show_new_section,
        )

    def render_dingtalk(
        self,
        report_data: Dict,
        update_info: Optional[Dict] = None,
        mode: str = "daily",
    ) -> str:
        """Render nội dung DingTalk"""
        return render_dingtalk_content(
            report_data=report_data,
            update_info=update_info,
            mode=mode,
            region_order=self.region_order,
            get_time_func=self.get_time,
            show_new_section=self.show_new_section,
        )

    def split_content(
        self,
        report_data: Dict,
        format_type: str,
        update_info: Optional[Dict] = None,
        max_bytes: Optional[int] = None,
        mode: str = "daily",
        rss_items: Optional[list] = None,
        rss_new_items: Optional[list] = None,
        ai_content: Optional[str] = None,
        standalone_data: Optional[Dict] = None,
        ai_stats: Optional[Dict] = None,
        report_type: str = "Báo cáo phân tích điểm nóng",
    ) -> List[str]:
        """Xử lý nội dung tin nhắn theo lô (hỗ trợ danh sách hot + gộp RSS + phân tích AI + khu vực hiển thị độc lập)

        Args:
            report_data: Dữ liệu báo cáo
            format_type: Loại định dạng
            update_info: Thông tin cập nhật
            max_bytes: Số byte tối đa
            mode: Chế độ báo cáo
            rss_items: Danh sách mục thống kê RSS
            rss_new_items: Danh sách mục RSS mới thêm
            ai_content: Nội dung phân tích AI (chuỗi đã render)
            standalone_data: Dữ liệu khu vực hiển thị độc lập
            ai_stats: Dữ liệu thống kê phân tích AI
            report_type: Loại báo cáo

        Returns:
            Danh sách nội dung tin nhắn sau khi chia lô
        """
        return split_content_into_batches(
            report_data=report_data,
            format_type=format_type,
            update_info=update_info,
            max_bytes=max_bytes,
            mode=mode,
            batch_sizes={
                "dingtalk": self.config.get("DINGTALK_BATCH_SIZE", 20000),
                "feishu": self.config.get("FEISHU_BATCH_SIZE", 29000),
                "default": self.config.get("MESSAGE_BATCH_SIZE", 4000),
            },
            feishu_separator=self.config.get("FEISHU_MESSAGE_SEPARATOR", "---"),
            region_order=self.region_order,
            get_time_func=self.get_time,
            rss_items=rss_items,
            rss_new_items=rss_new_items,
            timezone=self.config.get("TIMEZONE", DEFAULT_TIMEZONE),
            display_mode=self.display_mode,
            ai_content=ai_content,
            standalone_data=standalone_data,
            rank_threshold=self.rank_threshold,
            ai_stats=ai_stats,
            report_type=report_type,
            show_new_section=self.show_new_section,
        )

    # === Gửi thông báo ===

    def create_notification_dispatcher(self) -> NotificationDispatcher:
        """Tạo bộ lập lịch thông báo"""
        # Tạo trình dịch (nếu được bật)
        translator = None
        trans_config = self.config.get("AI_TRANSLATION", {})
        if trans_config.get("ENABLED", False):
            ai_config = self.config.get("AI", {})
            translator = AITranslator(trans_config, ai_config)

        return NotificationDispatcher(
            config=self.config,
            get_time_func=self.get_time,
            split_content_func=self.split_content,
            translator=translator,
        )

    def create_scheduler(self) -> Scheduler:
        """
        Tạo bộ lập lịch (khởi tạo trễ, singleton)

        Xây dựng dựa trên phần schedule của config.yaml + timeline.yaml.
        """
        if self._scheduler is None:
            schedule_config = self.config.get("SCHEDULE", {})
            timeline_data = self.config.get("_TIMELINE_DATA", {})

            self._scheduler = Scheduler(
                schedule_config=schedule_config,
                timeline_data=timeline_data,
                storage_backend=self.get_storage_manager(),
                get_time_func=self.get_time,
                fallback_report_mode=self.config.get("REPORT_MODE", "current"),
            )
        return self._scheduler

    # === Lọc thông minh AI ===

    @staticmethod
    def _with_ordered_priorities(tags: List[Dict], start_priority: int = 1) -> List[Dict]:
        """Bổ sung độ ưu tiên theo thứ tự danh sách hiện tại (giá trị càng nhỏ độ ưu tiên càng cao)"""
        normalized: List[Dict] = []
        priority = start_priority
        for tag_data in tags:
            if not isinstance(tag_data, dict):
                continue
            tag_name = str(tag_data.get("tag", "")).strip()
            if not tag_name:
                continue
            item = dict(tag_data)
            item["tag"] = tag_name
            item["priority"] = priority
            normalized.append(item)
            priority += 1
        return normalized

    def run_ai_filter(self, interests_file: Optional[str] = None) -> Optional[AIFilterResult]:
        """
        Thực thi toàn bộ quy trình lọc thông minh AI

        Args:
            interests_file: Tên tệp mô tả sở thích (nằm ở config/custom/ai/), None=sử dụng mặc định config/ai_interests.txt

        1. Đọc tệp mô tả sở thích, tính toán hash
        2. So sánh prompt_hash trong cơ sở dữ liệu, quyết định xem có trích xuất lại thẻ hay không
        3. Thu thập tin tức chờ phân loại (loại bỏ trùng lặp)
        4. Gọi phân loại AI theo nhóm batch_size
        5. Lưu kết quả
        6. Truy vấn kết quả active, nhóm theo nhãn và trả về

        Returns:
            AIFilterResult hoặc None (chưa bật hoặc có lỗi)
        """
        if not self.ai_filter_enabled:
            return None

        filter_config = self.ai_filter_config
        ai_config = self.config.get("AI", {})
        debug = self.config.get("DEBUG", False)

        # Tạo instance AIFilter
        ai_filter = AIFilter(ai_config, filter_config, self.get_time, debug)

        # Xác định tên tệp sở thích thực tế được sử dụng
        # None = Sử dụng mặc định config/ai_interests.txt, chỉ định tên tệp = config/custom/ai/{name}
        configured_interests = interests_file or filter_config.get("INTERESTS_FILE")
        effective_interests_file = configured_interests or "ai_interests.txt"

        if debug:
            print(f"[Lọc AI][DEBUG] === Thông tin cấu hình ===")
            print(f"[Lọc AI][DEBUG] Backend lưu trữ: {self.get_storage_manager().backend_name}")
            print(f"[Lọc AI][DEBUG] batch_size={filter_config.get('BATCH_SIZE', 200)}, "
                  f"batch_interval={filter_config.get('BATCH_INTERVAL', 5)}")
            print(f"[Lọc AI][DEBUG] interests_file={effective_interests_file}")
            print(f"[Lọc AI][DEBUG] prompt_file={filter_config.get('PROMPT_FILE', 'prompt.txt')}")
            print(f"[Lọc AI][DEBUG] extract_prompt_file={filter_config.get('EXTRACT_PROMPT_FILE', 'extract_prompt.txt')}")

        # 1. Đọc mô tả sở thích
        # Truyền configured_interests (có thể là None) cho load_interests_content,
        # Để nó phân biệt "tệp mặc định (config/ai_interests.txt)" và "tệp tùy chỉnh (config/custom/ai/)"
        interests_content = ai_filter.load_interests_content(configured_interests)
        if not interests_content:
            return AIFilterResult(success=False, error="Tệp mô tả sở thích trống hoặc không tồn tại")

        current_hash = ai_filter.compute_interests_hash(interests_content, effective_interests_file)
        storage = self.get_storage_manager()

        if debug:
            print(f"[Lọc AI][DEBUG] Hash mô tả sở thích: {current_hash}")
            print(f"[Lọc AI][DEBUG] Nội dung mô tả sở thích ({len(interests_content)} ký tự):\n{interests_content}")

        # 2. Bật chế độ hàng loạt (backend từ xa trì hoãn tải lên, tải lên đồng loạt sau khi hoàn tất mọi thao tác ghi)
        storage.begin_batch()

        # 3. Kiểm tra xem prompt có thay đổi không
        stored_hash = storage.get_latest_prompt_hash(interests_file=effective_interests_file)

        if debug:
            print(f"[Lọc AI][DEBUG] Hash lưu trữ cơ sở dữ liệu: {stored_hash}")
            print(f"[Lọc AI][DEBUG] so sánh hash: stored={stored_hash} vs current={current_hash} → {'Khớp' if stored_hash == current_hash else 'Không khớp'}")

        if stored_hash != current_hash:
            new_version = storage.get_latest_ai_filter_tag_version() + 1
            threshold = filter_config.get("RECLASSIFY_THRESHOLD", 0.6)

            if stored_hash is None:
                # Chạy lần đầu, trực tiếp trích xuất và lưu tất cả các thẻ
                print(f"[Lọc AI] Chạy lần đầu ({effective_interests_file}), trích xuất thẻ...")
                tags_data = ai_filter.extract_tags(interests_content)
                if not tags_data:
                    storage.end_batch()
                    return AIFilterResult(success=False, error="Trích xuất thẻ thất bại")
                tags_data = self._with_ordered_priorities(tags_data, start_priority=1)
                saved_count = storage.save_ai_filter_tags(tags_data, new_version, current_hash, interests_file=effective_interests_file)
                print(f"[Lọc AI] Đã lưu {saved_count} thẻ (phiên bản {new_version})")
            else:
                # Mô tả sở thích đã thay đổi, để AI so sánh thẻ cũ và sở thích mới, đưa ra phương án Cập nhật
                old_tags = storage.get_active_ai_filter_tags(interests_file=effective_interests_file)
                update_result = ai_filter.update_tags(old_tags, interests_content)

                if update_result is None:
                    # AI Cập nhật thẻ thất bại, quay lại trích xuất lại tất cả các thẻ
                    print(f"[Lọc AI] AI Cập nhật thẻ thất bại, quay lại trích xuất lại")
                    tags_data = ai_filter.extract_tags(interests_content)
                    if not tags_data:
                        storage.end_batch()
                        return AIFilterResult(success=False, error="Trích xuất thẻ thất bại")
                    tags_data = self._with_ordered_priorities(tags_data, start_priority=1)
                    deprecated_count = storage.deprecate_all_ai_filter_tags(interests_file=effective_interests_file)
                    storage.clear_analyzed_news(interests_file=effective_interests_file)
                    saved_count = storage.save_ai_filter_tags(tags_data, new_version, current_hash, interests_file=effective_interests_file)
                    print(f"[Lọc AI] Loại bỏ {deprecated_count} thẻ cũ, lưu {saved_count} thẻ mới (phiên bản {new_version})")
                else:
                    change_ratio = update_result["change_ratio"]
                    keep_tags = update_result["keep"]
                    add_tags = update_result["add"]
                    remove_tags = update_result["remove"]

                    if debug:
                        print(f"[Lọc AI][DEBUG] AI Cập nhật thẻ: keep={len(keep_tags)}, add={len(add_tags)}, remove={len(remove_tags)}, change_ratio={change_ratio:.2f}, threshold={threshold:.2f}")

                    if change_ratio >= threshold:
                        # Phân loại lại toàn bộ: loại bỏ tất cả thẻ cũ, dùng extract_tags để trích xuất lại
                        print(f"[Lọc AI] Tệp sở thích thay đổi: {effective_interests_file} (AI change_ratio={change_ratio:.2f} >= threshold={threshold:.2f} → Phân loại lại toàn bộ)")
                        tags_data = ai_filter.extract_tags(interests_content)
                        if not tags_data:
                            storage.end_batch()
                            return AIFilterResult(success=False, error="Trích xuất thẻ thất bại")
                        tags_data = self._with_ordered_priorities(tags_data, start_priority=1)
                        deprecated_count = storage.deprecate_all_ai_filter_tags(interests_file=effective_interests_file)
                        storage.clear_analyzed_news(interests_file=effective_interests_file)
                        saved_count = storage.save_ai_filter_tags(tags_data, new_version, current_hash, interests_file=effective_interests_file)
                        print(f"[Lọc AI] Loại bỏ {deprecated_count} thẻ cũ, lưu {saved_count} thẻ mới (phiên bản {new_version})")
                    else:
                        # Cập nhật thêm: thao tác theo chỉ thị của AI
                        print(f"[Lọc AI] Tệp sở thích thay đổi: {effective_interests_file} (AI change_ratio={change_ratio:.2f} < threshold={threshold:.2f} → Cập nhật thêm)")
                        print(f"[Lọc AI]   Giữ lại {len(keep_tags)} thẻ, thêm mới {len(add_tags)} thẻ, loại bỏ {len(remove_tags)} thẻ")

                        # Loại bỏ các thẻ được AI đánh dấu xóa
                        if remove_tags:
                            remove_set = set(remove_tags)
                            removed_ids = [t["id"] for t in old_tags if t["tag"] in remove_set]
                            if removed_ids:
                                storage.deprecate_specific_ai_filter_tags(removed_ids)
                                if debug:
                                    print(f"[Lọc AI][DEBUG] IDs thẻ bị loại bỏ: {removed_ids}")

                        # Cập nhật mô tả của các thẻ được giữ lại
                        keep_with_priority = []
                        if keep_tags:
                            storage.update_ai_filter_tag_descriptions(keep_tags, interests_file=effective_interests_file)
                            keep_with_priority = self._with_ordered_priorities(keep_tags, start_priority=1)
                            storage.update_ai_filter_tag_priorities(keep_with_priority, interests_file=effective_interests_file)

                        # Lưu các thẻ mới thêm
                        if add_tags:
                            add_start = keep_with_priority[-1]["priority"] + 1 if keep_with_priority else 1
                            add_with_priority = self._with_ordered_priorities(add_tags, start_priority=add_start)
                            saved_count = storage.save_ai_filter_tags(add_with_priority, new_version, current_hash, interests_file=effective_interests_file)
                            if debug:
                                print(f"[Lọc AI][DEBUG] Đã lưu thêm {saved_count} thẻ")

                        # Cập nhật hash của các thẻ được giữ lại (đánh dấu là đã xử lý)
                        storage.update_ai_filter_tags_hash(effective_interests_file, current_hash)

                        # Cập nhật thêm: xóa bản ghi phân tích của các tin tức không khớp, để chúng có cơ hội được phân tích lại bởi tập thẻ mới
                        if add_tags:
                            cleared = storage.clear_unmatched_analyzed_news(interests_file=effective_interests_file)
                            if cleared > 0:
                                print(f"[Lọc AI]   Đã xóa {cleared} bản ghi không khớp, sẽ được phân tích lại dưới các thẻ mới")

        # 3. Lấy các thẻ active hiện tại
        active_tags = storage.get_active_ai_filter_tags(interests_file=effective_interests_file)
        if debug:
            print(f"[Lọc AI][DEBUG] Lấy các thẻ active từ cơ sở dữ liệu: {len(active_tags)} thẻ")
            for t in active_tags:
                print(f"[Lọc AI][DEBUG]   id={t['id']} tag={t['tag']} priority={t.get('priority', 9999)} version={t.get('version')} hash={t.get('prompt_hash', '')[:8]}...")

        if not active_tags:
            storage.end_batch()
            return AIFilterResult(success=False, error="Không có thẻ nào khả dụng")

        print(f"[Lọc AI] Sử dụng {len(active_tags)} thẻ")

        # 4. Thu thập tin tức chờ phân loại
        # Danh sách hot
        all_news = storage.get_all_news_ids()
        analyzed_hotlist = storage.get_analyzed_news_ids("hotlist", interests_file=effective_interests_file)
        pending_news = [n for n in all_news if n["id"] not in analyzed_hotlist]

        # RSS (lọc theo độ mới trước, sau đó loại bỏ những tin đã phân loại)
        pending_rss = []
        freshness_filtered_rss = 0
        if self.rss_enabled:
            all_rss = storage.get_all_rss_ids()

            # Áp dụng lọc theo độ mới (giống với giai đoạn đẩy)
            rss_config = self.rss_config
            freshness_config = rss_config.get("FRESHNESS_FILTER", {})
            freshness_enabled = freshness_config.get("ENABLED", True)
            default_max_age_days = freshness_config.get("MAX_AGE_DAYS", 3)
            timezone = self.config.get("TIMEZONE", DEFAULT_TIMEZONE)

            # Xây dựng ánh xạ feed_id -> max_age_days
            feed_max_age_map = {}
            for feed_cfg in self.rss_feeds:
                feed_id = feed_cfg.get("id", "")
                max_age = feed_cfg.get("max_age_days")
                if max_age is not None:
                    try:
                        feed_max_age_map[feed_id] = int(max_age)
                    except (ValueError, TypeError):
                        pass

            fresh_rss = []
            for n in all_rss:
                published_at = n.get("published_at", "")
                feed_id = n.get("source_id", "")
                max_days = feed_max_age_map.get(feed_id, default_max_age_days)
                if freshness_enabled and max_days > 0 and published_at:
                    if not is_within_days(published_at, max_days, timezone):
                        freshness_filtered_rss += 1
                        continue
                fresh_rss.append(n)

            analyzed_rss = storage.get_analyzed_news_ids("rss", interests_file=effective_interests_file)
            pending_rss = [n for n in fresh_rss if n["id"] not in analyzed_rss]

        # Luôn in dữ liệu chi tiết về tổng số/đã phân tích/chờ phân tích
        hotlist_total = len(all_news)
        hotlist_skipped = len(analyzed_hotlist)
        hotlist_pending = len(pending_news)
        print(f"[Lọc AI] Danh sách hot: Tổng cộng {hotlist_total} tin, đã phân tích bỏ qua {hotlist_skipped} tin, gửi phân tích AI lần này {hotlist_pending} tin")
        if self.rss_enabled:
            rss_total = len(all_rss)
            rss_skipped = len(analyzed_rss)
            rss_pending = len(pending_rss)
            freshness_info = f", lọc theo độ mới {freshness_filtered_rss} tin" if freshness_filtered_rss > 0 else ""
            print(f"[Lọc AI] RSS: Tổng cộng {rss_total} tin{freshness_info}, đã phân tích bỏ qua {rss_skipped} tin, gửi phân tích AI lần này {rss_pending} tin")

        total_pending = len(pending_news) + len(pending_rss)
        if total_pending == 0:
            print("[AI Lọc] Không có tin tức mới nào cần phân loại")

        # 5. Phân loại hàng loạt
        batch_size = filter_config.get("BATCH_SIZE", 200)
        batch_interval = filter_config.get("BATCH_INTERVAL", 5)
        total_results = []
        batch_count = 0  # Đếm số batch toàn cục qua hot trend và RSS

        # Xử lý hot trend
        for i in range(0, len(pending_news), batch_size):
            if batch_count > 0 and batch_interval > 0:
                import time
                print(f"[AI Lọc] Khoảng thời gian chờ giữa các batch là {batch_interval} giây...")
                time.sleep(batch_interval)
            batch = pending_news[i:i + batch_size]
            titles_for_ai = [
                {"id": n["id"], "title": n["title"], "source": n.get("source_name", "")}
                for n in batch
            ]
            batch_results = ai_filter.classify_batch(titles_for_ai, active_tags, interests_content)
            for r in batch_results:
                r["source_type"] = "hotlist"
            total_results.extend(batch_results)
            batch_count += 1
            print(f"[AI Lọc] Batch hot trend {i // batch_size + 1}: {len(batch)} mục → {len(batch_results)} mục khớp")

        # Xử lý RSS
        for i in range(0, len(pending_rss), batch_size):
            if batch_count > 0 and batch_interval > 0:
                import time
                print(f"[AI Lọc] Khoảng thời gian chờ giữa các batch là {batch_interval} giây...")
                time.sleep(batch_interval)
            batch = pending_rss[i:i + batch_size]
            titles_for_ai = [
                {"id": n["id"], "title": n["title"], "source": n.get("source_name", "")}
                for n in batch
            ]
            batch_results = ai_filter.classify_batch(titles_for_ai, active_tags, interests_content)
            for r in batch_results:
                r["source_type"] = "rss"
            total_results.extend(batch_results)
            batch_count += 1
            print(f"[AI Lọc] Batch RSS {i // batch_size + 1}: {len(batch)} mục → {len(batch_results)} mục khớp")

        # 6. Lưu kết quả
        if total_results:
            saved = storage.save_ai_filter_results(total_results)
            print(f"[AI Lọc] Lưu {saved} kết quả phân loại")
            if debug and saved != len(total_results):
                print(f"[AI Lọc][DEBUG] !! Số lượng lưu không khớp: mong đợi {len(total_results)}, thực tế {saved} (có thể các bản ghi trùng lặp đã bị bỏ qua)")

        # 6.5 Ghi lại tất cả tin tức đã phân tích (khớp + không khớp, dùng để loại bỏ trùng lặp)
        matched_hotlist_ids = {r["news_item_id"] for r in total_results if r.get("source_type") == "hotlist"}
        matched_rss_ids = {r["news_item_id"] for r in total_results if r.get("source_type") == "rss"}

        if pending_news:
            hotlist_ids = [n["id"] for n in pending_news]
            storage.save_analyzed_news(
                hotlist_ids, "hotlist", effective_interests_file,
                current_hash, matched_hotlist_ids
            )

        if pending_rss:
            rss_ids = [n["id"] for n in pending_rss]
            storage.save_analyzed_news(
                rss_ids, "rss", effective_interests_file,
                current_hash, matched_rss_ids
            )

        if pending_news or pending_rss:
            total_analyzed = len(pending_news) + len(pending_rss)
            total_matched = len(matched_hotlist_ids) + len(matched_rss_ids)
            print(f"[AI Lọc] Đã ghi lại trạng thái phân tích của {total_analyzed} tin tức (khớp {total_matched}, không khớp {total_analyzed - total_matched})")

        # 7. Kết thúc chế độ hàng loạt (tải đồng loạt cơ sở dữ liệu lên lưu trữ từ xa)
        storage.end_batch()

        # 8. Truy vấn và lắp ráp kết quả trả về
        all_results = storage.get_active_ai_filter_results(interests_file=effective_interests_file)

        if debug:
            print(f"[AI Lọc][DEBUG] === Tổng hợp cuối cùng ===")
            print(f"[AI Lọc][DEBUG] Kết quả phân loại active trong cơ sở dữ liệu: {len(all_results)} mục")
            # Thống kê theo thẻ
            tag_counts: dict = {}
            for r in all_results:
                tag_name = r.get("tag", "?")
                src_type = r.get("source_type", "?")
                key = f"{tag_name}({src_type})"
                tag_counts[key] = tag_counts.get(key, 0) + 1
            for key, count in sorted(tag_counts.items()):
                print(f"[AI Lọc][DEBUG]   {key}: {count} mục")

        return self._build_filter_result(all_results, active_tags, total_pending)

    def _build_filter_result(
        self,
        raw_results: List[Dict],
        tags: List[Dict],
        total_processed: int,
    ) -> AIFilterResult:
        """Lắp ráp kết quả truy vấn cơ sở dữ liệu thành AIFilterResult"""
        priority_sort_enabled = self.ai_priority_sort_enabled
        tag_priority_map = {}
        for idx, t in enumerate(tags, start=1):
            tag_name = str(t.get("tag", "")).strip() if isinstance(t, dict) else ""
            if not tag_name:
                continue
            try:
                tag_priority_map[tag_name] = int(t.get("priority", idx))
            except (TypeError, ValueError):
                tag_priority_map[tag_name] = idx

        # Nhóm theo thẻ
        tag_groups: Dict[str, Dict] = {}
        seen_titles: Dict[str, set] = {}  # Loại bỏ trùng lặp dưới mỗi thẻ

        for r in raw_results:
            tag_name = r["tag"]
            if tag_name not in tag_groups:
                raw_priority = r.get("tag_priority", tag_priority_map.get(tag_name, 9999))
                try:
                    tag_position = int(raw_priority)
                except (TypeError, ValueError):
                    tag_position = 9999
                tag_groups[tag_name] = {
                    "tag": tag_name,
                    "description": r.get("tag_description", ""),
                    "position": tag_position,
                    "count": 0,
                    "items": [],
                }
                seen_titles[tag_name] = set()

            title = r["title"]
            if title in seen_titles[tag_name]:
                continue
            seen_titles[tag_name].add(title)

            tag_groups[tag_name]["items"].append({
                "title": title,
                "source_id": r.get("source_id", ""),
                "source_name": r.get("source_name", ""),
                "url": r.get("url", ""),
                "mobile_url": r.get("mobile_url", ""),
                "rank": r.get("rank", 0),
                "ranks": r.get("ranks", []),
                "first_time": r.get("first_time", ""),
                "last_time": r.get("last_time", ""),
                "count": r.get("count", 1),
                "relevance_score": r.get("relevance_score", 0),
                "source_type": r.get("source_type", "hotlist"),
            })
            tag_groups[tag_name]["count"] += 1

        # Sắp xếp theo cấu hình: ưu tiên vị trí / ưu tiên số lượng
        if priority_sort_enabled:
            sorted_tags = sorted(
                tag_groups.values(),
                key=lambda x: (x.get("position", 9999), -x["count"], x["tag"]),
            )
        else:
            sorted_tags = sorted(
                tag_groups.values(),
                key=lambda x: (-x["count"], x.get("position", 9999), x["tag"]),
            )

        total_matched = sum(t["count"] for t in sorted_tags)

        return AIFilterResult(
            tags=sorted_tags,
            total_matched=total_matched,
            total_processed=total_processed,
            success=True,
        )

    def convert_ai_filter_to_report_data(
        self,
        ai_filter_result: AIFilterResult,
        mode: str = "daily",
        new_titles: Optional[Dict] = None,
        rss_new_urls: Optional[set] = None,
    ) -> tuple:
        """
        Chuyển đổi kết quả lọc AI thành cấu trúc dữ liệu giống với khớp từ khóa

        Mỗi tag trong AIFilterResult.tags tương ứng với một "word" (nhóm từ khóa).
        Các mục có source_type="hotlist" trong tag.items sẽ vào stats của hotlist,
        Các mục có source_type="rss" sẽ vào stats của rss_items.

        Args:
            ai_filter_result: Kết quả lọc AI
            mode: Chế độ báo cáo ("daily" | "current" | "incremental")
            new_titles: Tiêu đề mới thêm vào hotlist {source_id: {title: data}}, dùng để kiểm tra is_new
            rss_new_urls: Tập hợp URL của các mục RSS mới thêm, dùng để kiểm tra is_new

        Returns:
            (hotlist_stats, rss_stats):
            - hotlist_stats: Định dạng đầu ra giống với count_word_frequency()
            - rss_stats: Định dạng giống với rss_items
        """
        hotlist_stats = []
        rss_stats = []
        max_news = self.config.get("MAX_NEWS_PER_KEYWORD", 0)
        min_score = self.ai_filter_config.get("MIN_SCORE", 0)

        # Chế độ current: tính toán thời gian mới nhất, chỉ giữ lại các tin tức hiện đang trên hotlist
        # Căn chỉnh với logic lọc của count_word_frequency(mode="current")
        latest_time = None
        if mode == "current":
            for tag_data in ai_filter_result.tags:
                for item in tag_data.get("items", []):
                    if item.get("source_type", "hotlist") == "hotlist":
                        last_time = item.get("last_time", "")
                        if last_time and (latest_time is None or last_time > latest_time):
                            latest_time = last_time
            if latest_time:
                print(f"[Lọc AI] Chế độ current: thời gian mới nhất {latest_time}, lọc các tin tức đã rớt khỏi hotlist")

        # Cấu hình lọc độ mới của RSS (giống với giai đoạn push)
        rss_config = self.rss_config
        freshness_config = rss_config.get("FRESHNESS_FILTER", {})
        freshness_enabled = freshness_config.get("ENABLED", True)
        default_max_age_days = freshness_config.get("MAX_AGE_DAYS", 3)
        timezone = self.config.get("TIMEZONE", DEFAULT_TIMEZONE)

        feed_max_age_map = {}
        for feed_cfg in self.rss_feeds:
            feed_id = feed_cfg.get("id", "")
            max_age = feed_cfg.get("max_age_days")
            if max_age is not None:
                try:
                    feed_max_age_map[feed_id] = int(max_age)
                except (ValueError, TypeError):
                    pass

        filtered_count = 0
        for tag_data in ai_filter_result.tags:
            tag_name = tag_data.get("tag", "")
            items = tag_data.get("items", [])
            if not items:
                continue

            hotlist_titles = []
            rss_titles = []

            for item in items:
                source_type = item.get("source_type", "hotlist")

                # Chế độ current: bỏ qua các tin tức đã rớt khỏi hotlist
                if mode == "current" and latest_time and source_type == "hotlist":
                    if item.get("last_time", "") != latest_time:
                        filtered_count += 1
                        continue

                # Lọc theo ngưỡng điểm: bỏ qua các tin tức có độ liên quan thấp hơn min_score
                if min_score > 0:
                    score = item.get("relevance_score", 0)
                    if score < min_score:
                        continue

                # Xây dựng hiển thị thời gian
                first_time = item.get("first_time", "")
                last_time = item.get("last_time", "")
                if source_type == "rss":
                    # Lọc độ mới RSS: Bỏ qua các bài viết cũ vượt quá max_age_days
                    if freshness_enabled and first_time:
                        feed_id = item.get("source_id", "")
                        max_days = feed_max_age_map.get(feed_id, default_max_age_days)
                        if max_days > 0 and not is_within_days(first_time, max_days, timezone):
                            continue

                    # Mục RSS: first_time ở định dạng ISO, hiển thị bằng định dạng thân thiện
                    if first_time:
                        time_display = format_iso_time_friendly(first_time, timezone, include_date=True)
                    else:
                        time_display = ""
                else:
                    # Mục danh sách hot: Sử dụng định dạng [HH:MM ~ HH:MM] (nhất quán với chế độ keyword)
                    if first_time and last_time and first_time != last_time:
                        first_display = convert_time_for_display(first_time)
                        last_display = convert_time_for_display(last_time)
                        time_display = f"[{first_display} ~ {last_display}]"
                    elif first_time:
                        time_display = convert_time_for_display(first_time)
                    else:
                        time_display = ""

                # Tính toán is_new (căn chỉnh với chế độ keyword core/analyzer.py:335-342)
                if source_type == "rss":
                    is_new = False
                    if rss_new_urls:
                        item_url = item.get("url", "")
                        is_new = item_url in rss_new_urls if item_url else False
                else:
                    is_new = False
                    if new_titles:
                        item_source_id = item.get("source_id", "")
                        item_title = item.get("title", "")
                        if item_source_id in new_titles:
                            is_new = item_title in new_titles[item_source_id]

                # Trong chế độ incremental, chỉ giữ lại các mục mới trúng đích trong vòng này.
                # run_ai_filter() trả về tập kết quả active, do đó ở đây cần
                # lọc bỏ rõ ràng các mục cũ đã trúng đích trong lịch sử để căn chỉnh với hành vi của chế độ keyword.
                if mode == "incremental" and not is_new:
                    continue

                title_entry = {
                    "title": item.get("title", ""),
                    "source_name": item.get("source_name", ""),
                    "url": item.get("url", ""),
                    "mobile_url": item.get("mobile_url", ""),
                    "ranks": item.get("ranks", []),
                    "rank_threshold": self.rank_threshold,
                    "count": item.get("count", 1),
                    "is_new": is_new,
                    "time_display": time_display,
                    "matched_keyword": tag_name,
                }

                if source_type == "rss":
                    rss_titles.append(title_entry)
                else:
                    hotlist_titles.append(title_entry)

            if hotlist_titles:
                if max_news > 0:
                    hotlist_titles = hotlist_titles[:max_news]
                hotlist_stats.append({
                    "word": tag_name,
                    "count": len(hotlist_titles),
                    "position": tag_data.get("position", 9999),
                    "titles": hotlist_titles,
                })

            if rss_titles:
                if max_news > 0:
                    rss_titles = rss_titles[:max_news]
                rss_stats.append({
                    "word": tag_name,
                    "count": len(rss_titles),
                    "position": tag_data.get("position", 9999),
                    "titles": rss_titles,
                })

        if mode == "current" and filtered_count > 0:
            total_kept = sum(s["count"] for s in hotlist_stats)
            print(f"[Lọc AI] chế độ current: Đã lọc {filtered_count} tin tức rớt hạng, giữ lại {total_kept} tin tức đang trong bảng xếp hạng")

        if min_score > 0:
            hotlist_kept = sum(s["count"] for s in hotlist_stats)
            rss_kept = sum(s["count"] for s in rss_stats)
            total_kept = hotlist_kept + rss_kept
            parts = [f"Danh sách hot {hotlist_kept} mục"]
            if rss_kept > 0:
                parts.append(f"RSS {rss_kept} mục")
            print(f"[Lọc AI] Lọc theo điểm: min_score={min_score}, giữ lại {total_kept} mục có score≥{min_score} ({', '.join(parts)})")

        priority_sort_enabled = self.ai_priority_sort_enabled
        if priority_sort_enabled:
            hotlist_stats.sort(key=lambda x: (x.get("position", 9999), -x["count"], x["word"]))
            rss_stats.sort(key=lambda x: (x.get("position", 9999), -x["count"], x["word"]))
        else:
            hotlist_stats.sort(key=lambda x: (-x["count"], x.get("position", 9999), x["word"]))
            rss_stats.sort(key=lambda x: (-x["count"], x.get("position", 9999), x["word"]))

        return hotlist_stats, rss_stats

    # === Dọn dẹp tài nguyên ===

    def cleanup(self):
        """Dọn dẹp tài nguyên"""
        if self._storage_manager:
            self._storage_manager.cleanup_old_data()
            self._storage_manager.cleanup()
            self._storage_manager = None
