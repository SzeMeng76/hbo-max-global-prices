#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HBO Max CHANGELOG 归档管理器
每季度自动归档 CHANGELOG，保持主文件的可读性
基于Spotify项目改编，适配HBO Max三个月运行频率
"""

import os
import re
from datetime import datetime, timedelta
from typing import List, Tuple
import calendar

class MaxChangelogArchiver:
    def __init__(self):
        self.changelog_file = "CHANGELOG.md"
        self.archive_dir = "changelog_archive"
        self.header_template = """# HBO Max 价格变化记录

此文件记录 HBO Max 各国套餐价格的变化历史。

> 📊 **说明**：价格变化自动检测功能已启用，每季度（三个月）爬虫运行后都会对比上次的价格数据，生成详细的变化报告。

## 📁 历史归档

| 年季度 | 归档文件 | 变化次数 |
|--------|----------|----------|
{archive_links}

---

## 📅 当前季度记录

{current_quarter_header}
"""
    
    def ensure_archive_directory(self):
        """确保归档目录存在"""
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
            print(f"✅ 创建归档目录: {self.archive_dir}")
    
    def parse_changelog_entries(self) -> Tuple[List[str], List[str]]:
        """解析 CHANGELOG 中的条目，分离需要归档的和保留的"""
        if not os.path.exists(self.changelog_file):
            print(f"⚠️ CHANGELOG 文件不存在: {self.changelog_file}")
            return [], []
        
        with open(self.changelog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有日期条目
        # 匹配格式如: ## 2025-08-05 14:30:22 或 ## 2025-08-05
        date_pattern = r'^## (\d{4}-\d{2}-\d{2})(?:\s+\d{2}:\d{2}:\d{2})?'
        
        lines = content.split('\n')
        entries_to_archive = []
        entries_to_keep = []
        current_entry = []
        current_date = None
        in_entry = False
        
        # 获取当前日期和上个季度的最后一天
        now = datetime.now()
        current_quarter = (now.month - 1) // 3 + 1
        
        if current_quarter == 1:
            # 如果是Q1，上个季度是去年Q4
            last_quarter_year = now.year - 1
            last_quarter = 4
            cutoff_date = datetime(last_quarter_year, 12, 31).date()
        else:
            # 其他情况
            last_quarter_year = now.year
            last_quarter = current_quarter - 1
            last_quarter_end_month = last_quarter * 3
            cutoff_date = datetime(last_quarter_year, last_quarter_end_month, 
                                 calendar.monthrange(last_quarter_year, last_quarter_end_month)[1]).date()
        
        print(f"📅 归档截止日期: {cutoff_date.strftime('%Y-%m-%d')} (上季度结束)")
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 检查是否是日期标题行
            match = re.match(date_pattern, line, re.MULTILINE)
            if match:
                # 保存上一个条目
                if current_entry and current_date:
                    entry_content = '\n'.join(current_entry)
                    if current_date <= cutoff_date:
                        entries_to_archive.append(entry_content)
                    else:
                        entries_to_keep.append(entry_content)
                
                # 开始新条目
                current_date = datetime.strptime(match.group(1), '%Y-%m-%d').date()
                current_entry = [line]
                in_entry = True
            elif in_entry and (line.startswith('## ') or line.startswith('# ')):
                # 遇到新的标题，结束当前条目
                if current_entry and current_date:
                    entry_content = '\n'.join(current_entry)
                    if current_date <= cutoff_date:
                        entries_to_archive.append(entry_content)
                    else:
                        entries_to_keep.append(entry_content)
                
                # 重置状态，这行不是日期条目
                current_entry = []
                current_date = None
                in_entry = False
                
                # 如果这是非日期的标题，需要跳过
                continue
            elif in_entry:
                # 添加到当前条目
                current_entry.append(line)
            
            i += 1
        
        # 处理最后一个条目
        if current_entry and current_date:
            entry_content = '\n'.join(current_entry)
            if current_date <= cutoff_date:
                entries_to_archive.append(entry_content)
            else:
                entries_to_keep.append(entry_content)
        
        return entries_to_archive, entries_to_keep
    
    def create_quarterly_archive(self, entries: List[str], year_quarter: str) -> str:
        """创建季度归档文件"""
        if not entries:
            print(f"⚠️ {year_quarter} 没有需要归档的条目")
            return ""
        
        archive_filename = f"changelog_{year_quarter}.md"
        archive_path = os.path.join(self.archive_dir, archive_filename)
        
        # 生成归档文件内容
        year, quarter = year_quarter.split('-Q')
        quarter_name = f"第{quarter}季度"
        
        # 计算季度的月份范围
        quarter_start_month = (int(quarter) - 1) * 3 + 1
        quarter_end_month = int(quarter) * 3
        
        archive_content = f"""# HBO Max 价格变化记录 - {year}年{quarter_name}

> 📁 **归档说明**：本文件包含 {year}年{quarter_name} 的所有价格变化记录。

## 📊 本季度概览

- **记录时间范围**：{year}-{quarter_start_month:02d}-01 至 {year}-{quarter_end_month:02d}-{calendar.monthrange(int(year), quarter_end_month)[1]:02d}
- **变化记录数量**：{len(entries)} 次
- **归档日期**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
        
        # 添加所有条目
        for entry in entries:
            archive_content += entry + "\n\n"
        
        # 添加页脚
        archive_content += f"""---

📚 **相关链接**：
- [返回主 CHANGELOG](../CHANGELOG.md)
- [查看其他季度归档](./)

*此文件由自动归档系统生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # 写入归档文件
        with open(archive_path, 'w', encoding='utf-8') as f:
            f.write(archive_content)
        
        print(f"✅ 创建季度归档: {archive_path} ({len(entries)} 个条目)")
        return archive_filename
    
    def get_existing_archives(self) -> List[Tuple[str, str, int]]:
        """获取现有归档文件信息"""
        archives = []
        
        if not os.path.exists(self.archive_dir):
            return archives
        
        # 扫描归档目录
        for filename in os.listdir(self.archive_dir):
            if filename.startswith('changelog_') and filename.endswith('.md'):
                # 提取年季度信息
                year_quarter = filename.replace('changelog_', '').replace('.md', '')
                if re.match(r'\d{4}-Q[1-4]', year_quarter):
                    # 统计该归档文件中的条目数量
                    archive_path = os.path.join(self.archive_dir, filename)
                    try:
                        with open(archive_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # 统计 ## YYYY-MM-DD 格式的条目
                        entry_count = len(re.findall(r'^## \d{4}-\d{2}-\d{2}', content, re.MULTILINE))
                        archives.append((year_quarter, filename, entry_count))
                    except Exception as e:
                        print(f"⚠️ 读取归档文件失败: {filename} - {e}")
                        archives.append((year_quarter, filename, 0))
        
        # 按年季度排序（最新的在前）
        archives.sort(key=lambda x: x[0], reverse=True)
        return archives
    
    def generate_archive_links(self, archives: List[Tuple[str, str, int]]) -> str:
        """生成归档链接表格"""
        if not archives:
            return "| - | 暂无归档 | - |"
        
        links = []
        for year_quarter, filename, count in archives:
            year, quarter = year_quarter.split('-Q')
            display_name = f"{year}年Q{quarter}"
            link = f"| {display_name} | [changelog_{year_quarter}.md]({self.archive_dir}/{filename}) | {count} |"
            links.append(link)
        
        return '\n'.join(links)
    
    def update_main_changelog(self, entries_to_keep: List[str], new_archives: List[str]):
        """更新主 CHANGELOG 文件"""
        # 获取所有归档信息
        existing_archives = self.get_existing_archives()
        archive_links = self.generate_archive_links(existing_archives)
        
        # 生成当前季度标题
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        current_quarter_header = f"### {now.year}年Q{quarter}"
        
        # 生成新的 CHANGELOG 内容
        new_content = self.header_template.format(
            archive_links=archive_links,
            current_quarter_header=current_quarter_header
        )
        
        # 添加保留的条目
        if entries_to_keep:
            for entry in entries_to_keep:
                new_content += entry + "\n\n"
        else:
            new_content += "\n*本季度暂无价格变化记录*\n\n"
        
        # 写入文件
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 更新主 CHANGELOG: {self.changelog_file}")
    
    def should_archive(self) -> bool:
        """判断是否应该执行归档（每季度第一个月前7天内）"""
        now = datetime.now()
        # 在每季度第一个月（1月、4月、7月、10月）的前7天内执行归档
        return now.day <= 7 and now.month in [1, 4, 7, 10]
    
    def archive_last_quarter(self) -> Tuple[int, List[str]]:
        """归档上个季度的记录"""
        print("🗂️ 开始执行 HBO Max CHANGELOG 季度归档...")
        
        # 确保归档目录存在
        self.ensure_archive_directory()
        
        # 解析现有记录
        entries_to_archive, entries_to_keep = self.parse_changelog_entries()
        
        if not entries_to_archive:
            print("📝 没有需要归档的历史记录")
            return 0, []
        
        # 按季度分组归档条目
        quarterly_entries = {}
        for entry in entries_to_archive:
            # 提取日期
            match = re.search(r'^## (\d{4}-\d{2})-\d{2}', entry, re.MULTILINE)
            if match:
                year = int(match.group(1)[:4])
                month = int(match.group(1)[5:7])
                quarter = (month - 1) // 3 + 1
                year_quarter = f"{year}-Q{quarter}"
                
                if year_quarter not in quarterly_entries:
                    quarterly_entries[year_quarter] = []
                quarterly_entries[year_quarter].append(entry)
        
        # 创建季度归档文件
        archived_files = []
        total_archived = 0
        
        for year_quarter, entries in quarterly_entries.items():
            archive_filename = self.create_quarterly_archive(entries, year_quarter)
            if archive_filename:
                archived_files.append(archive_filename)
                total_archived += len(entries)
        
        # 更新主 CHANGELOG
        self.update_main_changelog(entries_to_keep, archived_files)
        
        print(f"🎉 归档完成！共归档 {total_archived} 个条目到 {len(archived_files)} 个文件")
        return total_archived, archived_files


def main():
    """主函数"""
    archiver = MaxChangelogArchiver()
    
    # 检查是否应该执行归档
    if not archiver.should_archive():
        now = datetime.now()
        print(f"⏰ 当前日期 {now.strftime('%Y-%m-%d')} 不在归档窗口期（每季度首月1-7日）")
        print("跳过归档操作")
        return
    
    # 执行归档
    archived_count, archived_files = archiver.archive_last_quarter()
    
    # 输出结果供 GitHub Actions 使用
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output and github_output != '/dev/stdout':
        with open(github_output, 'a') as f:
            f.write(f"archived_count={archived_count}\n")
            f.write(f"archived_files={','.join(archived_files)}\n")
    else:
        # 如果不在 GitHub Actions 环境中，输出到标准输出
        print(f"archived_count={archived_count}")
        print(f"archived_files={','.join(archived_files)}")


if __name__ == "__main__":
    main()