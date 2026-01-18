# Document Fact-Checking Application

## Overview

This application provides automated fact-checking capabilities for PDF documents. It extracts verifiable claims from uploaded documents and validates them against live web sources using AI-powered analysis.

## Features

- PDF document parsing and text extraction
- Automated claim identification and extraction
- Real-time web verification using search APIs
- AI-powered accuracy assessment
- Interactive results dashboard with color-coded verdicts

## Technology Stack

- **Frontend**: Streamlit
- **AI Model**: Google Gemini (via LangChain)
- **Search API**: Tavily
- **PDF Processing**: PyPDF2
- **Data Handling**: Pandas
- **Language Framework**: Python 3.10+

## Installation

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key
- Tavily API key

### Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd assesment
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure API keys:

Create a `.streamlit/secrets.toml` file with the following content:
```toml
GEMINI_API_KEY = "your-gemini-api-key"
TAVILY_API_KEY = "your-tavily-api-key"
```

## Usage

### Running Locally

Start the application with:
```bash
streamlit run streamlit_app.py
```

The application will open in your default browser at `http://localhost:8501`.

### Using the Application

1. Upload a PDF document using the file uploader
2. The system will automatically extract text content
3. Claims are identified and categorized
4. Each claim is verified against web sources
5. Results are displayed with verdicts and supporting evidence

## Verification Categories

- **Verified**: Claim is accurate and supported by current sources
- **Inaccurate**: Claim contains incorrect information
- **False**: Claim is demonstrably untrue
- **Outdated**: Information was accurate but is no longer current
- **Unverifiable**: Insufficient evidence to confirm or deny
- **Error**: Technical issue during verification

## Deployment

### Railway Deployment

This application is configured for deployment on Railway using the included `railway.toml` configuration file.

Set environment variables in Railway dashboard:
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`

The application will automatically deploy when changes are pushed to the main branch.

## Project Structure

```
assesment/
├── streamlit_app.py      # Main application interface
├── verifier.py           # Core verification logic
├── requirements.txt      # Python dependencies
├── railway.toml          # Railway deployment config
└── .streamlit/
    └── secrets.toml      # API keys (not committed)
```

## Dependencies

- streamlit>=1.31.0
- langchain>=0.3.19
- langchain-google-genai>=2.0.0
- langchain-community>=0.3.18
- google-generativeai>=0.7.0
- tavily-python>=0.3.3
- pypdf2>=3.0.1
- pandas>=2.2.0
- python-dotenv>=1.0.1
- pydantic>=2.0.0

## How It Works

1. **Document Processing**: The application extracts text from uploaded PDF files using PyPDF2
2. **Claim Extraction**: Google Gemini identifies verifiable claims within the text
3. **Web Search**: Tavily API searches for relevant information about each claim
4. **Verification**: AI analyzes search results to determine claim accuracy
5. **Presentation**: Results are displayed in an interactive table with color-coded verdicts

## Limitations

- Requires valid API keys for Google Gemini and Tavily
- PDF must contain extractable text (not scanned images)
- Verification accuracy depends on available web sources
- Rate limits apply based on API subscription tier

## License

This project is provided as-is for educational and assessment purposes.

## Support

For issues or questions, please refer to the project documentation or contact the development team.
