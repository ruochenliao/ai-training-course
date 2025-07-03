"""
分页工具模块
提供分页相关的工具函数
"""

import math
from typing import List, TypeVar, Generic
from ..schemas.common import PaginationResponse, PaginationParams
from ..core.config import settings


T = TypeVar('T')


class Paginator(Generic[T]):
    """分页器类"""
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
    
    @property
    def total_pages(self) -> int:
        """总页数"""
        return math.ceil(self.total / self.page_size) if self.total > 0 else 1
    
    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.page > 1
    
    @property
    def next_page(self) -> int:
        """下一页页码"""
        return self.page + 1 if self.has_next else self.page
    
    @property
    def prev_page(self) -> int:
        """上一页页码"""
        return self.page - 1 if self.has_prev else self.page
    
    @property
    def start_index(self) -> int:
        """当前页起始索引"""
        return (self.page - 1) * self.page_size + 1
    
    @property
    def end_index(self) -> int:
        """当前页结束索引"""
        end = self.page * self.page_size
        return min(end, self.total)
    
    def to_response(self) -> PaginationResponse[T]:
        """转换为分页响应"""
        from app.schemas.common import PaginationInfo

        pagination_info = PaginationInfo(
            total=self.total,
            page=self.page,
            page_size=self.page_size,
            total_pages=self.total_pages,
            has_next=self.has_next,
            has_prev=self.has_prev,
            start_index=self.start_index,
            end_index=self.end_index
        )

        return PaginationResponse(
            items=self.items,
            pagination=pagination_info,
            total=self.total,
            page=self.page,
            page_size=self.page_size,
            total_pages=self.total_pages,
            has_next=self.has_next,
            has_prev=self.has_prev
        )


def create_pagination_response(
    items: List[T],
    total: int,
    params: PaginationParams
) -> PaginationResponse[T]:
    """
    创建分页响应
    
    Args:
        items: 数据列表
        total: 总数量
        params: 分页参数
        
    Returns:
        PaginationResponse: 分页响应
    """
    paginator = Paginator(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size
    )
    return paginator.to_response()


def validate_pagination_params(params: PaginationParams) -> PaginationParams:
    """
    验证和修正分页参数
    
    Args:
        params: 分页参数
        
    Returns:
        PaginationParams: 修正后的分页参数
    """
    # 验证页码
    if params.page < 1:
        params.page = 1
    
    # 验证页面大小
    if params.page_size < 1:
        params.page_size = settings.PAGINATION_PAGE_SIZE
    elif params.page_size > settings.PAGINATION_MAX_PAGE_SIZE:
        params.page_size = settings.PAGINATION_MAX_PAGE_SIZE
    
    # 验证排序方向
    if params.sort_order not in ["asc", "desc"]:
        params.sort_order = "desc"
    
    return params


def calculate_offset(page: int, page_size: int) -> int:
    """
    计算偏移量
    
    Args:
        page: 页码
        page_size: 页面大小
        
    Returns:
        int: 偏移量
    """
    return (page - 1) * page_size


def calculate_limit(page_size: int) -> int:
    """
    计算限制数量
    
    Args:
        page_size: 页面大小
        
    Returns:
        int: 限制数量
    """
    return min(page_size, settings.PAGINATION_MAX_PAGE_SIZE)


class PaginationInfo:
    """分页信息类"""
    
    def __init__(self, total: int, page: int, page_size: int):
        self.total = total
        self.page = page
        self.page_size = page_size
    
    @property
    def total_pages(self) -> int:
        """总页数"""
        return math.ceil(self.total / self.page_size) if self.total > 0 else 1
    
    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.page > 1
    
    @property
    def offset(self) -> int:
        """偏移量"""
        return calculate_offset(self.page, self.page_size)
    
    @property
    def limit(self) -> int:
        """限制数量"""
        return calculate_limit(self.page_size)
    
    def get_page_numbers(self, window_size: int = 5) -> List[int]:
        """
        获取页码列表（用于分页导航）
        
        Args:
            window_size: 窗口大小
            
        Returns:
            List[int]: 页码列表
        """
        if self.total_pages <= window_size:
            return list(range(1, self.total_pages + 1))
        
        # 计算窗口范围
        half_window = window_size // 2
        start = max(1, self.page - half_window)
        end = min(self.total_pages, start + window_size - 1)
        
        # 调整起始位置
        if end - start + 1 < window_size:
            start = max(1, end - window_size + 1)
        
        return list(range(start, end + 1))
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
            "offset": self.offset,
            "limit": self.limit
        }


def paginate_list(items: List[T], page: int, page_size: int) -> tuple[List[T], PaginationInfo]:
    """
    对列表进行分页
    
    Args:
        items: 数据列表
        page: 页码
        page_size: 页面大小
        
    Returns:
        tuple: (分页后的数据, 分页信息)
    """
    total = len(items)
    info = PaginationInfo(total, page, page_size)
    
    start = info.offset
    end = start + info.limit
    paginated_items = items[start:end]
    
    return paginated_items, info
