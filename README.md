# WikiBiasTracker

## Overview
WikiBiasTracker is an advanced research tool designed to analyze and track the evolution of Wikipedia articles, with a focus on understanding potential political biases in their revisions. This tool extracts revisions of Wikipedia articles, identifies contributors, and reconstructs article versions at different points in time. The end goal is to develop a web dashboard that allows users to visually explore these revisions, understand contribution patterns, and analyze potential biases of contributors.

### DoltHub

This project uses [DoltHub](https://www.dolthub.com/) to store and manage the data. Dolt is a SQL database that supports distributed version control. DoltHub is a place to share Dolt repositories. The data for this project is stored in a Dolt repository on DoltHub. You can find the repository [here](https://www.dolthub.com/repositories/actual_genius_intellectual/wikipedia-revisions).

## Features
- **Revision Tracking**: Extracts and tracks Wikipedia article revisions over time.
- **Contributor Identification**: Identifies users who have made contributions to each article.
- **Article Reconstruction**: Reconstructs the state of an article at any given point in its history.
- **Change Attribution ("Git Blame")**: Determines which user contributed specific parts of an article.
- **Bias Analysis**: Aims to identify potential political biases in contributions.
- **Web Dashboard**: Provides a user-friendly interface for exploring article histories and analyses.

## Installation

### Prerequisites
- Python 3.6 or higher
- Requests library for Python
- SQLite Database
- Flask for the web dashboard (optional)

### Setup
1. **Clone the Repository**: `git clone https://github.com/yourusername/wiki-trust-py.git`
2. **Install Dependencies**: Run `pip install -r requirements.txt` to install the required Python libraries.
3. **Database Setup**: Use SQLite to set up your database according to the provided schema.
4. **Run the Application**: Execute `python main.py` to start the application.

## Usage
- **Data Collection**: Run `python collect_data.py` to start extracting revisions.
- **Web Dashboard**: If implemented, launch the Flask app to access the dashboard and explore the data.

## Ethical Considerations and Privacy
This project is committed to ethical research practices and respects the privacy of Wikipedia contributors. Our methodology for bias analysis is transparent, and we ensure that the data used does not infringe upon the privacy rights of individuals. We advise users of WikiBiasTracker to adhere to these principles and use the tool responsibly.

## Contributing
We welcome contributions from developers, researchers, and enthusiasts. Please read `CONTRIBUTING.md` for guidelines on how to submit contributions.

## License
This project is licensed under the MIT License - see the `LICENSE` file for details.

## Acknowledgments
- Wikipedia and the Wikimedia Foundation for providing open access to article revision data.
- The Python community for providing excellent libraries that make data handling and web development easier.

## Disclaimer
This tool is for research purposes only. The creators of WikiBiasTracker are not responsible for any misuse of the tool or interpretations of the data provided.
