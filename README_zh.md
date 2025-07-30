# 🎬 HBO Max 全球价格抓取工具

> 自动抓取全球 HBO Max 订阅价格，实时汇率转换，帮你找到最便宜的订阅地区

[![自动更新](https://img.shields.io/badge/自动更新-每周一次-brightgreen)](#)
[![价格数据](https://img.shields.io/badge/国家地区-70+-blue)](#)
[![货币转换](https://img.shields.io/badge/转换为-人民币-red)](#)

**🌐 语言**: [English](README.md) | [中文](README_zh.md)

## ✨ 核心功能

| 功能特性 | 说明描述 |
|---------|----------|
| 🌍 **全球价格抓取** | 自动抓取70+个国家和地区的HBO Max价格 |
| 🔐 **代理集成** | 内置代理支持，访问地理限制内容 |
| 💱 **实时汇率转换** | 集成汇率API，所有价格实时转换为人民币 |
| 🏆 **智能排序分析** | 按不同套餐类型排序，瞬间找到最便宜订阅地区 |
| 📊 **标准化数据** | 多语言套餐名称标准化和分类处理 |
| 🤖 **自动化执行** | GitHub Actions每周一自动运行，无需人工干预 |
| 📈 **历史数据** | 按年份自动归档，支持价格趋势分析 |

## 🚀 快速开始

### 前置条件
- Python 3.9+
- 代理服务（用于访问不同地区的HBO Max）
- 免费的 [OpenExchangeRates API Key](https://openexchangerates.org/)

### 一键配置
```bash
# 1. 克隆仓库
git clone <你的仓库地址>
cd hbo-max-global-prices

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加你的API密钥

# 4. 运行完整工作流
python max_scraper.py              # 抓取价格数据
python max_rate_converter.py       # 货币转换和排序
```

### 🔑 API配置

**本地开发:**
```bash
# .env 文件
PROXY_API_TEMPLATE=http://api.proxy-service.com/v1/gen?user=你的用户名&country={country}&pass=你的密码
API_KEY=你的_openexchangerates_api_密钥
```

**GitHub Actions:**
1. 仓库设置 → Secrets and variables → Actions
2. 添加密钥:
   - `PROXY_API_TEMPLATE` = 你的代理服务API模板
   - `EXCHANGE_API_KEY` = 你的OpenExchangeRates API密钥

> 💡 **获取免费汇率API密钥**: 访问 [OpenExchangeRates](https://openexchangerates.org/) 注册，每月1000次免费请求

## 🤖 自动化工作流

### 📅 定时任务
- **运行时间**: 每周一北京时间上午10点
- **执行流程**: 价格抓取 → 货币转换 → 数据提交 → 文件归档
- **手动触发**: 支持GitHub Actions手动执行

### 🔄 工作流程
```mermaid
graph LR
    A[获取代理] --> B[抓取价格]
    B --> C[货币转换]
    C --> D[标准化数据]
    D --> E[排序分析]
    E --> F[归档文件]
    F --> G[提交到仓库]
```

## 📊 数据输出

### 主要文件
| 文件名 | 描述 | 用途 |
|-------|------|-----|
| `max_prices_all_countries.json` | 原始价格数据 | 包含完整抓取信息的数据源 |
| `max_prices_cny_sorted.json` | 人民币排序数据 | 包含前10名最便宜套餐的分析结果 |

### 特色数据结构
```json
{
  "_top_10_cheapest_all": {
    "description": "全球最便宜的前10名HBO Max套餐",
    "updated_at": "2025-01-30",
    "data": [
      {
        "rank": 1,
        "country_name_cn": "美国",
        "plan_name": "HBO Max (含广告版)",
        "price_cny": 68.50,
        "original_price": "$9.99 per month"
      }
    ]
  }
}
```

## 🏗️ 项目架构

```
📦 hbo-max-global-prices
├── 🕷️ max_scraper.py                  # 核心抓取引擎
├── 💱 max_rate_converter.py           # 货币转换与数据处理
├── 📋 requirements.txt                 # Python依赖包
├── ⚙️ .env.example                    # 环境变量模板
├── 📁 archive/                        # 历史数据归档
│   ├── 2025/                         # 按年份组织
│   └── 2026/
├── 🔄 .github/workflows/
│   ├── weekly-max-scraper.yml        # 主要自动化工作流
│   └── manual-test.yml               # 手动测试工作流
├── 📖 README.md                      # 英文文档
└── 📖 README_zh.md                   # 中文文档
```

## 🌟 核心功能详解

### 代理集成
自动获取不同国家的代理来访问地理限制的HBO Max内容:
- ✅ 支持70+个国家和地区
- ✅ 自动代理轮换和重试机制
- ✅ 连接失败的备用策略

### 多语言套餐标准化
自动将本地化的套餐名称转换为统一的标准格式:

| 原始名称 | 标准化名称 | 地区 |
|---------|-----------|------|
| HBO Max con anuncios | HBO Max (含广告版) | 西班牙语 |
| HBO Max sin anuncios | HBO Max (无广告版) | 西班牙语 |
| HBO Max 广告版 | HBO Max (含广告版) | 中文 |
| HBO Max 无广告版 | HBO Max (无广告版) | 中文 |

### 智能价格提取
支持各种价格格式和促销信息:
- ✅ `$9.99 per month` → 提取 9.99
- ✅ `Después, €8,99*** por mes` → 提取 8.99
- ✅ `First month free, then $15/month` → 提取 15.00

### 历史数据管理
- 📅 按年份自动分类归档
- 📈 支持长期价格趋势分析
- 🔄 智能文件迁移和组织

## 🛠️ 故障排除

<details>
<summary>🔍 常见问题与解决方案</summary>

### 代理问题
```bash
# 检查代理配置
echo $PROXY_API_TEMPLATE

# 测试代理连接
curl -x "代理:端口" -U "用户:密码" https://www.max.com/us/en
```

### API限制处理
- ⚠️ 免费账户: 每月1000次请求
- 💡 错误代码429: 请求过多
- 🔄 解决方案: 等待重置或升级套餐

### GitHub Actions调试
```bash
# 检查密钥配置
GitHub仓库 → 设置 → 密钥 → PROXY_API_TEMPLATE, EXCHANGE_API_KEY

# 查看详细日志
Actions → 选择失败的工作流 → 展开日志
```
</details>

## 📈 数据示例

最新全球HBO Max价格前5名:

| 排名 | 国家 | 套餐类型 | 价格(人民币) | 原始价格 |
|------|------|----------|-------------|----------|
| 🥇 | 美国 | 含广告版 | ¥68.50 | $9.99/月 |
| 🥈 | 墨西哥 | 含广告版 | ¥85.20 | $99 MXN/月 |
| 🥉 | 巴西 | 含广告版 | ¥92.30 | R$19.90/月 |
| 4 | 阿根廷 | 含广告版 | ¥98.75 | $2599 ARS/月 |
| 5 | 哥伦比亚 | 含广告版 | ¥105.40 | $16900 COP/月 |

> 💡 **价格仅供参考**，实际订阅可能受地区限制

## 🔧 技术栈

| 技术 | 用途 | 版本 |
|------|------|------|
| ![Python](https://img.shields.io/badge/Python-3.9+-blue) | 核心开发语言 | 3.9+ |
| ![HTTPX](https://img.shields.io/badge/HTTPX-最新版-green) | 异步HTTP客户端 | 最新版 |
| ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI/CD-orange) | 自动化部署 | - |
| ![OpenExchangeRates](https://img.shields.io/badge/OpenExchangeRates-API-yellow) | 汇率数据源 | v6 |

## ⚠️ 使用须知

- 📚 **用途**: 仅供教育和研究目的，请遵守网站服务条款
- 🔐 **代理使用**: 确保你有合法授权使用代理服务
- ⏱️ **频率**: 内置延迟机制，避免过度请求
- 📊 **准确性**: 价格数据仅供参考，以官方价格为准
- 🌐 **限制**: 某些地区可能有订阅限制

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests!

1. Fork 本项目
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -m 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交 Pull Request

## 📝 更新日志

- **v1.0** 🎉 初始版本，支持全球HBO Max价格抓取
- **v1.1** 🔧 增强代理集成和错误处理
- **v1.2** 🌍 新增70+个国家和地区支持
- **v1.3** 💱 集成实时货币转换
- **v1.4** 🤖 GitHub Actions自动化

## 📄 许可证

本项目仅供教育和研究目的。请遵守相关法律法规和网站服务条款。

---

<div align="center">

**🎬 发现全球最划算的HBO Max订阅优惠!**

[🚀 快速开始](#-快速开始) • [📊 查看数据](#-数据输出) • [🤖 自动化](#-自动化工作流) • [❓ 问题反馈](../../issues)

**语言**: [English](README.md) | [中文](README_zh.md)

</div>