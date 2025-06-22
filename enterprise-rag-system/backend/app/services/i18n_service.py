"""
国际化支持服务
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any

from loguru import logger

from app.core.exceptions import I18nException


class SupportedLanguage(Enum):
    """支持的语言"""
    ZH_CN = "zh-CN"
    EN_US = "en-US"
    JA_JP = "ja-JP"
    KO_KR = "ko-KR"
    FR_FR = "fr-FR"
    DE_DE = "de-DE"
    ES_ES = "es-ES"
    RU_RU = "ru-RU"


@dataclass
class LanguageInfo:
    """语言信息"""
    code: str
    name: str
    native_name: str
    flag: str
    rtl: bool = False
    enabled: bool = True


@dataclass
class TranslationKey:
    """翻译键"""
    key: str
    namespace: str = "common"
    default_value: str = ""
    description: str = ""
    context: str = ""


class I18nService:
    """国际化服务类"""
    
    def __init__(self):
        """初始化国际化服务"""
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.languages: Dict[str, LanguageInfo] = {}
        self.default_language = SupportedLanguage.ZH_CN.value
        self.fallback_language = SupportedLanguage.EN_US.value
        
        # 初始化支持的语言
        self._init_supported_languages()
        
        # 加载翻译文件
        self._load_translations()
        
        logger.info("国际化服务初始化完成")
    
    def _init_supported_languages(self):
        """初始化支持的语言"""
        self.languages = {
            SupportedLanguage.ZH_CN.value: LanguageInfo(
                code="zh-CN",
                name="Chinese (Simplified)",
                native_name="简体中文",
                flag="🇨🇳"
            ),
            SupportedLanguage.EN_US.value: LanguageInfo(
                code="en-US",
                name="English (United States)",
                native_name="English",
                flag="🇺🇸"
            ),
            SupportedLanguage.JA_JP.value: LanguageInfo(
                code="ja-JP",
                name="Japanese",
                native_name="日本語",
                flag="🇯🇵"
            ),
            SupportedLanguage.KO_KR.value: LanguageInfo(
                code="ko-KR",
                name="Korean",
                native_name="한국어",
                flag="🇰🇷"
            ),
            SupportedLanguage.FR_FR.value: LanguageInfo(
                code="fr-FR",
                name="French",
                native_name="Français",
                flag="🇫🇷"
            ),
            SupportedLanguage.DE_DE.value: LanguageInfo(
                code="de-DE",
                name="German",
                native_name="Deutsch",
                flag="🇩🇪"
            ),
            SupportedLanguage.ES_ES.value: LanguageInfo(
                code="es-ES",
                name="Spanish",
                native_name="Español",
                flag="🇪🇸"
            ),
            SupportedLanguage.RU_RU.value: LanguageInfo(
                code="ru-RU",
                name="Russian",
                native_name="Русский",
                flag="🇷🇺"
            )
        }
    
    def _load_translations(self):
        """加载翻译文件"""
        try:
            # 翻译文件目录
            translations_dir = Path(__file__).parent.parent / "i18n" / "locales"
            
            if not translations_dir.exists():
                translations_dir.mkdir(parents=True, exist_ok=True)
                self._create_default_translations(translations_dir)
            
            # 加载每种语言的翻译文件
            for lang_code in self.languages.keys():
                lang_file = translations_dir / f"{lang_code}.json"
                
                if lang_file.exists():
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                else:
                    # 创建默认翻译文件
                    self.translations[lang_code] = self._get_default_translations(lang_code)
                    self._save_translation_file(lang_code, self.translations[lang_code])
                    
        except Exception as e:
            logger.error(f"加载翻译文件失败: {e}")
            # 使用内置默认翻译
            self._load_builtin_translations()
    
    def _create_default_translations(self, translations_dir: Path):
        """创建默认翻译文件"""
        for lang_code in self.languages.keys():
            translations = self._get_default_translations(lang_code)
            self._save_translation_file(lang_code, translations)
    
    def _get_default_translations(self, lang_code: str) -> Dict[str, Any]:
        """获取默认翻译"""
        if lang_code == SupportedLanguage.ZH_CN.value:
            return {
                "common": {
                    "yes": "是",
                    "no": "否",
                    "ok": "确定",
                    "cancel": "取消",
                    "save": "保存",
                    "delete": "删除",
                    "edit": "编辑",
                    "add": "添加",
                    "search": "搜索",
                    "loading": "加载中...",
                    "error": "错误",
                    "success": "成功",
                    "warning": "警告",
                    "info": "信息"
                },
                "auth": {
                    "login": "登录",
                    "logout": "退出",
                    "register": "注册",
                    "username": "用户名",
                    "password": "密码",
                    "email": "邮箱",
                    "forgot_password": "忘记密码",
                    "login_success": "登录成功",
                    "login_failed": "登录失败",
                    "invalid_credentials": "用户名或密码错误"
                },
                "knowledge_base": {
                    "title": "知识库",
                    "create": "创建知识库",
                    "name": "知识库名称",
                    "description": "描述",
                    "documents": "文档",
                    "upload_document": "上传文档",
                    "processing": "处理中",
                    "processed": "已处理",
                    "failed": "处理失败"
                },
                "chat": {
                    "title": "智能问答",
                    "input_placeholder": "请输入您的问题...",
                    "send": "发送",
                    "thinking": "思考中...",
                    "no_results": "未找到相关信息",
                    "sources": "参考来源",
                    "new_conversation": "新对话"
                },
                "analytics": {
                    "title": "数据分析",
                    "overview": "概览",
                    "users": "用户",
                    "documents": "文档",
                    "conversations": "对话",
                    "total_users": "总用户数",
                    "total_documents": "总文档数",
                    "total_conversations": "总对话数",
                    "growth_rate": "增长率"
                }
            }
        elif lang_code == SupportedLanguage.EN_US.value:
            return {
                "common": {
                    "yes": "Yes",
                    "no": "No",
                    "ok": "OK",
                    "cancel": "Cancel",
                    "save": "Save",
                    "delete": "Delete",
                    "edit": "Edit",
                    "add": "Add",
                    "search": "Search",
                    "loading": "Loading...",
                    "error": "Error",
                    "success": "Success",
                    "warning": "Warning",
                    "info": "Information"
                },
                "auth": {
                    "login": "Login",
                    "logout": "Logout",
                    "register": "Register",
                    "username": "Username",
                    "password": "Password",
                    "email": "Email",
                    "forgot_password": "Forgot Password",
                    "login_success": "Login successful",
                    "login_failed": "Login failed",
                    "invalid_credentials": "Invalid username or password"
                },
                "knowledge_base": {
                    "title": "Knowledge Base",
                    "create": "Create Knowledge Base",
                    "name": "Knowledge Base Name",
                    "description": "Description",
                    "documents": "Documents",
                    "upload_document": "Upload Document",
                    "processing": "Processing",
                    "processed": "Processed",
                    "failed": "Processing Failed"
                },
                "chat": {
                    "title": "Intelligent Q&A",
                    "input_placeholder": "Please enter your question...",
                    "send": "Send",
                    "thinking": "Thinking...",
                    "no_results": "No relevant information found",
                    "sources": "Sources",
                    "new_conversation": "New Conversation"
                },
                "analytics": {
                    "title": "Analytics",
                    "overview": "Overview",
                    "users": "Users",
                    "documents": "Documents",
                    "conversations": "Conversations",
                    "total_users": "Total Users",
                    "total_documents": "Total Documents",
                    "total_conversations": "Total Conversations",
                    "growth_rate": "Growth Rate"
                }
            }
        else:
            # 其他语言使用英文作为基础
            return self._get_default_translations(SupportedLanguage.EN_US.value)
    
    def _save_translation_file(self, lang_code: str, translations: Dict[str, Any]):
        """保存翻译文件"""
        try:
            translations_dir = Path(__file__).parent.parent / "i18n" / "locales"
            translations_dir.mkdir(parents=True, exist_ok=True)
            
            lang_file = translations_dir / f"{lang_code}.json"
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存翻译文件失败: {e}")
    
    def _load_builtin_translations(self):
        """加载内置翻译"""
        for lang_code in self.languages.keys():
            self.translations[lang_code] = self._get_default_translations(lang_code)
    
    def get_translation(
        self,
        key: str,
        lang_code: str = None,
        namespace: str = "common",
        default: str = None,
        **kwargs
    ) -> str:
        """获取翻译"""
        try:
            if not lang_code:
                lang_code = self.default_language
            
            # 检查语言是否支持
            if lang_code not in self.translations:
                lang_code = self.fallback_language
            
            # 获取翻译
            translations = self.translations.get(lang_code, {})
            namespace_translations = translations.get(namespace, {})
            
            # 支持嵌套键，如 "user.profile.name"
            keys = key.split('.')
            value = namespace_translations
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    value = None
                    break
            
            # 如果没找到翻译，尝试回退语言
            if value is None and lang_code != self.fallback_language:
                return self.get_translation(key, self.fallback_language, namespace, default, **kwargs)
            
            # 如果还是没找到，使用默认值
            if value is None:
                value = default or key
            
            # 处理参数插值
            if isinstance(value, str) and kwargs:
                try:
                    value = value.format(**kwargs)
                except (KeyError, ValueError):
                    pass
            
            return str(value)
            
        except Exception as e:
            logger.error(f"获取翻译失败: {e}")
            return default or key
    
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """获取支持的语言列表"""
        return [
            {
                "code": lang_info.code,
                "name": lang_info.name,
                "native_name": lang_info.native_name,
                "flag": lang_info.flag,
                "rtl": lang_info.rtl,
                "enabled": lang_info.enabled
            }
            for lang_info in self.languages.values()
            if lang_info.enabled
        ]
    
    def is_language_supported(self, lang_code: str) -> bool:
        """检查语言是否支持"""
        return lang_code in self.languages and self.languages[lang_code].enabled
    
    def detect_language(self, text: str) -> str:
        """检测文本语言"""
        try:
            # 简单的语言检测逻辑
            # 实际应用中应该使用专业的语言检测库
            
            # 检测中文字符
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            total_chars = len(text)
            
            if total_chars > 0 and chinese_chars / total_chars > 0.3:
                return SupportedLanguage.ZH_CN.value
            
            # 检测日文字符
            japanese_chars = len([c for c in text if '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff'])
            if total_chars > 0 and japanese_chars / total_chars > 0.1:
                return SupportedLanguage.JA_JP.value
            
            # 检测韩文字符
            korean_chars = len([c for c in text if '\uac00' <= c <= '\ud7af'])
            if total_chars > 0 and korean_chars / total_chars > 0.1:
                return SupportedLanguage.KO_KR.value
            
            # 默认返回英文
            return SupportedLanguage.EN_US.value
            
        except Exception as e:
            logger.error(f"语言检测失败: {e}")
            return self.default_language
    
    def add_translation(
        self,
        lang_code: str,
        key: str,
        value: str,
        namespace: str = "common"
    ) -> bool:
        """添加翻译"""
        try:
            if lang_code not in self.translations:
                self.translations[lang_code] = {}
            
            if namespace not in self.translations[lang_code]:
                self.translations[lang_code][namespace] = {}
            
            # 支持嵌套键
            keys = key.split('.')
            current = self.translations[lang_code][namespace]
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
            
            # 保存到文件
            self._save_translation_file(lang_code, self.translations[lang_code])
            
            return True
            
        except Exception as e:
            logger.error(f"添加翻译失败: {e}")
            return False
    
    def get_missing_translations(self, lang_code: str) -> List[str]:
        """获取缺失的翻译"""
        try:
            if lang_code not in self.translations:
                return []
            
            base_translations = self.translations.get(self.default_language, {})
            target_translations = self.translations.get(lang_code, {})
            
            missing = []
            
            def check_missing(base_dict, target_dict, prefix=""):
                for key, value in base_dict.items():
                    current_key = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, dict):
                        if key not in target_dict or not isinstance(target_dict[key], dict):
                            missing.append(current_key)
                        else:
                            check_missing(value, target_dict[key], current_key)
                    else:
                        if key not in target_dict:
                            missing.append(current_key)
            
            for namespace, translations in base_translations.items():
                if namespace not in target_translations:
                    missing.append(namespace)
                else:
                    check_missing(translations, target_translations[namespace], namespace)
            
            return missing
            
        except Exception as e:
            logger.error(f"获取缺失翻译失败: {e}")
            return []


# 全局国际化服务实例
i18n_service = I18nService()


# 便捷函数
def t(key: str, lang_code: str = None, namespace: str = "common", default: str = None, **kwargs) -> str:
    """翻译函数的简写"""
    return i18n_service.get_translation(key, lang_code, namespace, default, **kwargs)


def get_user_language(accept_language: str = None) -> str:
    """从HTTP Accept-Language头获取用户语言偏好"""
    if not accept_language:
        return i18n_service.default_language
    
    # 解析Accept-Language头
    languages = []
    for lang in accept_language.split(','):
        parts = lang.strip().split(';')
        lang_code = parts[0].strip()
        
        # 提取质量值
        quality = 1.0
        if len(parts) > 1:
            for part in parts[1:]:
                if part.strip().startswith('q='):
                    try:
                        quality = float(part.strip()[2:])
                    except ValueError:
                        pass
        
        languages.append((lang_code, quality))
    
    # 按质量值排序
    languages.sort(key=lambda x: x[1], reverse=True)
    
    # 找到第一个支持的语言
    for lang_code, _ in languages:
        # 处理语言代码格式
        if '-' in lang_code:
            lang_code = lang_code.replace('-', '-').upper()
            if lang_code.count('-') == 1:
                parts = lang_code.split('-')
                lang_code = f"{parts[0].lower()}-{parts[1].upper()}"
        
        if i18n_service.is_language_supported(lang_code):
            return lang_code
        
        # 尝试只匹配语言部分
        base_lang = lang_code.split('-')[0].lower()
        for supported_lang in i18n_service.languages.keys():
            if supported_lang.startswith(base_lang):
                return supported_lang
    
    return i18n_service.default_language
