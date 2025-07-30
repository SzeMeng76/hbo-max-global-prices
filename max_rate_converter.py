#!/usr/bin/env python3
"""
HBO Max Price Rate Converter
汇率转换器 - 将HBO Max各国价格转换为人民币并排序
基于Spotify项目的汇率转换逻辑，优化为HBO Max数据处理
"""

import json
import os
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

# 环境变量配置
API_KEY = os.getenv('API_KEY', '')  # OpenExchangeRates API Key
BASE_CURRENCY = 'USD'  # 基础货币
TARGET_CURRENCY = 'CNY'  # 目标货币（人民币）

# 输入输出文件配置
INPUT_FILE = 'max_prices_all_countries.json'
OUTPUT_FILE = 'max_prices_cny_sorted.json'

# API配置
EXCHANGE_API_URL = f'https://openexchangerates.org/api/latest.json'

def load_max_prices() -> Dict[str, Any]:
    """加载HBO Max价格数据"""
    try:
        if not os.path.exists(INPUT_FILE):
            print(f"❌ 输入文件不存在: {INPUT_FILE}")
            return {}
        
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 成功加载 {len(data)} 个国家的HBO Max价格数据")
        return data
    except Exception as e:
        print(f"❌ 加载数据失败: {e}")
        return {}

def get_exchange_rates() -> Dict[str, float]:
    """获取汇率数据"""
    if not API_KEY:
        print("❌ 未设置API_KEY环境变量")
        return {}
    
    try:
        print("🔄 获取汇率数据...")
        
        params = {
            'app_id': API_KEY,
            'base': BASE_CURRENCY,
            'prettyprint': False,
            'show_alternative': False
        }
        
        response = requests.get(EXCHANGE_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        rates = data.get('rates', {})
        
        if not rates:
            print("❌ 汇率数据为空")
            return {}
        
        print(f"✅ 成功获取 {len(rates)} 种货币的汇率")
        print(f"💱 USD to CNY: {rates.get('CNY', 'N/A')}")
        
        return rates
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return {}
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        return {}
    except Exception as e:
        print(f"❌ 获取汇率失败: {e}")
        return {}

def convert_currency(amount: float, from_currency: str, to_currency: str, rates: Dict[str, float]) -> Optional[float]:
    """转换货币"""
    if not amount or amount <= 0:
        return None
    
    # 如果源货币和目标货币相同
    if from_currency == to_currency:
        return amount
    
    # 如果源货币是基础货币（USD）
    if from_currency == BASE_CURRENCY:
        if to_currency in rates:
            return amount * rates[to_currency]
        else:
            print(f"⚠️ 未找到目标货币汇率: {to_currency}")
            return None
    
    # 如果目标货币是基础货币（USD）
    if to_currency == BASE_CURRENCY:
        if from_currency in rates:
            return amount / rates[from_currency]
        else:
            print(f"⚠️ 未找到源货币汇率: {from_currency}")
            return None
    
    # 通过基础货币（USD）进行转换
    if from_currency in rates and to_currency in rates:
        # 先转换为USD，再转换为目标货币
        usd_amount = amount / rates[from_currency]
        return usd_amount * rates[to_currency]
    else:
        missing_currencies = []
        if from_currency not in rates:
            missing_currencies.append(from_currency)
        if to_currency not in rates:
            missing_currencies.append(to_currency)
        print(f"⚠️ 未找到货币汇率: {', '.join(missing_currencies)}")
        return None

def standardize_plan_name(plan_name: str) -> str:
    """标准化套餐名称（参考Spotify项目逻辑）"""
    if not plan_name:
        return "Unknown Plan"
    
    plan_lower = plan_name.lower()
    
    # HBO Max 特定的套餐名称标准化
    if any(keyword in plan_lower for keyword in ['with ads', 'ad-supported', 'advertisement']):
        return "HBO Max (With Ads)"
    elif any(keyword in plan_lower for keyword in ['ad-free', 'no ads', 'premium']):
        return "HBO Max (Ad-Free)"
    elif any(keyword in plan_lower for keyword in ['ultimate', 'max', 'plus']):
        return "HBO Max Ultimate"
    elif any(keyword in plan_lower for keyword in ['basic', 'standard']):
        return "HBO Max Basic"
    else:
        # 保持原始名称，但清理格式
        return plan_name.strip()

def process_country_data(country_data: Dict[str, Any], rates: Dict[str, float]) -> List[Dict[str, Any]]:
    """处理单个国家的数据"""
    country_code = country_data.get('country_code', '')
    country_name = country_data.get('country_name', '')
    plans = country_data.get('plans', [])
    
    processed_plans = []
    
    for plan in plans:
        try:
            plan_name = standardize_plan_name(plan.get('name', ''))
            original_price = plan.get('price', '')
            price_number = plan.get('price_number', 0)
            currency = plan.get('currency', 'USD')
            plan_group = plan.get('plan_group', 'unknown')
            label = plan.get('label', '未知周期')
            
            # 转换为人民币
            cny_price = convert_currency(price_number, currency, TARGET_CURRENCY, rates)
            
            if cny_price is not None and cny_price > 0:
                processed_plan = {
                    'country_code': country_code,
                    'country_name': country_name,
                    'country_name_cn': get_chinese_country_name(country_name),
                    'plan_name': plan_name,
                    'plan_name_standardized': plan_name,
                    'plan_group': plan_group,
                    'billing_cycle': label,
                    'original_price': original_price,
                    'original_currency': currency,
                    'original_price_number': price_number,
                    'price_cny': round(cny_price, 2),
                    'exchange_rate_used': rates.get(currency, 1.0) if currency != BASE_CURRENCY else rates.get(TARGET_CURRENCY, 7.0)
                }
                processed_plans.append(processed_plan)
                print(f"💰 {country_code} - {plan_name}: {original_price} → ¥{cny_price:.2f}")
            else:
                print(f"⚠️ {country_code} - {plan_name}: 汇率转换失败")
                
        except Exception as e:
            print(f"❌ 处理套餐失败 {country_code} - {plan.get('name', 'Unknown')}: {e}")
            continue
    
    return processed_plans

def get_chinese_country_name(english_name: str) -> str:
    """获取国家的中文名称"""
    country_map = {
        "Malaysia": "马来西亚",
        "Hong Kong": "香港",
        "Philippines": "菲律宾", 
        "Taiwan": "台湾",
        "Indonesia": "印度尼西亚",
        "Singapore": "新加坡",
        "Thailand": "泰国",
        "Colombia": "哥伦比亚",
        "Costa Rica": "哥斯达黎加",
        "Guatemala": "危地马拉",
        "Peru": "秘鲁",
        "Uruguay": "乌拉圭",
        "Mexico": "墨西哥",
        "Honduras": "洪都拉斯",
        "Nicaragua": "尼加拉瓜",
        "Panama": "巴拿马",
        "Argentina": "阿根廷",
        "Bolivia": "玻利维亚",
        "Dominican Republic": "多米尼加共和国",
        "Ecuador": "厄瓜多尔",
        "El Salvador": "萨尔瓦多",
        "Paraguay": "巴拉圭",
        "Chile": "智利",
        "Brazil": "巴西",
        "Jamaica": "牙买加",
        "Montserrat": "蒙特塞拉特",
        "Anguilla": "安圭拉",
        "Antigua and Barbuda": "安提瓜和巴布达",
        "Aruba": "阿鲁巴",
        "Bahamas": "巴哈马",
        "Barbados": "巴巴多斯",
        "Belize": "伯利兹",
        "British Virgin Islands": "英属维尔京群岛",
        "Cayman Islands": "开曼群岛",
        "Curacao": "库拉索",
        "Dominica": "多米尼克",
        "Grenada": "格林纳达",
        "Guyana": "圭亚那",
        "Haiti": "海地",
        "Saint Kitts and Nevis": "圣基茨和尼维斯",
        "Saint Lucia": "圣卢西亚",
        "Saint Vincent and the Grenadines": "圣文森特和格林纳丁斯",
        "Suriname": "苏里南",
        "Trinidad and Tobago": "特立尼达和多巴哥",
        "Turks and Caicos Islands": "特克斯和凯科斯群岛",
        "United States": "美国",
        "Australia": "澳大利亚",
        "Andorra": "安道尔",
        "Bosnia and Herzegovina": "波斯尼亚和黑塞哥维那",
        "Bulgaria": "保加利亚",
        "Croatia": "克罗地亚",
        "Czech Republic": "捷克共和国",
        "Hungary": "匈牙利",
        "North Macedonia": "北马其顿",
        "Moldova": "摩尔多瓦",
        "Montenegro": "黑山",
        "Romania": "罗马尼亚",
        "Serbia": "塞尔维亚",
        "Slovakia": "斯洛伐克",
        "Slovenia": "斯洛文尼亚",
        "Denmark": "丹麦",
        "Finland": "芬兰",
        "Norway": "挪威",
        "Sweden": "瑞典",
        "Spain": "西班牙",
        "France": "法国",
        "Belgium": "比利时",
        "Portugal": "葡萄牙",
        "Netherlands": "荷兰",
        "Poland": "波兰",
        "Turkey": "土耳其"
    }
    return country_map.get(english_name, english_name)

def generate_top_cheapest(all_plans: List[Dict[str, Any]], plan_type: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
    """生成最便宜的套餐排行榜"""
    # 根据套餐类型过滤
    if plan_type == "monthly":
        filtered_plans = [p for p in all_plans if p.get('plan_group') == 'monthly']
    elif plan_type == "yearly":
        filtered_plans = [p for p in all_plans if p.get('plan_group') == 'yearly']
    elif plan_type == "ad_free":
        filtered_plans = [p for p in all_plans if 'ad-free' in p.get('plan_name', '').lower()]
    elif plan_type == "with_ads":
        filtered_plans = [p for p in all_plans if 'with ads' in p.get('plan_name', '').lower()]
    else:
        filtered_plans = all_plans
    
    # 按价格排序
    sorted_plans = sorted(filtered_plans, key=lambda x: x.get('price_cny', float('inf')))
    
    # 生成排行榜
    top_plans = []
    for i, plan in enumerate(sorted_plans[:limit]):
        top_plan = plan.copy()
        top_plan['rank'] = i + 1
        top_plans.append(top_plan)
    
    return top_plans

def main():
    """主函数"""
    print("🎬 HBO Max 价格汇率转换器启动...")
    
    # 加载价格数据
    price_data = load_max_prices()
    if not price_data:
        print("❌ 无法加载价格数据，程序退出")
        return
    
    # 获取汇率
    rates = get_exchange_rates()
    if not rates:
        print("❌ 无法获取汇率数据，程序退出")
        return
    
    # 处理所有国家数据
    all_plans = []
    successful_countries = 0
    failed_countries = 0
    
    print(f"\n🔄 开始处理 {len(price_data)} 个国家的数据...")
    
    for country_code, country_data in price_data.items():
        try:
            processed_plans = process_country_data(country_data, rates)
            if processed_plans:
                all_plans.extend(processed_plans)
                successful_countries += 1
                print(f"✅ {country_code}: 处理完成，获取 {len(processed_plans)} 个套餐")
            else:
                failed_countries += 1
                print(f"⚠️ {country_code}: 未获取到有效套餐")
        except Exception as e:
            failed_countries += 1
            print(f"❌ {country_code}: 处理失败 - {e}")
    
    if not all_plans:
        print("❌ 没有有效的套餐数据，程序退出")
        return
    
    print(f"\n📊 数据处理完成:")
    print(f"  成功处理: {successful_countries} 个国家")
    print(f"  处理失败: {failed_countries} 个国家") 
    print(f"  总套餐数: {len(all_plans)} 个")
    
    # 生成各种排行榜
    print(f"\n🏆 生成排行榜...")
    
    # 总体最便宜的前10名
    top_10_all = generate_top_cheapest(all_plans, "all", 10)
    
    # 按月付费最便宜的前10名
    top_10_monthly = generate_top_cheapest(all_plans, "monthly", 10)
    
    # 按年付费最便宜的前10名
    top_10_yearly = generate_top_cheapest(all_plans, "yearly", 10)
    
    # 无广告版本最便宜的前10名
    top_10_ad_free = generate_top_cheapest(all_plans, "ad_free", 10)
    
    # 含广告版本最便宜的前10名
    top_10_with_ads = generate_top_cheapest(all_plans, "with_ads", 10)
    
    # 构建输出数据
    output_data = {
        "_metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_countries": len(price_data),  
            "successful_countries": successful_countries,
            "failed_countries": failed_countries,
            "total_plans": len(all_plans),
            "base_currency": BASE_CURRENCY,
            "target_currency": TARGET_CURRENCY,
            "exchange_api": "OpenExchangeRates",
            "cny_exchange_rate": rates.get(TARGET_CURRENCY, 0)
        },
        "_top_10_cheapest_all": {
            "description": "Top 10 cheapest HBO Max plans (all types)",
            "updated_at": datetime.now().strftime('%Y-%m-%d'),
            "data": top_10_all
        },
        "_top_10_cheapest_monthly": {
            "description": "Top 10 cheapest HBO Max monthly plans", 
            "updated_at": datetime.now().strftime('%Y-%m-%d'),
            "data": top_10_monthly
        },
        "_top_10_cheapest_yearly": {
            "description": "Top 10 cheapest HBO Max yearly plans",
            "updated_at": datetime.now().strftime('%Y-%m-%d'), 
            "data": top_10_yearly
        },
        "_top_10_cheapest_ad_free": {
            "description": "Top 10 cheapest HBO Max ad-free plans",
            "updated_at": datetime.now().strftime('%Y-%m-%d'),
            "data": top_10_ad_free
        },
        "_top_10_cheapest_with_ads": {
            "description": "Top 10 cheapest HBO Max plans with ads",
            "updated_at": datetime.now().strftime('%Y-%m-%d'),
            "data": top_10_with_ads
        }
    }
    
    # 添加所有国家的完整数据
    for country_code, country_data in price_data.items():
        country_plans = [p for p in all_plans if p.get('country_code') == country_code]
        if country_plans:
            output_data[country_code] = {
                "country_name": country_plans[0].get('country_name'),
                "country_name_cn": country_plans[0].get('country_name_cn'),
                "plans": country_plans,
                "total_plans": len(country_plans)
            }
    
    # 保存结果
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 转换结果已保存到: {OUTPUT_FILE}")
        
        # 显示统计信息
        file_size = os.path.getsize(OUTPUT_FILE) / 1024  # KB
        print(f"📁 文件大小: {file_size:.1f} KB")
        
        # 显示排行榜预览
        if top_10_all:
            print(f"\n🏆 HBO Max 全球最便宜前5名:")
            for i, plan in enumerate(top_10_all[:5]):
                print(f"  {i+1}. {plan['country_name_cn']} - {plan['plan_name']}: ¥{plan['price_cny']}")
        
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
        print(traceback.format_exc())

if __name__ == '__main__':
    main()