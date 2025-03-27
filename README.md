# IBM SkillsBuild Platform Scraper

## Overview
The IBM SkillsBuild Platform Scraper is a Python-based tool designed to automate the collection of course and program data from the IBM SkillsBuild platform. This tool simplifies data extraction for further analysis, enabling better insights into the available educational content.

## Features
- **Automated Data Extraction:** Scrapes course titles, descriptions, categories, and other metadata.
- **Customisable Scraping Scope:** Allows targeting specific sections of the platform.
- **Efficient and Scalable:** Utilises multithreading for faster scraping.
- **Output Formats:** Saves extracted data in formats such as JSON, CSV, or a database.

## Prerequisites

### System Requirements
- Python 3.8+
- Operating System: Windows, macOS, or Linux

### Libraries
The following Python libraries are required:
- `requests`
- `beautifulsoup4`
- `selenium`
- `pandas`
- `lxml`

To install the dependencies, run:
```bash
pip install -r requirements.txt
```

### Tools
If using Selenium:
- Chrome WebDriver (ensure the driver version matches your installed Chrome version)

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/ibm-skillsbuild-scraper.git
   cd ibm-skillsbuild-scrapers
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Configure your environment:
   - Create a `.env` file for sensitive information, such as login credentials.
     - USERNAME=your_username 
     - PASSWORD=your_password

## Usage

### Basic Command
Run the scraper using:
```bash
python scrapers.py
```

### Configuration
Modify the `config.json` file to:
- Set target URLs.
- Specify the output format (JSON, CSV, or database).
- Adjust scraping parameters (e.g., delay, headers).

### Output
The scraper outputs data into the `output/` directory by default. The format can be adjusted in the configuration file.

## Project Structure
```plaintext
IBM_Scraper/
├── logs/             # Directory for logs
├── output/           # Directory for scraped data
├── scraper/          # Package for scraper code
│   ├── __init__.py   # Marks the folder as a Python package
│   └── main.py       # Main script for the scraper
└── config.json       # Configuration file
```

## Customisation
- Extend the scraper by adding more parsing logic to `scraper.py`.
- Update `config.json` to include additional fields or URLs to scrape.
- Implement additional output options (e.g., database integration).

## Error Handling
The scraper includes basic error handling for:
- Connection issues
- Rate limiting
- Page structure changes

Logs are stored in the `logs/` directory for debugging purposes.

## Contributing
Contributions are welcome! To contribute:
1. Fork this repository.
2. Create a new branch for your feature/bug fix.
3. Submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements
This project was developed as part of a final-year academic initiative to enhance educational data accessibility.

---

### Contact
For questions or feedback, please contact [Mathis Weil](mailto:ec22995@qmul.ac.uk).
