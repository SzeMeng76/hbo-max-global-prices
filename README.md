# 🎬 HBO Max Global Price Scraper

> Automatically scrape global HBO Max subscription prices with real-time currency conversion to find the most affordable regions

[![Auto Update](https://img.shields.io/badge/Auto%20Update-Weekly-brightgreen)](#)
[![Price Data](https://img.shields.io/badge/Countries-70+-blue)](#)
[![Currency](https://img.shields.io/badge/Convert%20to-CNY-red)](#)

**🌐 Language**: [English](README.md) | [中文](README_zh.md)

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🌍 **Global Price Scraping** | Automatically scrape HBO Max prices from 70+ countries and regions |
| 🔐 **Proxy Integration** | Built-in proxy support for accessing geo-restricted content |
| 💱 **Real-time Currency Conversion** | Integrated exchange rate API, convert all prices to CNY in real-time |
| 🏆 **Smart Sorting & Analysis** | Sort by different plan types, instantly find the cheapest subscription regions |
| 📊 **Standardized Data** | Multi-language plan name standardization and categorization |
| 🤖 **Automated Execution** | GitHub Actions runs automatically every Monday, no manual intervention needed |
| 📈 **Historical Data** | Auto-archive by year, supports price trend analysis |
| 📊 **Price Change Detection** | Quarterly price comparison with detailed change reports and CHANGELOG tracking |

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Proxy Service (for accessing HBO Max in different regions)
- Free [OpenExchangeRates API Key](https://openexchangerates.org/)

### One-Click Setup
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd hbo-max-global-prices

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env file and add your API keys

# 4. Run the complete workflow
python max_scraper.py              # Scrape price data
python max_rate_converter.py       # Convert currency and sort
```

### 🔑 API Configuration

**Local Development:**
```bash
# .env file
PROXY_API_TEMPLATE=http://api.mooproxy.xyz/v1/gen?user=YOUR_USER&country={country}&pass=YOUR_PASS
API_KEY=your_openexchangerates_api_key
```

**GitHub Actions:**
1. Repository Settings → Secrets and variables → Actions
2. Add Secrets:
   - `PROXY_API_TEMPLATE` = Your proxy service API template
   - `EXCHANGE_API_KEY` = Your OpenExchangeRates API key

> 💡 **Get Free Exchange API Key**: Visit [OpenExchangeRates](https://openexchangerates.org/) to register, 1000 free requests per month

## 🤖 Automation Workflow

### 📅 Scheduled Tasks
- **Runtime**: Every Monday 10:00 AM Beijing Time
- **Execution**: Price Scraping → Currency Conversion → Data Commit → File Archive
- **Manual Trigger**: Support GitHub Actions manual execution

### 🔄 Workflow Process
```mermaid
graph LR
    A[Get Proxies] --> B[Scrape Prices]
    B --> C[Convert Currency]
    C --> D[Standardize Data]
    D --> E[Sort & Analyze]
    E --> F[Archive Files]
    F --> G[Commit to Repo]
```

## 📊 Data Output

### Main Files
| Filename | Description | Purpose |
|----------|-------------|---------|
| `max_prices_all_countries.json` | Raw price data | Data source with complete scraping info |
| `max_prices_cny_sorted.json` | CNY sorted data | Analysis results with Top 10 cheapest |

### Featured Data Structure
```json
{
  "_top_10_cheapest_all": {
    "description": "Top 10 cheapest HBO Max plans (all types)",
    "updated_at": "2025-01-30",
    "data": [
      {
        "rank": 1,
        "country_name_cn": "美国",
        "plan_name": "HBO Max (With Ads)",
        "price_cny": 68.50,
        "original_price": "$9.99 per month"
      }
    ]
  }
}
```

## 🏗️ Project Architecture

```
📦 hbo-max-global-prices
├── 🕷️ max_scraper.py                  # Core scraping engine
├── 💱 max_rate_converter.py           # Currency conversion & data processing
├── 📊 max_price_change_detector.py    # Price change detection and comparison
├── 📝 max_changelog_archiver.py       # Changelog management and archiving
├── 📋 requirements.txt                 # Python dependencies
├── ⚙️ .env.example                    # Environment variables template
├── 📁 archive/                        # Historical data archive
│   ├── 2025/                         # Organized by year
│   └── 2026/
├── 📝 CHANGELOG.md                    # Price change history and reports
├── 🔄 .github/workflows/
│   ├── weekly-max-scraper.yml        # Main automation workflow
│   └── manual-test.yml               # Manual testing workflow
├── 📖 README.md                      # English documentation
└── 📖 README_zh.md                   # Chinese documentation
```

## 🌟 Core Features Explained

### Proxy Integration
Automatically obtains proxies for different countries to access geo-restricted HBO Max content:
- ✅ Support for 70+ countries and regions
- ✅ Automatic proxy rotation and retry mechanism
- ✅ Fallback strategies for failed connections

### Multi-language Plan Standardization
Automatically convert localized plan names to unified English standards:

| Original Name | Standardized Name | Region |
|---------------|-------------------|--------|
| HBO Max con anuncios | HBO Max (With Ads) | Spanish |
| HBO Max sin anuncios | HBO Max (Ad-Free) | Spanish |
| HBO Max 广告版 | HBO Max (With Ads) | Chinese |
| HBO Max 无广告版 | HBO Max (Ad-Free) | Chinese |

### Smart Price Extraction
Support various price formats and promotional information:
- ✅ `$9.99 per month` → Extract 9.99
- ✅ `Después, €8,99*** por mes` → Extract 8.99
- ✅ `First month free, then $15/month` → Extract 15.00

### Historical Data Management
- 📅 Auto-categorize archives by year
- 📈 Support long-term price trend analysis
- 🔄 Smart file migration and organization

## 🛠️ Troubleshooting

<details>
<summary>🔍 Common Issues & Solutions</summary>

### Proxy Issues
```bash
# Check proxy configuration
echo $PROXY_API_TEMPLATE

# Test proxy connectivity
curl -x "proxy:port" -U "user:pass" https://www.max.com/us/en
```

### API Limit Handling
- ⚠️ Free Account: 1000 requests/month
- 💡 Error Code 429: Too many requests
- 🔄 Solution: Wait for reset or upgrade plan

### GitHub Actions Debugging
```bash
# Check Secrets configuration
GitHub Repo → Settings → Secrets → PROXY_API_TEMPLATE, EXCHANGE_API_KEY

# View detailed logs
Actions → Select failed workflow → Expand logs
```
</details>

## 📊 Price Change Tracking

### 🔍 Automated Detection
The system automatically compares price data quarterly (every 3 months) and generates detailed change reports:

- ✅ **Price Increase Detection** - Identifies subscription fee increases
- ✅ **Price Decrease Detection** - Spots promotional discounts and price drops
- ✅ **New Plan Detection** - Discovers newly launched subscription tiers
- ✅ **Discontinued Plan Detection** - Tracks removed subscription options
- ✅ **Historical Archive** - Maintains quarterly archives for trend analysis

### 📝 CHANGELOG Integration
All price changes are automatically documented in `CHANGELOG.md` with:
- Detailed change summaries by country and plan type
- Quarterly archive organization
- Easy-to-read change reports with timestamps

## 📈 Data Examples

Latest Global HBO Max Price Top 5:

| Rank | Country | Plan Type | Price (CNY) | Original Price |
|------|---------|-----------|-------------|----------------|
| 🥇 | 美国 | With Ads | ¥68.50 | $9.99/month |
| 🥈 | 墨西哥 | With Ads | ¥85.20 | $99 MXN/month |
| 🥉 | 巴西 | With Ads | ¥92.30 | R$19.90/month |
| 4 | 阿根廷 | With Ads | ¥98.75 | $2599 ARS/month |
| 5 | 哥伦比亚 | With Ads | ¥105.40 | $16900 COP/month |

> 💡 **Prices for reference only**, actual subscriptions may be subject to regional restrictions

## 🔧 Tech Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| ![Python](https://img.shields.io/badge/Python-3.9+-blue) | Core development language | 3.9+ |
| ![HTTPX](https://img.shields.io/badge/HTTPX-Latest-green) | Async HTTP client | Latest |
| ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI/CD-orange) | Automated deployment | - |
| ![OpenExchangeRates](https://img.shields.io/badge/OpenExchangeRates-API-yellow) | Exchange rate data source | v6 |

## ⚠️ Usage Guidelines

- 📚 **Purpose**: For educational and research purposes only, please comply with website terms of service
- 🔐 **Proxy Usage**: Ensure you have proper authorization to use proxy services
- ⏱️ **Frequency**: Built-in delay mechanisms to avoid excessive requests
- 📊 **Accuracy**: Price data is for reference only, official prices prevail
- 🌐 **Limitations**: Some regions may have subscription restrictions

## 🤝 Contributing

Welcome to submit Issues and Pull Requests!

1. Fork this project
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -m 'Add new feature'`
4. Push branch: `git push origin feature/new-feature`
5. Submit Pull Request

## 📝 Changelog

- **v1.0** 🎉 Initial release with global HBO Max price scraping
- **v1.1** 🔧 Enhanced proxy integration and error handling
- **v1.2** 🌍 Added support for 70+ countries and regions
- **v1.3** 💱 Integrated real-time currency conversion
- **v1.4** 🤖 GitHub Actions automation
- **v1.5** 📊 Added automated price change detection and CHANGELOG tracking

## 📄 License

This project is for educational and research purposes only. Please comply with relevant laws and website terms of service.

---

<div align="center">

**🎬 Discover the Best HBO Max Subscription Deals Worldwide!**

[🚀 Get Started](#-quick-start) • [📊 View Data](#-data-output) • [🤖 Automation](#-automation-workflow) • [❓ Issues](../../issues)

**Language**: [English](README.md) | [中文](README_zh.md)

</div>
