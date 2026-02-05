"""
Infrastructure Layer: Output Schemas

預設的輸出結構定義，用於 Structured Output API。
使用者可在 Notion 選擇這些預設格式，或選擇「自動推斷」讓 AI 生成。
"""

from typing import Dict


# 預設輸出格式定義 - 使用繁體中文欄位名稱
PRESET_SCHEMAS: Dict[str, dict] = {
    "標準摘要": {
        "type": "object",
        "properties": {
            "標題": {
                "type": "string",
                "description": "用一句話概括主題，15字以內"
            },
            "摘要": {
                "type": "string",
                "description": "重點摘要內容"
            },
            "標籤": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5個相關標籤"
            }
        },
        "required": ["標題", "摘要", "標籤"]
    },
    
    "圖片分析": {
        "type": "object",
        "properties": {
            "標題": {
                "type": "string",
                "description": "用一句話描述圖片內容，15字以內"
            },
            "描述": {
                "type": "string",
                "description": "3-5句話詳細描述圖片中的內容、場景、物體、人物、文字等"
            },
            "標籤": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5個相關標籤"
            }
        },
        "required": ["標題", "描述", "標籤"]
    },
    
    "行動清單": {
        "type": "object",
        "properties": {
            "標題": {
                "type": "string",
                "description": "用一句話概括主題，15字以內"
            },
            "重點摘要": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5個重點摘要"
            },
            "行動建議": {
                "type": "array",
                "items": {"type": "string"},
                "description": "可執行的行動建議"
            },
            "標籤": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5個相關標籤"
            }
        },
        "required": ["標題", "重點摘要", "行動建議", "標籤"]
    },
    
    "優缺點分析": {
        "type": "object",
        "properties": {
            "標題": {
                "type": "string",
                "description": "用一句話概括主題，15字以內"
            },
            "概述": {
                "type": "string",
                "description": "整體概述"
            },
            "優點": {
                "type": "array",
                "items": {"type": "string"},
                "description": "優點列表"
            },
            "缺點": {
                "type": "array",
                "items": {"type": "string"},
                "description": "缺點列表"
            },
            "總結": {
                "type": "string",
                "description": "總結評價"
            },
            "標籤": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5個相關標籤"
            }
        },
        "required": ["標題", "概述", "優點", "缺點", "總結", "標籤"]
    }
}


# 預設 Schema（當其他方式都失敗時使用）
DEFAULT_SCHEMA = PRESET_SCHEMAS["標準摘要"]


def get_preset_schema(format_name: str) -> dict:
    """
    取得預設的輸出結構。
    
    Args:
        format_name: 預設格式名稱（如「標準摘要」、「圖片分析」等）
        
    Returns:
        對應的 JSON Schema，若不存在則回傳預設 Schema
    """
    return PRESET_SCHEMAS.get(format_name, DEFAULT_SCHEMA)


def is_preset_format(format_name: str) -> bool:
    """
    檢查是否為預設格式。
    
    Args:
        format_name: 格式名稱
        
    Returns:
        True 如果是預設格式，False 如果需要自動推斷
    """
    return format_name in PRESET_SCHEMAS


def list_preset_formats() -> list:
    """
    列出所有可用的預設格式名稱。
    
    Returns:
        預設格式名稱列表
    """
    return list(PRESET_SCHEMAS.keys())
