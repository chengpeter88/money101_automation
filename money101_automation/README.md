# Money101 Automation

This project is designed to automate the process of crawling and extracting financial information, specifically credit card and personal loan data. The project is structured to facilitate easy maintenance and iteration.

## Project Structure

```
money101_automation
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── crawlers
│   │   ├── __init__.py
│   │   ├── base_crawler.py
│   │   ├── credit_card_crawler.py
│   │   └── personal_loan_crawler.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── browser.py
│   │   ├── file_manager.py
│   │   └── html_parser.py
│   └── config
│       ├── __init__.py
│       └── settings.py
├── output
│   ├── credit_cards
│   └── personal_loans
├── logs
├── requirements.txt
├── README.md
└── setup.py
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd money101_automation
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Navigate to the `src` directory:
   ```
   cd src
   ```

2. Run the main application:
   ```
   python main.py
   ```

## Output

- The crawled credit card data will be saved in the `output/credit_cards` directory.
- The crawled personal loan data will be saved in the `output/personal_loans` directory.
- Log files will be stored in the `logs` directory.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.