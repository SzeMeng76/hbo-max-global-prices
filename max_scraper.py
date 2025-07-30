#!/usr/bin/env python3
"""
HBO Max Global Price Scraper
自动抓取全球 HBO Max 订阅价格，支持代理和并发处理
基于原有 max.py 代码，优化为批量自动化处理
"""

import asyncio
import json
import os
import time
import random
import traceback
import re
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

# 确保 BS4 可用
try:
    from bs4 import BeautifulSoup
    BS4_INSTALLED = True
except ImportError:
    BS4_INSTALLED = False
    print("❌ 请安装 BeautifulSoup4: pip install beautifulsoup4")
    exit(1)

# --- 常量定义 ---
MAX_URL = "https://www.max.com"

# 静态区域映射：国家代码 -> 多语言 URL 路径列表（基于原有max.py）
REGION_PATHS: Dict[str, List[str]] = {
    "my": ["/my/en", "/my/zh", "/my/ms"],
    "hk": ["/hk/en", "/hk/zh"],
    "ph": ["/ph/en", "/ph/tl"],
    "tw": ["/tw/en", "/tw/zh"],
    "id": ["/id/en", "/id/id"],
    "sg": ["/sg/en", "/sg/ms"],
    "th": ["/th/en", "/th/th"],
    "co": ["/co/es"], "cr": ["/cr/es"], "gt": ["/gt/es"], "pe": ["/pe/es"],
    "uy": ["/uy/es"], "mx": ["/mx/es"], "hn": ["/hn/es"], "ni": ["/ni/es"],
    "pa": ["/pa/es"], "ar": ["/ar/es"], "bo": ["/bo/es"], "do": ["/do/es"],
    "ec": ["/ec/es"], "sv": ["/sv/es"], "py": ["/py/es"], "cl": ["/cl/es"],
    "br": ["/br/pt"],
    "jm": ["/jm/en"], "ms": ["/ms/en"], "ai": ["/ai/en"], "ag": ["/ag/en"],
    "aw": ["/aw/en"], "bs": ["/bs/en"], "bb": ["/bb/en"], "bz": ["/bz/en"],
    "vg": ["/vg/en"], "ky": ["/ky/en"], "cw": ["/cw/en"], "dm": ["/dm/en"],
    "gd": ["/gd/en"], "gy": ["/gy/en"], "ht": ["/ht/en"], "kn": ["/kn/en"],
    "lc": ["/lc/en"], "vc": ["/vc/en"], "sr": ["/sr/en"], "tt": ["/tt/en"],
    "tc": ["/tc/en"],
    "us": ["/us/en", "/us/es"],
    "au": ["/au/en"],
    "ad": ["/ad/en", "/ad/es"],
    "ba": ["/ba/en", "/ba/hr"],
    "bg": ["/bg/en", "/bg/bg"],
    "hr": ["/hr/en", "/hr/hr"],
    "cz": ["/cz/cs"],
    "hu": ["/hu/hu"],
    "mk": ["/mk/en", "/mk/mk"],
    "md": ["/md/en", "/md/ro"],
    "me": ["/me/en", "/me/sr"],
    "ro": ["/ro/en", "/ro/ro"],
    "rs": ["/rs/en", "/rs/sr"],
    "sk": ["/sk/en", "/sk/sk"],
    "si": ["/si/en", "/si/sl"],
    "dk": ["/dk/da"],
    "fi": ["/fi/en", "/fi/fi"],
    "no": ["/no/no"],
    "se": ["/se/sv"],
    "es": ["/es/en", "/es/es"],
    "fr": ["/fr/en", "/fr/fr"],
    "be": ["/be/en", "/be/nl", "/be/fr"],
    "pt": ["/pt/en", "/pt/pt"],
    "nl": ["/nl/en", "/nl/nl"],
    "pl": ["/pl/pl"],
    "tr": ["/tr/en", "/tr/tr"],
    
    # 缺失的欧洲国家
    "al": ["/al/en", "/al/sq"],        # Albania
    "am": ["/am/en", "/am/hy"],        # Armenia  
    "cy": ["/cy/en", "/cy/el"],        # Cyprus
    "ee": ["/ee/en", "/ee/et"],        # Estonia
    "ge": ["/ge/en", "/ge/ka"],        # Georgia
    "is": ["/is/en", "/is/is"],        # Iceland
    "kz": ["/kz/en", "/kz/kk"],        # Kazakhstan
    "kg": ["/kg/en", "/kg/ky"],        # Kyrgyzstan
    "lv": ["/lv/en", "/lv/lv"],        # Latvia
    "lt": ["/lt/en", "/lt/lt"],        # Lithuania
    "mt": ["/mt/en", "/mt/mt"],        # Malta
    "tj": ["/tj/en", "/tj/tg"],        # Tajikistan
    
    # 缺失的拉美国家  
    "gp": ["/gp/en", "/gp/fr"],        # Guadeloupe
    "ve": ["/ve/es"],                  # Venezuela
}

# 国家名称映射
COUNTRY_NAMES = {
    "my": "Malaysia", "hk": "Hong Kong", "ph": "Philippines", "tw": "Taiwan",
    "id": "Indonesia", "sg": "Singapore", "th": "Thailand", "co": "Colombia",
    "cr": "Costa Rica", "gt": "Guatemala", "pe": "Peru", "uy": "Uruguay",
    "mx": "Mexico", "hn": "Honduras", "ni": "Nicaragua", "pa": "Panama",
    "ar": "Argentina", "bo": "Bolivia", "do": "Dominican Republic", "ec": "Ecuador",
    "sv": "El Salvador", "py": "Paraguay", "cl": "Chile", "br": "Brazil",
    "jm": "Jamaica", "ms": "Montserrat", "ai": "Anguilla", "ag": "Antigua and Barbuda",
    "aw": "Aruba", "bs": "Bahamas", "bb": "Barbados", "bz": "Belize",
    "vg": "British Virgin Islands", "ky": "Cayman Islands", "cw": "Curacao",
    "dm": "Dominica", "gd": "Grenada", "gy": "Guyana", "ht": "Haiti",
    "kn": "Saint Kitts and Nevis", "lc": "Saint Lucia", "vc": "Saint Vincent and the Grenadines",
    "sr": "Suriname", "tt": "Trinidad and Tobago", "tc": "Turks and Caicos Islands",
    "us": "United States", "au": "Australia", "ad": "Andorra", "ba": "Bosnia and Herzegovina",
    "bg": "Bulgaria", "hr": "Croatia", "cz": "Czech Republic", "hu": "Hungary",
    "mk": "North Macedonia", "md": "Moldova", "me": "Montenegro", "ro": "Romania",
    "rs": "Serbia", "sk": "Slovakia", "si": "Slovenia", "dk": "Denmark",
    "fi": "Finland", "no": "Norway", "se": "Sweden", "es": "Spain",
    "fr": "France", "be": "Belgium", "pt": "Portugal", "nl": "Netherlands",
    "pl": "Poland", "tr": "Turkey",
    
    # 缺失的欧洲国家
    "al": "Albania", "am": "Armenia", "cy": "Cyprus", "ee": "Estonia",
    "ge": "Georgia", "is": "Iceland", "kz": "Kazakhstan", "kg": "Kyrgyzstan", 
    "lv": "Latvia", "lt": "Lithuania", "mt": "Malta", "tj": "Tajikistan",
    
    # 缺失的拉美国家
    "gp": "Guadeloupe", "ve": "Venezuela"
}

# HBO Max 套餐名统一映射表（参考Spotify项目架构）
# 将各种语言/变体的套餐名统一为标准英文名称
HBO_PLAN_NAME_MAP = {
    # 标准英文套餐名（保持不变）
    "mobile": "Mobile",
    "standard": "Standard", 
    "ultimate": "Ultimate",
    "premium": "Premium",
    "basic": "Basic",
    "max": "Max",
    
    # 西班牙语套餐名映射
    "móvil": "Mobile",
    "movil": "Mobile",
    "estándar": "Standard",
    "estandar": "Standard",
    "último": "Ultimate",
    "ultimo": "Ultimate",
    "máximo": "Ultimate",
    "maximo": "Ultimate",
    "platino": "Ultimate",  # 重要：Platino = Ultimate
    "básico": "Basic",
    "basico": "Basic",
    "premium": "Premium",
    
    # 拉美地区常见套餐名
    "básico con anuncios": "Basic",
    "basico con anuncios": "Basic",
    
    # 葡萄牙语套餐名映射
    "móvel": "Mobile",
    "movel": "Mobile",
    "padrão": "Standard",
    "padrao": "Standard",
    "supremo": "Ultimate",
    "máximo": "Ultimate",
    "maximo": "Ultimate",
    "básico": "Basic",
    "basico": "Basic",
    
    # 法语套餐名映射
    "mobile": "Mobile",
    "standard": "Standard",
    "premium": "Premium",
    "ultime": "Ultimate",
    "de base": "Basic",
    "base": "Basic",
    
    # 德语套餐名映射
    "mobil": "Mobile",
    "standard": "Standard",
    "premium": "Premium",
    "ultimativ": "Ultimate",
    "basis": "Basic",
    "grund": "Basic",
    
    # 意大利语套餐名映射
    "mobile": "Mobile",
    "standard": "Standard",
    "premium": "Premium",
    "ultimo": "Ultimate",
    "base": "Basic",
    "di base": "Basic",
    
    # 荷兰语套餐名映射
    "mobiel": "Mobile",
    "standaard": "Standard",
    "premium": "Premium",
    "ultiem": "Ultimate",
    "basis": "Basic",
    
    # 波兰语套餐名映射
    "mobilny": "Mobile",
    "standardowy": "Standard",
    "premium": "Premium",
    "najwyższy": "Ultimate",
    "podstawowy": "Basic",
    
    # 捷克语套餐名映射
    "mobilní": "Mobile",
    "standardní": "Standard",
    "premium": "Premium",
    "ultimátní": "Ultimate",
    "základní": "Basic",
    
    # 匈牙利语套餐名映射
    "mobil": "Mobile",
    "standard": "Standard",
    "prémium": "Premium",
    "premium": "Premium",
    "végső": "Ultimate",
    "alap": "Basic",
    
    # 土耳其语套餐名映射
    "mobil": "Mobile",
    "standart": "Standard",
    "premium": "Premium",
    "en üst": "Ultimate",
    "temel": "Basic",
    
    # 亚洲语言套餐名映射（如果有）
    "手机": "Mobile",
    "移动": "Mobile",
    "标准": "Standard",
    "高级": "Premium",
    "至尊": "Ultimate",
    "终极": "Ultimate",
    "基础": "Basic",
    "基本": "Basic",
    
    # 繁体中文套餐名映射
    "標準": "Standard",
    "高級": "Ultimate",  # 高級在HBO Max中通常是最高级套餐
    "手機": "Mobile",
    "移動": "Mobile",
    "基礎": "Basic",
    "基本": "Basic",
    "終極": "Ultimate",
    "至尊": "Ultimate",
    
    # 马来语套餐名映射
    "mudah alih": "Mobile",
    "standard": "Standard",
    "premium": "Premium",
    "muktamad": "Ultimate",
    "asas": "Basic",
    
    # 泰语套餐名映射
    "มือถือ": "Mobile",
    "มาตรฐาน": "Standard", 
    "พรีเมียม": "Premium",
    "สูงสุด": "Ultimate",
    "พื้นฐาน": "Basic",
    
    # 印尼语套餐名映射
    "mobile": "Mobile",
    "standar": "Standard",
    "premium": "Premium",
    "tertinggi": "Ultimate",
    "dasar": "Basic",
    
    # 菲律宾语(塔加洛语)套餐名映射
    "mobile": "Mobile",
    "karaniwan": "Standard", 
    "premium": "Premium",
    "pinakamataas": "Ultimate",
    "pangunahing": "Basic",
    
    # 其他可能的变体
    "mob": "Mobile",
    "std": "Standard",
    "prem": "Premium",
    "ult": "Ultimate",
    "bas": "Basic",
    "max": "Max"
}

def normalize_plan_name(plan_name: str) -> str:
    """
    统一套餐名称，将各种语言/变体的套餐名转换为标准英文名称
    参考Spotify项目的架构设计
    """
    if not plan_name:
        return "Unknown Plan"
    
    # 清理套餐名称
    cleaned_name = plan_name.strip().lower()
    
    # 移除常见的前缀/后缀
    prefixes_to_remove = ['hbo max', 'max', 'hbo', 'plan', 'subscription', 'abonnement', 'suscripción']
    for prefix in prefixes_to_remove:
        if cleaned_name.startswith(prefix):
            cleaned_name = cleaned_name[len(prefix):].strip()
        if cleaned_name.endswith(prefix):
            cleaned_name = cleaned_name[:-len(prefix)].strip()
    
    # 移除特殊字符和多余空格
    cleaned_name = re.sub(r'[^\w\s]', ' ', cleaned_name)
    cleaned_name = ' '.join(cleaned_name.split())
    
    # 检查映射表
    if cleaned_name in HBO_PLAN_NAME_MAP:
        normalized = HBO_PLAN_NAME_MAP[cleaned_name]
        print(f"    📋 套餐名映射: '{plan_name}' -> '{normalized}'")
        return normalized
    
    # 部分匹配检查（用于处理复合名称）
    for key, value in HBO_PLAN_NAME_MAP.items():
        if key in cleaned_name or cleaned_name in key:
            print(f"    📋 套餐名部分匹配: '{plan_name}' -> '{value}' (匹配关键词: '{key}')")
            return value
    
    # 如果没有找到映射，返回首字母大写的原名称
    fallback_name = ' '.join(word.capitalize() for word in cleaned_name.split())
    if not fallback_name:
        fallback_name = "Unknown Plan"
    
    print(f"    ⚠️ 套餐名未找到映射: '{plan_name}' -> '{fallback_name}' (建议添加到映射表)")
    return fallback_name

# 请求头配置
USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",  
    "Mozilla/5.0 (Windows NT 10.0; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; x64) AppleWebKit/537.36 Edg/120.0"
]

BASE_HEADERS: Dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
    "Sec-GPC": "1"
}

# 代理API配置（使用环境变量）
PROXY_API_TEMPLATE = os.getenv("PROXY_API_TEMPLATE", "http://api.mooproxy.xyz/v1/gen?user=Domo_lee&country={country}&pass=UNuYSniZ8D")

def extract_year_from_timestamp(timestamp: str) -> str:
    """从时间戳中提取年份"""
    try:
        if len(timestamp) >= 4:
            return timestamp[:4]
        else:
            return time.strftime('%Y')
    except:
        return time.strftime('%Y')

def create_archive_directory_structure(archive_dir: str, timestamp: str) -> str:
    """根据时间戳创建按年份组织的归档目录结构"""
    year = extract_year_from_timestamp(timestamp)
    year_dir = os.path.join(archive_dir, year)
    if not os.path.exists(year_dir):
        os.makedirs(year_dir)
        print(f"📁 创建年份目录: {year_dir}")
    return year_dir

async def get_proxy(country_code: str) -> Optional[Dict[str, str]]:
    """获取指定国家的代理"""
    url = PROXY_API_TEMPLATE.format(country=country_code.lower())
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            print(f"🔄 {country_code}: 获取代理...")
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            plist = data.get("proxies") or []
            if not plist:
                raise ValueError("代理列表为空")
            
            host, port, user, *rest = plist[0].split(":")
            password = ":".join(rest)
            if not port.isdigit():
                raise ValueError("端口号无效")
                
            full = f"http://{user}:{password}@{host}:{port}"
            print(f"✅ {country_code}: 代理获取成功 {host}:{port}")
            return {"http://": full, "https://": full}
    except Exception as e:
        print(f"❌ {country_code}: 代理获取失败 - {e}")
        return None

async def fetch_max_page(country_code: str, proxies: Dict[str, str], headers: Dict[str, str]) -> Optional[str]:
    """获取HBO Max页面内容"""
    cc = country_code.lower()
    paths = REGION_PATHS.get(cc)
    
    # 获取代理URL
    proxy_url = proxies.get('http://')
    
    # 优先使用静态映射
    if paths:
        for path in paths:
            url = MAX_URL + path
            try:
                async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=45.0, proxy=proxy_url) as client:
                    print(f"🌐 {country_code}: 访问 {url}")
                    r = await client.get(url)
                    print(f"📊 {country_code}: 响应 {r.status_code} -> {r.url}")
                    r.raise_for_status()
                    return r.text
            except httpx.HTTPStatusError as e:
                print(f"⚠️ {country_code}: HTTP {e.response.status_code} - 尝试下一个路径")
                continue
            except Exception as e:
                print(f"❌ {country_code}: 访问失败 - {e}")
                continue
        return None
    
    # 无映射时的通用逻辑
    default_url = f"{MAX_URL}/{cc}/"
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=45.0, proxy=proxy_url) as client:
            print(f"🌐 {country_code}: 访问 {default_url}")
            r = await client.get(default_url)
            print(f"📊 {country_code}: 响应 {r.status_code} -> {r.url}")
            r.raise_for_status()
            return r.text
    except httpx.HTTPStatusError as e:
        # 404时回退到西班牙语
        if e.response.status_code == 404:
            fallback = f"{MAX_URL}/{cc}/es"
            try:
                async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0, proxy=proxy_url) as client:
                    print(f"🔄 {country_code}: 西语回退 {fallback}")
                    r2 = await client.get(fallback)
                    print(f"📊 {country_code}: 回退响应 {r2.status_code} -> {r2.url}")
                    r2.raise_for_status()
                    return r2.text
            except Exception:
                pass
        return None
    except Exception as e:
        print(f"❌ {country_code}: 访问出错 - {e}")
        return None

def extract_price_number(price_str: str) -> float:
    """从价格字符串中提取数值（参考Spotify项目的逻辑）"""
    if not price_str:
        return 0.0
    
    # 首先尝试查找空格分隔的数字（如 "₡3 990" 或 "12x₡1 990"）
    space_separated_pattern = r'(\d+(?:\s+\d+)+)'
    space_matches = re.findall(space_separated_pattern, price_str)
    
    if space_matches:
        # 处理空格分隔的数字，移除空格
        number_part = space_matches[0].replace(' ', '')
        try:
            return float(number_part)
        except ValueError:
            pass
    
    # 查找数字、逗号、点的连续组合
    number_pattern = r'([\d,\.]+)'
    number_matches = re.findall(number_pattern, price_str)
    
    if not number_matches:
        return 0.0
    
    # 找到最长的数字串（通常是价格）
    number_part = max(number_matches, key=len)
    
    # 如果没有数字，返回0
    if not re.search(r'\d', number_part):
        return 0.0 
    
    # 处理不同的数字格式
    cleaned = number_part
    if ',' in cleaned and '.' in cleaned:
        # 判断是欧式格式还是美式格式
        comma_pos = cleaned.rindex(',')
        dot_pos = cleaned.rindex('.')
        if comma_pos > dot_pos:
            # 欧式格式 (1.234,56) - 点是千位分隔符，逗号是小数点
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # 美式格式 (1,234.56) - 逗号是千位分隔符，点是小数点
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # 只有逗号的情况
        parts = cleaned.split(',')
        if len(parts) == 2:
            # 检查小数部分长度来判断是小数点还是千位分隔符
            decimal_part = parts[-1]
            if len(decimal_part) <= 2:
                # 小数部分是1-2位数，很可能是小数点 (例如: 5,99)
                cleaned = cleaned.replace(',', '.')
            else:
                # 小数部分超过2位，很可能是千位分隔符 (例如: 2,499)
                cleaned = cleaned.replace(',', '')
        else:
            # 多个逗号，都是千位分隔符
            cleaned = cleaned.replace(',', '')
    elif '.' in cleaned:
        # 只有点的情况
        parts = cleaned.split('.')
        if len(parts) == 2:
            # 检查小数部分长度
            decimal_part = parts[-1]
            if len(decimal_part) <= 2:
                # 小数部分是1-2位数，保持为小数点 (例如: 5.99)
                pass  # 保持不变
            else:
                # 小数部分超过2位，很可能是千位分隔符 (例如: 2.499)
                cleaned = cleaned.replace('.', '')
        else:
            # 多个点，都是千位分隔符
            cleaned = cleaned.replace('.', '')
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def detect_currency(price_str: str, country_code: str = None) -> str:
    """检测价格字符串中的货币，优先使用国家上下文"""
    
    # 国家到货币的精确映射（最高优先级）
    country_currency_map = {
        'my': 'MYR',     # Malaysia - RM
        'sg': 'SGD',     # Singapore - S$ 或 $（需要特别处理）
        'th': 'THB',     # Thailand - ฿
        'id': 'IDR',     # Indonesia - Rp
        'ph': 'PHP',     # Philippines - ₱
        'hk': 'HKD',     # Hong Kong - HK$ 或 $（需要特别处理）
        'tw': 'TWD',     # Taiwan - NT$
        'au': 'AUD',     # Australia - A$ 或 $（需要特别处理）
        'us': 'USD',     # United States - $
        'co': 'COP',     # Colombia - $
        'cr': 'CRC',     # Costa Rica - ₡
        'gt': 'GTQ',     # Guatemala - Q
        'pe': 'PEN',     # Peru - S/.
        'uy': 'UYU',     # Uruguay - $
        'mx': 'MXN',     # Mexico - $
        'hn': 'HNL',     # Honduras - L
        'ni': 'NIO',     # Nicaragua - C$
        'pa': 'PAB',     # Panama - B/. 或 $
        'ar': 'ARS',     # Argentina - $
        'bo': 'BOB',     # Bolivia - Bs
        'do': 'DOP',     # Dominican Republic - RD$
        'ec': 'USD',     # Ecuador - $ (uses USD)
        'sv': 'USD',     # El Salvador - $ (uses USD)
        'py': 'PYG',     # Paraguay - Gs
        'cl': 'CLP',     # Chile - $
        'br': 'BRL',     # Brazil - R$
        'pl': 'PLN',     # Poland - zł
        'cz': 'CZK',     # Czech Republic - Kč
        'hu': 'HUF',     # Hungary - Ft
        'tr': 'TRY',     # Turkey - ₺
        'dk': 'DKK',     # Denmark - kr
        'no': 'NOK',     # Norway - kr
        'se': 'SEK',     # Sweden - kr
        'fi': 'EUR',     # Finland - €
        'es': 'EUR',     # Spain - €
        'fr': 'EUR',     # France - €
        'be': 'EUR',     # Belgium - €
        'pt': 'EUR',     # Portugal - €
        'nl': 'EUR',     # Netherlands - €
        'bg': 'BGN',     # Bulgaria - лв
        'hr': 'EUR',     # Croatia - €
        'mk': 'MKD',     # North Macedonia - ден
        'md': 'MDL',     # Moldova - lei
        'me': 'EUR',     # Montenegro - €
        'ro': 'RON',     # Romania - lei
        'rs': 'RSD',     # Serbia - din
        'sk': 'EUR',     # Slovakia - €
        'si': 'EUR',     # Slovenia - €
        'ba': 'BAM',     # Bosnia and Herzegovina - KM
        'ad': 'EUR',     # Andorra - €
    }
    
    # 优先使用国家上下文（最重要的修复）
    if country_code:
        country_code_lower = country_code.lower()
        if country_code_lower in country_currency_map:
            expected_currency = country_currency_map[country_code_lower]
            print(f"    💱 {country_code}: 使用国家映射货币 {expected_currency}")
            return expected_currency
    
    # 详细的货币符号检测（按优先级排序）
    currency_symbols = {
        # 优先检查带前缀的特殊符号（避免与通用$混淆）
        'US$': 'USD', 'USD': 'USD',
        'S$': 'SGD', 'SGD': 'SGD',  # 新加坡元
        'HK$': 'HKD', 'HKD': 'HKD',  # 港币
        'A$': 'AUD', 'AUD': 'AUD',   # 澳元
        'C$': 'CAD', 'CA$': 'CAD',   # 加元
        'MX$': 'MXN', 'NZ$': 'NZD', 'NT$': 'TWD',
        'R$': 'BRL', 'RD$': 'DOP',   # 巴西雷亚尔, 多米尼加比索
        
        # 特殊货币符号
        '€': 'EUR', 'EUR': 'EUR',
        '£': 'GBP', 'GBP': 'GBP', 
        '¥': 'JPY', '￥': 'JPY', 'JPY': 'JPY',
        '₹': 'INR', 'INR': 'INR',
        '₱': 'PHP', 'PHP': 'PHP',
        '₪': 'ILS', '₨': 'PKR', '₦': 'NGN', '₵': 'GHS',
        '₡': 'CRC', '₩': 'KRW', '₴': 'UAH', '₽': 'RUB',
        '₺': 'TRY', 'TRY': 'TRY',
        
        # 字母缩写
        'zł': 'PLN', 'PLN': 'PLN',
        'Kč': 'CZK', 'CZK': 'CZK', 
        'Ft': 'HUF', 'HUF': 'HUF',
        'TL': 'TRY', 'TRY': 'TRY',  # Turkish Lira
        'CHF': 'CHF', 'NOK': 'NOK', 'SEK': 'SEK', 'DKK': 'DKK',
        'RM': 'MYR', 'MYR': 'MYR',  # 马来西亚林吉特
        '฿': 'THB', 'THB': 'THB',    # 泰铢
        'Rp': 'IDR', 'IDR': 'IDR',   # 印尼盾
        'S/.': 'PEN', 'PEN': 'PEN',  # 秘鲁索尔
        'L': 'HNL', 'Gs': 'PYG', 'Q': 'GTQ',
        'kr': 'SEK',  # 默认kr为瑞典克朗
        
        # 最后检查通用美元符号（优先级最低）
        '$': 'USD'
    }
    
    # 按符号长度从长到短排序，优先匹配更具体的符号
    sorted_symbols = sorted(currency_symbols.items(), key=lambda x: len(x[0]), reverse=True)
    
    for symbol, currency in sorted_symbols:
        if symbol in price_str:
            return currency
    
    # 如果都没找到，返回国家映射的货币或默认USD
    if country_code:
        country_code_lower = country_code.lower()
        if country_code_lower in country_currency_map:
            return country_currency_map[country_code_lower]
    
    return 'USD'

async def parse_max_prices(html: str, country_code: str) -> Tuple[List[Dict[str, Any]], str]:
    """解析HBO Max页面价格信息，返回（结构化数据列表, 文本输出）"""
    if not html:
        err = f"❌ 无法获取页面内容 ({country_code})"
        return [], err
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        sections = soup.find_all('section', {'data-plan-group': True})
        plans: List[Dict[str, Any]] = []
        seen: set = set()
        
        if sections:
            print(f"📊 {country_code}: 找到 {len(sections)} 个价格区域")
            for sec in sections:
                p = sec['data-plan-group']
                label = '每月' if p == 'monthly' else '每年'
                cards = sec.find_all('div', class_='max-plan-picker-group__card')
                print(f"📦 {country_code}: {label} 区域找到 {len(cards)} 个套餐")
                
                for card in cards:
                    try:
                        name_elem = card.find('h3')
                        price_elem = card.find('h4')
                        
                        if not name_elem or not price_elem:
                            continue
                            
                        name = name_elem.get_text(strip=True)
                        price = price_elem.get_text(strip=True)
                        
                        # 统一套餐名称（参考Spotify项目架构）
                        normalized_name = normalize_plan_name(name)
                        
                        key = (p, normalized_name, price)
                        if key in seen:
                            continue
                        seen.add(key)
                        
                        # 提取价格数值和货币
                        price_number = extract_price_number(price)
                        currency = detect_currency(price, country_code)
                        
                        # 处理年付价格：如果是年付或bundle且价格格式为"12x $X.XX/mes"，计算年度总价
                        annual_total_price = price_number
                        if (p == 'yearly' or p == 'bundle') and price_number > 0:
                            # 检查是否是"12x"格式
                            if '12x' in price or '12 x' in price:
                                # 年付价格 = 月价格 × 12
                                annual_total_price = price_number * 12
                                print(f"    💰 {country_code}: 年付价格计算: {price_number}/月 × 12 = {annual_total_price}/年")
                        
                        plan_data = {
                            "plan_group": p,
                            "label": label,
                            "name": normalized_name,  # 使用统一后的套餐名
                            "original_name": name,    # 保留原始套餐名用于调试
                            "price": price,
                            "price_number": annual_total_price,  # 使用计算后的年度价格
                            "monthly_price": price_number,       # 保留原始月价格用于显示
                            "currency": currency
                        }
                        plans.append(plan_data)
                        print(f"✅ {country_code}: {normalized_name} ({label}) - {price} ({currency})")
                        if name != normalized_name:
                            print(f"    📋 原始名称: '{name}' -> 统一名称: '{normalized_name}'")
                        
                    except Exception as e:
                        print(f"⚠️ {country_code}: 解析套餐失败 - {e}")
                        continue
            
            # 构建输出文本
            if plans:
                out = [f"**HBO Max {country_code.upper()} 订阅价格:**"]
                for item in plans:
                    out.append(f"✅ {item['name']} ({item['label']}): **{item['price']}**")
                return plans, "\n".join(out)
        
        # 如果没有找到标准结构，尝试其他解析方法
        print(f"🔍 {country_code}: 未找到标准价格结构，尝试备用解析...")
        
        # 查找价格相关的元素
        price_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'price|cost|plan', re.I))
        if price_elements:
            print(f"📊 {country_code}: 找到 {len(price_elements)} 个价格相关元素")
            for elem in price_elements[:10]:  # 增加检查数量
                text = elem.get_text(strip=True)
                # 检查是否包含价格信息
                if re.search(r'[€$£¥₹₱₪₨₦₵₡₺zł]\s*[\d,.]|\d+[\d,.]*\s*[€$£¥₹₱₪₨₦₵₡₺zł]|[\d,.]+\s*(zł|Kč|Ft|kr|TL)', text):
                    # 尝试提取个别价格而不是整个文本块
                    price_matches = re.findall(r'(\d+[,.]?\d*)\s*(zł|€|$|£|¥|₹|₱|₪|₨|₦|₵|₡|₺|Kč|Ft|kr|TL)(?:/(?:mies|mes|month|rok|year|año))?', text)
                    
                    if price_matches:
                        for price_match in price_matches[:3]:  # 限制每个元素最多3个价格
                            price_text = price_match[0] + ' ' + price_match[1]
                            price_number = extract_price_number(price_text)
                            currency = detect_currency(price_text, country_code)
                            
                            if price_number > 0:
                                # 尝试从多个地方获取套餐名称
                                plan_name = "HBO Max Plan"
                                
                                # 方法1: 从父元素查找标题
                                parent = elem.find_parent()
                                if parent:
                                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                                    if title_elem:
                                        title_text = title_elem.get_text(strip=True)
                                        if title_text and len(title_text) < 50:
                                            plan_name = title_text
                                
                                # 方法2: 从兄弟元素查找套餐名
                                if plan_name == "HBO Max Plan":
                                    siblings = elem.find_previous_siblings(['div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                                    for sibling in siblings[:3]:  # 只检查前3个兄弟元素
                                        sibling_text = sibling.get_text(strip=True)
                                        # 检查是否包含已知套餐名
                                        if any(name in sibling_text.lower() for name in ['podstawowy', 'standardowy', 'premium', 'basic', 'standard', 'ultimate']):
                                            if len(sibling_text) < 50:
                                                plan_name = sibling_text
                                                break
                                
                                # 方法3: 从当前元素的class或data属性推断
                                if plan_name == "HBO Max Plan" and elem.get('class'):
                                    class_str = ' '.join(elem.get('class', []))
                                    if 'basic' in class_str.lower():
                                        plan_name = "Basic"
                                    elif 'standard' in class_str.lower():
                                        plan_name = "Standard"  
                                    elif 'premium' in class_str.lower() or 'ultimate' in class_str.lower():
                                        plan_name = "Premium"
                                
                                normalized_name = normalize_plan_name(plan_name)
                                
                                # 使用 seen 集合去重
                                key = (normalized_name, price_text, currency)
                                if key in seen:
                                    continue
                                seen.add(key)
                                
                                plans.append({
                                    "plan_group": "unknown",
                                    "label": "未知周期",
                                    "name": normalized_name,
                                    "original_name": plan_name,
                                    "price": price_text,
                                    "price_number": price_number,
                                    "currency": currency
                                })
                                print(f"✅ {country_code}: 备用解析 - {normalized_name}: {price_text} ({currency})")
                    else:
                        # 如果没有匹配到具体价格，使用原来的逻辑（但限制文本长度）
                        if len(text) < 200:  # 只处理较短的文本，避免整页内容
                            price_number = extract_price_number(text)
                            currency = detect_currency(text, country_code)
                            if price_number > 0:
                                normalized_name = normalize_plan_name("HBO Max Plan")
                                
                                # 使用 seen 集合去重
                                key = (normalized_name, text, currency)
                                if key in seen:
                                    continue
                                seen.add(key)
                                
                                plans.append({
                                    "plan_group": "unknown",
                                    "label": "未知周期",
                                    "name": normalized_name,
                                    "original_name": "HBO Max Plan",
                                    "price": text,
                                    "price_number": price_number,
                                    "currency": currency
                                })
                                print(f"✅ {country_code}: 备用解析 - {text} ({currency})")
                                break
        
        if plans:
            out = [f"**HBO Max {country_code.upper()} 订阅价格:**"]
            for item in plans:
                out.append(f"✅ {item['name']} ({item['label']}): **{item['price']}**")
            return plans, "\n".join(out)
        
    except Exception as e:
        print(f"❌ {country_code}: 解析失败 - {e}")
        err = f"❌ 解析出错: {e}"
        return [], err
    
    return [], f"❌ {country_code}: 未解析到任何价格"

async def get_max_prices_for_country(country_code: str, max_retries: int = 2, semaphore: asyncio.Semaphore = None) -> Optional[Dict[str, Any]]:
    """获取指定国家的HBO Max价格"""
    if semaphore:
        async with semaphore:
            return await _get_max_prices_for_country_impl(country_code, max_retries)
    else:
        return await _get_max_prices_for_country_impl(country_code, max_retries)

async def _get_max_prices_for_country_impl(country_code: str, max_retries: int) -> Optional[Dict[str, Any]]:
    """获取指定国家的HBO Max价格的内部实现"""
    country_name = COUNTRY_NAMES.get(country_code.lower(), country_code.upper())
    
    for attempt in range(max_retries):
        try:
            print(f"\n🌍 {country_code} ({country_name}) - 尝试 {attempt + 1}/{max_retries}")
            
            # 获取代理
            proxies = await get_proxy(country_code)
            if not proxies:
                print(f"❌ {country_code}: 无法获取代理，尝试下一次")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                else:
                    return None
            
            # 设置请求头
            headers = {**BASE_HEADERS, 'User-Agent': random.choice(USER_AGENTS)}
            
            # 获取页面内容
            html = await fetch_max_page(country_code, proxies, headers)
            if not html:
                print(f"❌ {country_code}: 无法获取页面内容")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                else:
                    return None
            
            # 解析价格
            plans, result_text = await parse_max_prices(html, country_code)
            
            if plans:
                print(f"🎯 {country_code}: 成功获取 {len(plans)} 个套餐")
                return {
                    'country_code': country_code.upper(),
                    'country_name': country_name,
                    'plans': plans,
                    'scraped_at': datetime.now().isoformat(),
                    'attempt': attempt + 1,
                    'success': True
                }
            else:
                print(f"⚠️ {country_code}: 未获取到价格信息")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                else:
                    return None
                    
        except Exception as e:
            print(f"❌ {country_code}: 处理失败 - {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(2, 5))
                continue
            else:
                return None
    
    return None

async def main():
    """主函数：并发获取各国HBO Max价格"""
    print("🎬 HBO Max Global Price Scraper 启动...")
    print("🚀 使用并发模式，同时处理多个国家")
    
    results = {}
    failed_countries = []
    
    # 获取所有国家代码
    all_countries = list(REGION_PATHS.keys())
    total_countries = len(all_countries)
    max_concurrent = 5  # 最大并发数，避免过多请求
    
    print(f"📊 准备处理 {total_countries} 个国家/地区")
    
    # 创建信号量来限制并发数
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_country_with_semaphore(country_code: str, index: int):
        """使用信号量控制并发的国家处理函数"""
        print(f"\n🔄 开始处理: {index+1}/{total_countries} - {country_code}")
        
        # 获取该国家的价格
        country_data = await get_max_prices_for_country(country_code, semaphore=semaphore)
        
        if country_data:
            results[country_code.upper()] = country_data
            print(f"✅ {country_code}: 成功获取 {len(country_data['plans'])} 个套餐")
            return True, country_code
        else:
            failed_countries.append(f"{country_code} ({COUNTRY_NAMES.get(country_code.lower(), country_code)})")
            print(f"❌ {country_code}: 获取失败")
            return False, country_code
    
    # 创建所有任务
    tasks = []
    for i, country_code in enumerate(all_countries):
        task = process_country_with_semaphore(country_code, i)
        tasks.append(task)
    
    # 分批处理以避免过载
    batch_size = 15  # 每批处理15个国家
    
    print(f"🚀 开始并发处理（最大并发数: {max_concurrent}，批处理大小: {batch_size}）...")
    
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        batch_start = i + 1
        batch_end = min(i + batch_size, len(tasks))
        
        print(f"\n📦 处理批次 {batch_start}-{batch_end}/{total_countries}")
        
        # 并发执行当前批次
        batch_results = await asyncio.gather(*batch, return_exceptions=True)
        
        # 处理批次结果
        for result in batch_results:
            if isinstance(result, Exception):
                print(f"❌ 批次中发生异常: {result}")
            elif isinstance(result, tuple) and len(result) == 2:
                success, country_code = result
                if success:
                    print(f"📊 批次完成: {country_code} ✅")
                else:
                    print(f"📊 批次完成: {country_code} ❌")
        
        # 批次间添加延迟
        if i + batch_size < len(tasks):
            delay = random.uniform(3, 8)
            print(f"⏱️  批次间等待 {delay:.1f} 秒...")
            await asyncio.sleep(delay)
    
    # 保存结果
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = f'max_prices_all_countries_{timestamp}.json'
    output_file_latest = 'max_prices_all_countries.json'
    
    # 确保归档目录结构存在
    archive_dir = 'archive'
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    # 根据时间戳创建年份子目录
    year_archive_dir = create_archive_directory_structure(archive_dir, timestamp)
    
    # 保存带时间戳的版本到对应年份归档目录
    archive_file = os.path.join(year_archive_dir, output_file)
    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 保存最新版本（供转换器使用）
    with open(output_file_latest, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 打印统计信息
    print(f"\n" + "="*60)
    print(f"🎉 HBO Max 价格抓取完成！")
    print(f"✅ 成功: {len(results)} 个国家")
    print(f"❌ 失败: {len(failed_countries)} 个国家")
    print(f"📁 历史版本已保存到: {archive_file}")
    print(f"📁 最新版本已保存到: {output_file_latest}")
    
    if failed_countries:
        print(f"\n❌ 失败的国家: {', '.join(failed_countries)}")
    
    # 显示成功率统计
    success_rate = len(results) / total_countries * 100
    print(f"\n📊 统计信息:")
    print(f"  总国家数: {total_countries}")
    print(f"  成功获取: {len(results)} 个国家")
    print(f"  失败数量: {len(failed_countries)} 个国家")
    print(f"  成功率: {success_rate:.1f}%")
    
    return results

if __name__ == '__main__':
    # 运行爬虫
    try:
        results = asyncio.run(main())
        
        # 显示一些样本数据
        if results:
            print(f"\n📋 样本数据:")
            for country_code, data in list(results.items())[:3]:
                print(f"\n{country_code} - {data.get('country_name', 'Unknown')}:")
                for plan in data.get('plans', []):
                    print(f"  📦 {plan.get('name', 'Unknown')}: {plan.get('price', 'N/A')}")
        
        print(f"\n🎬 HBO Max 价格抓取任务完成！")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序执行错误: {e}")
        print(traceback.format_exc())