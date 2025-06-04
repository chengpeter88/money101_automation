from src.crawlers.credit_card_crawler import CreditCardCrawler
# from src.crawlers.personal_loan_crawler import PersonalLoanCrawler

def main():
    credit_card_crawler = CreditCardCrawler()
    # personal_loan_crawler = PersonalLoanCrawler()

    try:
        print("開始爬取信用卡資訊...")
        credit_card_data = credit_card_crawler.crawl_credit_cards()
        print(f"成功爬取 {len(credit_card_data)} 張信用卡資訊")
        credit_card_crawler.save_to_file(credit_card_data)

        # print("開始爬取個人貸款資訊...")
        # personal_loan_data = personal_loan_crawler.crawl_loans()
        # print(f"成功爬取 {len(personal_loan_data)} 個貸款產品資訊")
        # personal_loan_crawler.save_to_file(personal_loan_data)

        print("爬蟲任務完成")
    except Exception as e:
        print(f"爬蟲過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        credit_card_crawler.close()
        # personal_loan_crawler.close()

if __name__ == "__main__":
    main()