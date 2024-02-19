![My Project Logo](https://github.com/viaConBodhi/jira_migration/blob/main/images/migrate.png)

# Jira Service Management Migration Project

## Overview
This project facilitates the migration of an on-prem Jira Service Management system to the cloud. The need for migration arises from the discontinuation of maintenance support for the on-prem version. A significant aspect of this migration is the custom ETL (Extract, Transform, Load) process, specifically designed to remove Protected Health Information (PHI) from Jira tickets that support clinical research.

## Key Features
- **Custom ETL Processing:** Scripts to extract Jira data, transform it by removing PHI, and load it into a cloud-based Jira Service Management system.
- **Data Integrity:** Ensures that all relevant data, excluding PHI, is accurately migrated to the cloud environment.
- **Migration Checklist:** Detailed tasks and checks to ensure a complete and secure migration process, including worklogs, attachments, comments, and user permissions.
- **Cloud Migration Preparation:** Preparation steps and considerations for migrating to a cloud-based service, addressing potential challenges and solutions.

## Requirements
- Python 3.8 or higher
- Pandas for data manipulation
- Requests for API interactions
- GSpread for Google Sheets integration
- Additional Python libraries: numpy, re (regular expressions), datetime, json, csv
- Requirements found in requirements.txt

## Setup and Installation
1. Ensure Python 3.8 or higher is installed on your system.
2. Install the required Python libraries using pip: pip install pandas requests gspread numpy

3. Clone this repository to your local machine.
4. Create a file called `jira_config.py` in the utilz directory. This file should contain a dictionary with the following config items:
    ```python
    jconfig = {
        'api_token': 'Jira API Key',
        'url': 'Jira Site Name using the format: sitename.atlassian.net',
        'jira_user_name': 'Jira User Name',
        'db_server': 'Your Local Jira Database Server',
        'database': 'Your Local Database Name',
        'db_username': 'Your Local Database User Name',
        'db_password': 'Your Local Database Password',
        'output_path': 'Location where the post processed CSV will be stored so you can load into the cloud',
        'issue_folder_path': 'Local directory containing excel files provided by Jira agents with Jira ticket they need migrated',
        'issue_error_path': 'Location where the error logs will be stored for processing Jira issues into the CSV',
        'attachments_folder_path': 'Local directory containing excel files provided by Jira agents with Jira attachments they need migrated',
        'attachments_error_path': 'Location where the error logs will be stored for processing Jira attachments'
    }
    ```

5. Follow Google and gspread.service_account instructions to create a json file the contains the required credentials and name this file `jira_migration_cloud_key.json` and store in the `utliz` directory

## Usage
The migration process is divided into multiple steps, outlined in the Jupyter Notebook (`migrate_jira.ipynb`) included in this repository. Each step must be executed sequentially to ensure a smooth migration:
- Special Note: You'll need to review the code and update project IDs and custom field names where appropriate 
1. **Data Extraction:** Scripts to extract data from the on-prem Jira system and related databases.
2. **Data Transformation:** Custom scripts to identify and remove PHI from the extracted data.
3. **Data Loading:** Scripts to load the transformed data into the Jira Cloud environment, including specific processes for attachments, comments, and worklogs.
4. **Post-Migration Validation:** Scripts to validate the migrated data against the source data to ensure completeness and integrity.

## Custom ETL Process Overview
- `list_files_in_folder`: Lists all files in a specified folder path, aiding in the migration of attachments and other file-based data.
- `remove_non_ascii`: Removes non-ASCII characters from text, ensuring compatibility with the cloud environment.
- `worklog_fields`: Preprocessing worklog records from on-prem system to the cloud, with specific handling to maintain links and references within tickets.
- `comment_fields`: Preprocessing comment records from on-prem system to the cloud, with specific handling to maintain links and references within tickets.
- `watchers_fields`: Preprocessing issue watchers from on-prem system to the cloud, with specific handling to maintain links and references within tickets.
- `process_attachments`: Migrates attachments from the on-prem system to the cloud, with specific handling to maintain links and references within tickets.
- `update_google_sheets_reporting_views`: Updates Google Sheets with migration progress and status, facilitating project tracking and reporting.

## Migration Checklist
A comprehensive checklist is provided to guide you through the migration process, ensuring no data is missed and all necessary transformations are applied. This checklist includes steps for pre-migration data cleanup, PHI data identification and removal, user and permissions mapping, and post-migration validation.

## Contributing
Contributions to this project are welcome. Please fork the repository and submit pull requests with any enhancements, bug fixes, or documentation improvements.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- The migration team for their insights and testing.
- The Jira Cloud API documentation for providing comprehensive integration guidance.
