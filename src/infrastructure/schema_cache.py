"""
Infrastructure Layer: Schema Cache

快取已生成的 Schema，避免重複呼叫 AI。
使用 Prompt 雜湊值驗證 Prompt 是否有變更。
"""

import hashlib
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CachedSchema:
    """快取的 Schema 資料"""
    schema: dict
    prompt_hash: str


class SchemaCache:
    """
    Schema 快取管理器。
    
    依據分類（category）快取已生成的 Schema，
    並透過 Prompt 雜湊值驗證 Prompt 是否有變更。
    """
    
    def __init__(self):
        """初始化快取"""
        self._cache: Dict[str, CachedSchema] = {}
    
    @staticmethod
    def compute_hash(prompt: str) -> str:
        """
        計算 Prompt 的雜湊值。
        
        Args:
            prompt: Prompt 內容
            
        Returns:
            MD5 雜湊字串
        """
        return hashlib.md5(prompt.encode('utf-8')).hexdigest()
    
    def get(self, category: str, prompt: str) -> Optional[dict]:
        """
        取得快取的 Schema。
        
        Args:
            category: 分類名稱
            prompt: 目前的 Prompt（用於驗證是否有變更）
            
        Returns:
            快取的 Schema，若不存在或 Prompt 已變更則回傳 None
        """
        if category not in self._cache:
            return None
        
        cached = self._cache[category]
        current_hash = self.compute_hash(prompt)
        
        # 驗證 Prompt 是否有變更
        if cached.prompt_hash != current_hash:
            print(f"⚠️ [SchemaCache] Prompt 已變更，需重新生成 Schema: {category}")
            # 移除過期的快取
            del self._cache[category]
            return None
        
        print(f"✅ [SchemaCache] 命中快取: {category}")
        return cached.schema
    
    def set(self, category: str, schema: dict, prompt: str) -> None:
        """
        儲存 Schema 到快取。
        
        Args:
            category: 分類名稱
            schema: 要快取的 Schema
            prompt: 對應的 Prompt（用於計算雜湊值）
        """
        prompt_hash = self.compute_hash(prompt)
        self._cache[category] = CachedSchema(
            schema=schema,
            prompt_hash=prompt_hash
        )
        print(f"📦 [SchemaCache] 已快取 Schema: {category}")
    
    def invalidate(self, category: str) -> None:
        """
        使特定分類的快取失效。
        
        Args:
            category: 要使失效的分類名稱
        """
        if category in self._cache:
            del self._cache[category]
            print(f"🗑️ [SchemaCache] 已清除快取: {category}")
    
    def clear(self) -> None:
        """清除所有快取"""
        self._cache.clear()
        print("🗑️ [SchemaCache] 已清除所有快取")
    
    def get_cached_categories(self) -> list:
        """
        取得所有已快取的分類名稱。
        
        Returns:
            已快取的分類名稱列表
        """
        return list(self._cache.keys())
