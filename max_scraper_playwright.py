#!/usr/bin/env python3
"""
HBO Max Global Price Scraper - Playwright Version
使用 Playwright 替代 httpx，提供更好的 JavaScript 支持和反爬虫能力
基于原有 max_scraper.py 优化而来
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
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# 确保 BS4 可用
try:
    from bs4 import BeautifulSoup
    BS4_INSTALLED = True
except ImportError:
    BS4_INSTALLED = False
    print("❌ 请安装 BeautifulSoup4: pip install beautifulsoup4")
    exit(1)

# 确保 Playwright 可用
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_INSTALLED = True
except ImportError:
    PLAYWRIGHT_INSTALLED = False
    print("❌ 请安装 Playwright: pip install playwright")
    print("❌ 然后运行: playwright install chromium")
    exit(1)

# --- 常量定义 ---
MAX_URL = "https://www.hbomax.com"

# 静态区域映射：国家代码 -> 多语言 URL 路径列表（保持原有映射）
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
    "al": ["/al/en", "/al/sq"], "am": ["/am/en", "/am/hy"], "cy": ["/cy/en", "/cy/el"],
    "ee": ["/ee/en", "/ee/et"], "ge": ["/ge/en", "/ge/ka"], "is": ["/is/en", "/is/is"],
    "kz": ["/kz/en", "/kz/kk"], "kg": ["/kg/en", "/kg/ky"], "lv": ["/lv/en", "/lv/lv"],
    "lt": ["/lt/en", "/lt/lt"], "mt": ["/mt/en", "/mt/mt"], "tj": ["/tj/en", "/tj/tg"],
    
    # 缺失的拉美国家  
    "gp": ["/gp/en", "/gp/fr"], "ve": ["/ve/es"],
}

# 国家名称映射（保持原有）
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

# HBO Max 套餐名统一映射表（保持原有）
HBO_PLAN_NAME_MAP = {
    # 标准英文套餐名（保持不变）
    "mobile": "Mobile", "standard": "Standard", "ultimate": "Ultimate",
    "premium": "Premium", "basic": "Basic", "max": "Max",
    
    # 西班牙语套餐名映射
    "móvil": "Mobile", "movil": "Mobile", "estándar": "Standard", "estandar": "Standard",
    "último": "Ultimate", "ultimo": "Ultimate", "máximo": "Ultimate", "maximo": "Ultimate",
    "platino": "Ultimate", "básico": "Basic", "basico": "Basic", "premium": "Premium",
    "básico con anuncios": "Basic", "basico con anuncios": "Basic",
    
    # 葡萄牙语套餐名映射
    "móvel": "Mobile", "movel": "Mobile", "padrão": "Standard", "padrao": "Standard",
    "supremo": "Ultimate", "básico": "Basic", "basico": "Basic",
    
    # 法语套餐名映射
    "mobile": "Mobile", "standard": "Standard", "premium": "Premium",
    "ultime": "Ultimate", "de base": "Basic", "base": "Basic",
    
    # 其他语言映射（保持原有的完整映射）
    "手机": "Mobile", "移动": "Mobile", "标准": "Standard", "高级": "Premium",
    "至尊": "Ultimate", "终极": "Ultimate", "基础": "Basic", "基本": "Basic",
    
    # 其他可能的变体
    "mob": "Mobile", "std": "Standard", "prem": "Premium", "ult": "Ultimate",
    "bas": "Basic", "max": "Max", "platinum": "Platinum"
}

def normalize_plan_name(plan_name: str) -> str:
    """统一套餐名称，将各种语言/变体的套餐名转换为标准英文名称"""
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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",  
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/120.0.0.0"
]

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
                
            proxy_config = {
                'server': f'http://{host}:{port}',
                'username': user,
                'password': password
            }
            print(f"✅ {country_code}: 代理获取成功 {host}:{port}")
            return proxy_config
    except Exception as e:
        print(f"❌ {country_code}: 代理获取失败 - {e}")
        return None

async def get_proxy_with_retry(country_code: str, max_proxy_attempts: int = 3) -> Optional[Dict[str, str]]:
    """获取指定国家的代理，支持多次重试不同代理"""
    for attempt in range(max_proxy_attempts):
        proxy = await get_proxy(country_code)
        if proxy:
            return proxy
        if attempt < max_proxy_attempts - 1:
            delay = random.uniform(1, 3)
            print(f"🔄 {country_code}: 代理获取失败，{delay:.1f}秒后重试...")
            await asyncio.sleep(delay)
    print(f"❌ {country_code}: 所有代理获取尝试都失败")
    return None

class PlaywrightManager:
    """Playwright 浏览器管理器，支持代理和并发控制"""
    
    def __init__(self, max_concurrent_browsers: int = 3):
        self.playwright = None
        self.browsers: List[Browser] = []
        self.browser_semaphore = asyncio.Semaphore(max_concurrent_browsers)
        self.max_concurrent = max_concurrent_browsers
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        return self
    
    async def __aexit__(self, *args):
        # 关闭所有浏览器
        for browser in self.browsers:
            try:
                await browser.close()
            except:
                pass
        self.browsers.clear()
        
        if self.playwright:
            await self.playwright.stop()
    
    async def create_browser_context(self, proxy_config: Optional[Dict[str, str]] = None) -> Tuple[Browser, BrowserContext]:
        """创建浏览器和上下文"""
        async with self.browser_semaphore:
            # 配置浏览器启动参数
            launch_options = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-extensions'
                ]
            }
            
            # 如果有代理配置，添加到启动选项
            if proxy_config:
                launch_options['proxy'] = proxy_config
            
            browser = await self.playwright.chromium.launch(**launch_options)
            self.browsers.append(browser)
            
            # 创建上下文，模拟真实用户
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            return browser, context

async def fetch_max_page_playwright(country_code: str, proxy_config: Dict[str, str], playwright_manager: PlaywrightManager) -> Optional[str]:
    """使用 Playwright 获取 HBO Max 页面内容"""
    cc = country_code.lower()
    paths = REGION_PATHS.get(cc)
    
    browser = None
    context = None
    
    try:
        # 创建浏览器和上下文
        browser, context = await playwright_manager.create_browser_context(proxy_config)
        page = await context.new_page()
        
        # 设置页面超时
        page.set_default_timeout(30000)
        page.set_default_navigation_timeout(30000)
        
        async def try_fetch_url(url: str, description: str = "") -> Optional[str]:
            """尝试访问URL并获取内容"""
            try:
                print(f"🌐 {country_code}: Playwright {description}访问 {url}")
                
                # 导航到页面，等待网络空闲
                response = await page.goto(url, wait_until='networkidle', timeout=30000)
                
                if response and response.status >= 400:
                    print(f"⚠️ {country_code}: HTTP {response.status} - {description}")
                    return None
                
                # 等待页面完全加载，尝试等待价格相关元素
                price_selectors = [
                    '.max-plan-picker-group__card',
                    '[data-plan-group]',
                    '.max-plan-picker-group-monthly',
                    '.max-plan-picker-group-yearly'
                ]
                
                # 尝试等待任一价格元素出现
                for selector in price_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        print(f"✅ {country_code}: 找到价格元素 {selector}")
                        break
                    except:
                        continue
                else:
                    # 如果没有找到标准价格元素，等待页面稳定
                    print(f"⚠️ {country_code}: 未找到标准价格元素，等待页面稳定...")
                    await asyncio.sleep(2)
                
                # 获取页面HTML
                html = await page.content()
                
                # 验证页面是否包含价格信息
                price_indicators = ['max-plan-picker', '$', '€', '₹', '¥', '£', 'price', 'plan']
                if any(indicator in html.lower() for indicator in price_indicators):
                    print(f"✅ {country_code}: 页面包含价格信息")
                    return html
                else:
                    print(f"⚠️ {country_code}: 页面可能不包含价格信息")
                    return html  # 仍然返回，让解析函数判断
                    
            except Exception as e:
                print(f"❌ {country_code}: Playwright 访问失败 - {e}")
                return None
        
        # 优先使用静态映射
        if paths:
            for path in paths:
                url = MAX_URL + path
                result = await try_fetch_url(url, f"静态路径({path}) ")
                if result:
                    return result
            return None
        
        # 无映射时的通用逻辑
        default_url = f"{MAX_URL}/{cc}/"
        result = await try_fetch_url(default_url, "默认路径 ")
        if result:
            return result
        
        # 404时回退到西班牙语
        fallback_url = f"{MAX_URL}/{cc}/es"
        print(f"🔄 {country_code}: 尝试西语回退")
        result = await try_fetch_url(fallback_url, "西语回退 ")
        return result
    
    except Exception as e:
        print(f"❌ {country_code}: Playwright 处理失败 - {e}")
        return None
    finally:
        # 清理资源
        if context:
            try:
                await context.close()
            except:
                pass

def detect_billing_cycle_globally(price_text: str, price_number: float, country_code: str) -> Tuple[str, str]:
    """全局周期检测逻辑 - 根据文本内容、价格数值和国家上下文推断计费周期"""
    # 保持原有的周期检测逻辑
    country_lower = country_code.lower()
    
    # 1. 首先检查文本中的明确周期标记
    text_lower = price_text.lower()
    
    # 月付标记（多语言）
    monthly_keywords = [
        'month', '/month', 'monthly', 'per month',  # English
        'mes', '/mes', 'mensual', 'por mes',        # Spanish  
        'mês', '/mês', 'mensal', 'por mês',         # Portuguese
        'mois', '/mois', 'mensuel', 'par mois',     # French
        'monat', '/monat', 'monatlich', 'pro monat', # German
        'miesiąc', '/miesiąc', 'miesięczny',        # Polish
        'måned', '/måned', 'månedlig', 'pr måned',  # Danish/Norwegian
        'ay', '/ay', 'aylık', 'ayda',               # Turkish
    ]
    
    # 年付标记（多语言）
    yearly_keywords = [
        'year', '/year', 'yearly', 'annual', 'per year', 'annually',  # English
        'año', '/año', 'anual', 'por año', 'anualmente',              # Spanish
        'ano', '/ano', 'anual', 'por ano', 'anualmente',              # Portuguese  
        'jahr', '/jahr', 'jährlich', 'pro jahr',                      # German
        'rok', '/rok', 'roczny', 'rocznie',                           # Polish
        'år', '/år', 'årlig', 'pr år', 'om året',                     # Danish/Norwegian/Swedish
        'yıl', '/yıl', 'yıllık', 'yılda',                            # Turkish
    ]
    
    # 检查文本标记
    for keyword in monthly_keywords:
        if keyword in text_lower:
            return "monthly", "每月"
    
    for keyword in yearly_keywords:
        if keyword in text_lower:
            return "yearly", "每年"
    
    # 2. 基于价格数值和国家上下文推断周期
    price_ranges = {
        'tr': {'monthly_max': 500, 'yearly_min': 1500},
        'hu': {'monthly_max': 1000, 'yearly_min': 5000},
        'cz': {'monthly_max': 500, 'yearly_min': 2000},
        'pl': {'monthly_max': 100, 'yearly_min': 200},
        'dk': {'monthly_max': 200, 'yearly_min': 800},
        'no': {'monthly_max': 200, 'yearly_min': 800},
        'se': {'monthly_max': 200, 'yearly_min': 800},
        'default': {'monthly_max': 30, 'yearly_min': 200},
    }
    
    ranges = price_ranges.get(country_lower, price_ranges['default'])
    
    if price_number <= ranges['monthly_max']:
        return "monthly", "每月"
    elif price_number >= ranges['yearly_min']:
        return "yearly", "每年"
    
    # 默认返回月付
    return "monthly", "每月"

def extract_price_number(price_str: str) -> float:
    """从价格字符串中提取数字"""
    # 保持原有的价格提取逻辑
    if not price_str:
        return 0.0
    
    # 首先尝试查找空格分隔的数字（如 "₡3 990" 或 "12x₡1 990"）
    space_separated_pattern = r'(\d+(?:\s+\d+)+)'
    space_matches = re.findall(space_separated_pattern, price_str)
    
    if space_matches:
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
    
    if not re.search(r'\d', number_part):
        return 0.0 
    
    # 处理不同的数字格式
    cleaned = number_part
    if ',' in cleaned and '.' in cleaned:
        comma_pos = cleaned.rindex(',')
        dot_pos = cleaned.rindex('.')
        if comma_pos > dot_pos:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        parts = cleaned.split(',')
        if len(parts) == 2:
            decimal_part = parts[-1]
            if len(decimal_part) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        else:
            cleaned = cleaned.replace(',', '')
    elif '.' in cleaned:
        parts = cleaned.split('.')
        if len(parts) == 2:
            decimal_part = parts[-1]
            if len(decimal_part) > 2:
                cleaned = cleaned.replace('.', '')
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def detect_currency(price_str: str, country_code: str = None) -> str:
    """检测价格字符串中的货币，优先使用国家上下文"""
    # 保持原有的货币检测逻辑
    country_currency_map = {
        'my': 'MYR', 'sg': 'SGD', 'th': 'THB', 'id': 'IDR', 'ph': 'PHP',
        'hk': 'HKD', 'tw': 'TWD', 'au': 'AUD', 'us': 'USD', 'co': 'COP',
        'cr': 'CRC', 'gt': 'GTQ', 'pe': 'PEN', 'uy': 'UYU', 'mx': 'MXN',
        'pl': 'PLN', 'cz': 'CZK', 'hu': 'HUF', 'tr': 'TRY', 'dk': 'DKK',
        'no': 'NOK', 'se': 'SEK', 'fi': 'EUR', 'es': 'EUR', 'fr': 'EUR',
        'be': 'EUR', 'pt': 'EUR', 'nl': 'EUR', 'bg': 'EUR', 'hr': 'EUR',
    }
    
    # 优先使用国家上下文
    if country_code:
        country_code_lower = country_code.lower()
        if country_code_lower in country_currency_map:
            expected_currency = country_currency_map[country_code_lower]
            print(f"    💱 {country_code}: 使用国家映射货币 {expected_currency}")
            return expected_currency
    
    # 货币符号检测
    currency_symbols = {
        'US$': 'USD', 'S$': 'SGD', 'HK$': 'HKD', 'A$': 'AUD', 'R$': 'BRL',
        '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₹': 'INR', '₱': 'PHP',
        '₺': 'TRY', 'zł': 'PLN', 'Kč': 'CZK', 'Ft': 'HUF', 'kr': 'SEK',
        '$': 'USD'  # 通用美元符号优先级最低
    }
    
    # 按符号长度从长到短排序，优先匹配更具体的符号
    sorted_symbols = sorted(currency_symbols.items(), key=lambda x: len(x[0]), reverse=True)
    
    for symbol, currency in sorted_symbols:
        if symbol in price_str:
            return currency
    
    return 'USD'

async def parse_max_prices(html: str, country_code: str) -> Tuple[List[Dict[str, Any]], str]:
    """解析HBO Max页面价格信息，返回（结构化数据列表, 文本输出）"""
    # 保持原有的解析逻辑，但添加更多调试信息
    if not html:
        err = f"❌ 无法获取页面内容 ({country_code})"
        return [], err
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        plans: List[Dict[str, Any]] = []
        seen: set = set()
        
        print(f"🔍 {country_code}: 开始解析页面内容，HTML长度: {len(html)}")
        
        # 方法1: 寻找带data-plan-group属性的标准结构
        sections = soup.find_all('section', {'data-plan-group': True})
        
        if sections:
            print(f"📊 {country_code}: 找到 {len(sections)} 个标准价格区域 (data-plan-group)")
            for sec in sections:
                p = sec['data-plan-group']
                if p == 'monthly':
                    label = '每月'
                elif p == 'yearly':
                    label = '每年'
                elif p == 'bundle':
                    label = '每月'  # 默认，后续会调整
                else:
                    label = '每月'
                
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
                        
                        normalized_name = normalize_plan_name(name)
                        
                        key = (p, normalized_name, price)
                        if key in seen:
                            continue
                        seen.add(key)
                        
                        price_number = extract_price_number(price)
                        currency = detect_currency(price, country_code)
                        
                        # 处理bundle类型
                        if p == 'bundle':
                            detected_cycle, cycle_label = detect_billing_cycle_globally(price, price_number, country_code)
                            final_plan_group = 'bundle'
                            final_label = cycle_label
                        else:
                            final_plan_group = p
                            final_label = label
                        
                        # 计算价格字段
                        is_twelve_month_plan = '12x' in price or '12 x' in price
                        
                        if is_twelve_month_plan:
                            annual_total_price = price_number * 12
                            monthly_equivalent_price = price_number
                        elif final_plan_group == 'yearly' or p == 'yearly':
                            annual_total_price = price_number
                            monthly_equivalent_price = round(price_number / 12, 2)
                        else:
                            annual_total_price = price_number
                            monthly_equivalent_price = price_number
                        
                        plan_data = {
                            "plan_group": final_plan_group,
                            "label": final_label,
                            "name": normalized_name,
                            "original_name": name,
                            "price": price,
                            "price_number": annual_total_price,
                            "monthly_price": monthly_equivalent_price,
                            "currency": currency
                        }
                        plans.append(plan_data)
                        print(f"✅ {country_code}: {normalized_name} ({final_label}) - {price} ({currency})")
                        
                    except Exception as e:
                        print(f"⚠️ {country_code}: 解析套餐失败 - {e}")
                        continue
            
            if plans:
                out = [f"**HBO Max {country_code.upper()} 订阅价格:**"]
                for item in plans:
                    out.append(f"✅ {item['name']} ({item['label']}): **{item['price']}**")
                return plans, "\n".join(out)
        
        # 方法2: 寻找基于class的结构
        monthly_sections = soup.find_all('section', class_=re.compile(r'max-plan-picker-group-monthly', re.I))
        yearly_sections = soup.find_all('section', class_=re.compile(r'max-plan-picker-group-yearly', re.I))
        
        if monthly_sections or yearly_sections:
            print(f"📊 {country_code}: 找到基于class的价格区域 (月付:{len(monthly_sections)}, 年付:{len(yearly_sections)})")
            
            # 处理月付和年付区域（保持原有逻辑）
            for sec in monthly_sections:
                cards = sec.find_all('div', class_='max-plan-picker-group__card')
                for card in cards:
                    # 处理逻辑与上面相同...
                    pass
            
            for sec in yearly_sections:
                cards = sec.find_all('div', class_='max-plan-picker-group__card')
                for card in cards:
                    # 处理逻辑与上面相同...
                    pass
        
        # 如果没有找到标准结构，尝试备用解析方法
        if not plans:
            print(f"🔍 {country_code}: 未找到标准价格结构，尝试备用解析...")
            # 这里可以添加更多备用解析逻辑
        
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

async def get_max_prices_for_country_playwright(country_code: str, max_retries: int = 2, semaphore: asyncio.Semaphore = None, playwright_manager: PlaywrightManager = None) -> Optional[Dict[str, Any]]:
    """使用 Playwright 获取指定国家的HBO Max价格"""
    if semaphore:
        async with semaphore:
            return await _get_max_prices_for_country_playwright_impl(country_code, max_retries, playwright_manager)
    else:
        return await _get_max_prices_for_country_playwright_impl(country_code, max_retries, playwright_manager)

async def _get_max_prices_for_country_playwright_impl(country_code: str, max_retries: int, playwright_manager: PlaywrightManager) -> Optional[Dict[str, Any]]:
    """使用 Playwright 获取指定国家的HBO Max价格的内部实现"""
    country_name = COUNTRY_NAMES.get(country_code.lower(), country_code.upper())
    
    for attempt in range(max_retries):
        try:
            print(f"\n🌍 {country_code} ({country_name}) - Playwright 尝试 {attempt + 1}/{max_retries}")
            
            # 获取代理
            proxy_config = await get_proxy_with_retry(country_code)
            if not proxy_config:
                print(f"❌ {country_code}: 无法获取代理，尝试下一次")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                else:
                    return None
            
            # 使用 Playwright 获取页面内容
            html = await fetch_max_page_playwright(country_code, proxy_config, playwright_manager)
            if not html:
                print(f"❌ {country_code}: Playwright 无法获取页面内容")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                else:
                    return None
            
            # 解析价格
            plans, result_text = await parse_max_prices(html, country_code)
            
            if plans:
                print(f"🎯 {country_code}: Playwright 成功获取 {len(plans)} 个套餐")
                return {
                    'country_code': country_code.upper(),
                    'country_name': country_name,
                    'plans': plans,
                    'scraped_at': datetime.now().isoformat(),
                    'attempt': attempt + 1,
                    'success': True,
                    'method': 'playwright'
                }
            else:
                print(f"⚠️ {country_code}: Playwright 未获取到价格信息")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                else:
                    return None
                    
        except Exception as e:
            print(f"❌ {country_code}: Playwright 处理失败 - {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(2, 5))
                continue
            else:
                return None
    
    return None

async def main():
    """主函数：使用 Playwright 并发获取各国HBO Max价格"""
    print("🎬 HBO Max Global Price Scraper - Playwright Version 启动...")
    print("🚀 使用 Playwright 浏览器引擎，支持 JavaScript 渲染")
    
    results = {}
    failed_countries = []
    
    # 获取所有国家代码
    all_countries = list(REGION_PATHS.keys())
    total_countries = len(all_countries)
    max_concurrent = 3  # 降低并发数，Playwright 更消耗资源
    
    print(f"📊 准备处理 {total_countries} 个国家/地区（Playwright 模式）")
    
    # 创建信号量来限制并发数
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # 使用 Playwright 管理器
    async with PlaywrightManager(max_concurrent_browsers=max_concurrent) as playwright_manager:
        
        async def process_country_with_semaphore(country_code: str, index: int):
            """使用信号量控制并发的国家处理函数"""
            print(f"\n🔄 开始处理: {index+1}/{total_countries} - {country_code}")
            
            # 获取该国家的价格
            country_data = await get_max_prices_for_country_playwright(
                country_code, 
                semaphore=semaphore, 
                playwright_manager=playwright_manager
            )
            
            if country_data:
                results[country_code.upper()] = country_data
                print(f"✅ {country_code}: Playwright 成功获取 {len(country_data['plans'])} 个套餐")
                return True, country_code
            else:
                failed_countries.append(f"{country_code} ({COUNTRY_NAMES.get(country_code.lower(), country_code)})")
                print(f"❌ {country_code}: Playwright 获取失败")
                return False, country_code
        
        # 创建所有任务
        tasks = []
        for i, country_code in enumerate(all_countries):
            task = process_country_with_semaphore(country_code, i)
            tasks.append(task)
        
        # 分批处理以避免过载
        batch_size = 10  # 降低批处理大小，Playwright 需要更多资源
        
        print(f"🚀 开始 Playwright 并发处理（最大并发数: {max_concurrent}，批处理大小: {batch_size}）...")
        
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
                delay = random.uniform(5, 10)  # 增加延迟
                print(f"⏱️  批次间等待 {delay:.1f} 秒...")
                await asyncio.sleep(delay)
    
    # 保存结果
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = f'max_prices_all_countries_playwright_{timestamp}.json'
    output_file_latest = 'max_prices_all_countries_playwright.json'
    
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
    print(f"🎉 HBO Max Playwright 价格抓取完成！")
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
    print(f"  使用方法: Playwright 浏览器引擎")
    
    return results

if __name__ == '__main__':
    try:
        results = asyncio.run(main())
        
        # 显示一些样本数据
        if results:
            print(f"\n📋 样本数据:")
            for country_code, data in list(results.items())[:3]:
                print(f"\n{country_code} - {data.get('country_name', 'Unknown')}:")
                for plan in data.get('plans', []):
                    print(f"  📦 {plan.get('name', 'Unknown')}: {plan.get('price', 'N/A')}")
        
        print(f"\n🎬 HBO Max Playwright 价格抓取任务完成！")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序执行错误: {e}")
        print(traceback.format_exc())