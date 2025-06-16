import os
import re
from pathlib import Path

class ArticleAnalyzer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.articles_data = []

    def extract_article_info(self):
        """提取所有文章資訊"""
        # 取得所有content檔案
        content_files = list(self.data_dir.glob("article_*_content.txt"))
        
        for content_file in sorted(content_files, key=lambda x: int(re.search(r'article_(\d+)_content', x.name).group(1))):
            article_num = re.search(r'article_(\d+)_content', content_file.name).group(1)
            
            # 對應的表格檔案
            table_file = self.data_dir / f"article_{article_num}_tables.txt"
            
            # 提取文章資訊
            article_info = self.analyze_single_article(content_file, table_file, article_num)
            if article_info:
                self.articles_data.append(article_info)
        
        return self.articles_data

    def analyze_single_article(self, content_file, table_file, article_num):
        """分析單篇文章"""
        try:
            # 讀取內容檔案
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 讀取表格檔案（如果存在）
            tables_content = ""
            if table_file.exists():
                with open(table_file, 'r', encoding='utf-8') as f:
                    tables_content = f.read()
            
            # 提取文章資訊
            title = self.extract_title_from_content(content)
            link = self.extract_link_from_content(content)
            publish_date = self.extract_publish_date(content)
            categories = self.extract_categories(content)
            topics = self.extract_topics(content, tables_content)
            total_chars = self.count_characters(content, tables_content)
            
            return {
                "文章編號": article_num,
                "文章標題": title,
                "文章連結": link,
                "發布日期": publish_date,
                "文章分類": categories,
                "主要主題": topics,
                "總字數": total_chars,
                "內容檔案": content_file.name,
                "表格檔案": table_file.name if table_file.exists() else "無",
                "有表格": table_file.exists()
            }
            
        except Exception as e:
            print(f"處理文章 {article_num} 時發生錯誤: {e}")
            return None

    def extract_title_from_content(self, content):
        """從內容中提取標題"""
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('標題:'):
                title = line.replace('標題:', '').strip()
                return title
        
        return f"未找到標題"

    def extract_link_from_content(self, content):
        """從內容中提取連結"""
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('連結:'):
                link = line.replace('連結:', '').strip()
                return link
        
        return "未找到連結"

    def extract_publish_date(self, content):
        """從內容中提取發布日期"""
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('發布日期:'):
                date = line.replace('發布日期:', '').strip()
                return date
        
        return "未找到發布日期"

    def extract_categories(self, content):
        """從內容中提取分類"""
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('分類:'):
                categories = line.replace('分類:', '').strip()
                # 將分類分割成列表
                category_list = [cat.strip() for cat in categories.split(',')]
                return category_list
        
        return ["未分類"]

    def extract_topics(self, content, tables_content):
        """提取主要主題關鍵字"""
        combined_text = content + " " + tables_content
        
        # 定義主題關鍵字映射
        topic_keywords = {
            "信用卡優惠": ["折扣", "優惠", "回饋", "紅利", "積分", "現金回饋"],
            "電影娛樂": ["威秀", "電影", "影城", "IMAX", "TITAN", "購票"],
            "餐飲美食": ["王品", "餐廳", "美食", "生日", "買一送一", "用餐"],
            "旅遊消費": ["KKday", "旅遊", "訂房", "機票", "行程"],
            "銀行服務": ["年費", "免年費", "申請", "核卡", "帳單"],
            "支付方式": ["APP", "電子支付", "行動支付", "瘋Pay", "刷卡"],
            "會員權益": ["會員", "VIP", "專屬", "特權", "升等"],
            "消費分析": ["評價", "心得", "推薦", "比較", "適合"],
            "促銷活動": ["限時", "期間限定", "活動", "特價", "折扣碼"]
        }
        
        detected_topics = []
        for topic, keywords in topic_keywords.items():
            keyword_count = sum(combined_text.count(keyword) for keyword in keywords)
            if keyword_count >= 2:  # 至少出現2次相關關鍵字
                detected_topics.append(f"{topic}({keyword_count})")
        
        return detected_topics if detected_topics else ["一般金融"]

    def count_characters(self, content, tables_content):
        """計算總字數（排除格式標記）"""
        combined_text = content + tables_content
        
        # 移除檔案路徑標記
        combined_text = re.sub(r'// filepath:.*?\n', '', combined_text)
        
        # 移除標題、連結、日期、分類等格式標記
        combined_text = re.sub(r'^標題:.*?\n', '', combined_text, flags=re.MULTILINE)
        combined_text = re.sub(r'^連結:.*?\n', '', combined_text, flags=re.MULTILINE)
        combined_text = re.sub(r'^發布日期:.*?\n', '', combined_text, flags=re.MULTILINE)
        combined_text = re.sub(r'^分類:.*?\n', '', combined_text, flags=re.MULTILINE)
        combined_text = re.sub(r'^完整內容:.*?\n', '', combined_text, flags=re.MULTILINE)
        
        # 移除markdown標記
        combined_text = re.sub(r'#{1,6}\s*', '', combined_text)
        combined_text = re.sub(r'●\s*', '', combined_text)
        
        # 只計算中文、英文、數字
        clean_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', combined_text)
        
        return len(clean_text)

    def save_results(self, output_file="articles_analysis.txt"):
        """儲存分析結果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("RooCash 文章分析報告\n")
            f.write("=" * 60 + "\n\n")
            
            for article in self.articles_data:
                f.write(f"文章編號: {article['文章編號']}\n")
                f.write(f"文章標題: {article['文章標題']}\n")
                f.write(f"文章連結: {article['文章連結']}\n")
                f.write(f"發布日期: {article['發布日期']}\n")
                f.write(f"文章分類: {', '.join(article['文章分類'])}\n")
                f.write(f"主要主題: {', '.join(article['主要主題'])}\n")
                f.write(f"總字數: {article['總字數']:,}\n")
                f.write(f"內容檔案: {article['內容檔案']}\n")
                f.write(f"表格檔案: {article['表格檔案']}\n")
                f.write(f"包含表格: {'是' if article['有表格'] else '否'}\n")
                f.write("-" * 50 + "\n\n")
        
        print(f"分析結果已儲存到 {output_file}")

    def save_to_csv(self, output_file="articles_data.csv"):
        """儲存為CSV格式"""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['文章編號', '文章標題', '文章連結', '發布日期', '文章分類', 
                         '主要主題', '總字數', '內容檔案', '表格檔案', '有表格']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for article in self.articles_data:
                # 將列表轉換為字串
                article_copy = article.copy()
                article_copy['文章分類'] = ', '.join(article['文章分類'])
                article_copy['主要主題'] = ', '.join(article['主要主題'])
                article_copy['有表格'] = '是' if article['有表格'] else '否'
                writer.writerow(article_copy)
        
        print(f"CSV 檔案已儲存到 {output_file}")

    def generate_summary(self):
        """生成統計摘要"""
        if not self.articles_data:
            return
        
        total_articles = len(self.articles_data)
        articles_with_tables = sum(1 for article in self.articles_data if article['有表格'])
        total_chars = sum(article['總字數'] for article in self.articles_data)
        avg_chars = total_chars / total_articles if total_articles > 0 else 0
        
        # 分類統計
        all_categories = []
        for article in self.articles_data:
            all_categories.extend(article['文章分類'])
        
        category_counts = {}
        for category in all_categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 主題統計
        all_topics = []
        for article in self.articles_data:
            all_topics.extend([topic.split('(')[0] for topic in article['主要主題']])
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        print("\nRooCash 文章分析統計摘要")
        print("=" * 40)
        print(f"總文章數: {total_articles}")
        print(f"包含表格的文章數: {articles_with_tables}")
        print(f"總字數: {total_chars:,}")
        print(f"平均字數: {avg_chars:.0f}")
        
        print(f"\n文章分類分佈:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count} 篇")
            
        print(f"\n主題分佈:")
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {topic}: {count} 篇")

def main():
    # 使用方式
    data_dir = "/Users/heng/Documents/money101_automation/roocash_data"
    
    analyzer = ArticleAnalyzer(data_dir)
    
    print("開始分析 RooCash 文章...")
    articles = analyzer.extract_article_info()
    
    print(f"共分析了 {len(articles)} 篇文章")
    
    # 顯示統計摘要
    analyzer.generate_summary()
    
    # 儲存詳細結果
    analyzer.save_results("roocash_articles_analysis.txt")
    
    # 儲存為CSV格式
    analyzer.save_to_csv("roocash_articles_data.csv")
    
    # 顯示前3篇文章的範例
    print(f"\n前3篇文章範例:")
    print("=" * 50)
    for i, article in enumerate(articles[:3]):
        print(f"\n{i+1}. {article['文章標題']}")
        print(f"   連結: {article['文章連結']}")
        print(f"   發布日期: {article['發布日期']}")
        print(f"   分類: {', '.join(article['文章分類'])}")
        print(f"   主題: {', '.join(article['主要主題'])}")
        print(f"   字數: {article['總字數']:,}")

if __name__ == "__main__":
    main()