from src.crawlers.credit_card_crawler import CreditCardCrawler
from src.crawlers.personal_loan_crawler import PersonalLoanCrawler
from src.crawlers.account_crawler import AccountCrawler

def main():
    credit_card_crawler = CreditCardCrawler()
    personal_loan_crawler = PersonalLoanCrawler()
    account_crawler = AccountCrawler()

    try:
        print("開始爬取信用卡資訊...")
        credit_card_data = credit_card_crawler.crawl_credit_cards()
        print(f"成功爬取 {len(credit_card_data)} 張信用卡資訊")
        credit_card_crawler.save_to_file(credit_card_data)

        print("\n開始爬取個人貸款資訊...")
        personal_loan_data = personal_loan_crawler.crawl_loans()
        print(f"成功爬取 {len(personal_loan_data)} 個貸款產品資訊")
        personal_loan_crawler.save_to_file(personal_loan_data)

        print("\n開始爬取證券開戶資訊...")
        account_data = account_crawler.crawl_accounts()
        print(f"成功爬取 {len(account_data)} 個證券開戶產品資訊")
        account_crawler.save_to_file(account_data)

        print("\n所有爬蟲任務完成")
    except Exception as e:
        print(f"爬蟲過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        credit_card_crawler.close()
        personal_loan_crawler.close()
        account_crawler.close()

if __name__ == "__main__":
    main()