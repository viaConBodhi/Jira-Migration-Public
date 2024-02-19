import pandas as pd
import numpy as np
from io import StringIO
import os
from dateutil import parser
import re
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import json
import csv
import gspread
from gspread_dataframe import set_with_dataframe
from sql_utliz import *









# get a list of all files in the folder
def list_files_in_folder(folder_path):
    file_info_list = []
    
    if os.path.isdir(folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_name = file
                file_info_list.append({'file_path': file_path, 'file_name': file_name})
    
    return file_info_list



def remove_non_ascii(text):
    # If the data is not a string, convert it to string
    if not isinstance(text, str):
        text = str(text)
    # Return string with non-ASCII characters removed
    return ''.join(char for char in text if ord(char) < 128)




# mapping where the Jira onprem field values are the key and CSV formatted field titles are the values so the Jira db can be directly 
# aligned with CSV mappings that were orginally built from the onprem CSV export. 
custom_field_dict = {
 'CTMS Protocol #':'STRINGVALUE',
 #'Change reason':'Custom field (Change reason)', # no records being returned
 #'Change risk':'Custom field (Change risk)', # no recoreds being returned
 #'Change risk':'Custom field (Change type)', # no records being returned
 'Contact Email':'STRINGVALUE',
 'Contact Name':'STRINGVALUE',
 'Contact Phone':'STRINGVALUE',
 #'Customer Request Type':'Custom field (Customer Request Type)',# data in STRINGVALUE this is already in the vw_all_jira_issues view
 'Estimated # Patients Consented':'NUMBERVALUE',
 'Estimated # Patients Evaluated':'NUMBERVALUE',
 'Grant #':'STRINGVALUE',
 'Grant Sponsor':'STRINGVALUE',
 'IRB #':'STRINGVALUE',
 #'Impact':'Custom field (Impact)', # no records being returned
 'Index/Account #':'STRINGVALUE',
 'MCC Is Primary':'STRINGVALUE',
 'Oncology Related':'STRINGVALUE',
 'PI Email':'STRINGVALUE',
 'PI Name':'STRINGVALUE',
 'PI ORCID':'STRINGVALUE',
 'PI Phone':'STRINGVALUE',
 'Patient De-Identified #':'NUMBERVALUE',
 'Patient Identified #':'NUMBERVALUE',
 'Project Description':'TEXTVALUE',
 'Project Title':'STRINGVALUE',
 'REDCap Record ID':'STRINGVALUE',
 'Regulatory Compliance Complete':'STRINGVALUE',
 'Research Related':'STRINGVALUE',
 'Responsible Group':'STRINGVALUE',
 'Service/Effort Category':'STRINGVALUE',
 'Sponsor Category':'STRINGVALUE',

# the items below here are either not RDS or were not in the first processing cycle
'Time to first response':'TEXTVALUE',
'Time to resolution':'TEXTVALUE',
'Signature Name':'STRINGVALUE', # only 2 records and looks like maybe test stuff
'Signature Date':'DATEVALUE', # only 2 records from 2021 so most likely test stuff
'Satisfaction':'STRINGVALUE', # only 1 record so most likely test stuff
'Satisfaction date':'DATEVALUE', # only 1 record so most likely test stuff
'PI Program Affiliation':'STRINGVALUE',
'PI Category':'STRINGVALUE',
'Analysis Type 1 # of Samples':'NUMBERVALUE',
'Targeted Analysis Type 1':'STRINGVALUE',
'Targeted Sample Type':'STRINGVALUE',
'Untargeted Sample Type':'STRINGVALUE',
'Analysis Type 2 # of Samples':'NUMBERVALUE',
'Untargeted Analysis Type 1':'STRINGVALUE',
'Untargeted Analysis Type 2':'STRINGVALUE',

 }

# cfname values in the customer_fields_data view that require mapping to the custom field options view
# because their values in the STRINGVALUE field are coded so they need mapped to their actual human readable values 
fields_needing_options_data = ['Sponsor Category', 
                               'Service/Effort Category',
                               'Responsible Group',
                               'Research Related',
                               'Regulatory Compliance Complete',
                               'Oncology Related',
                               'MCC Is Primary',
                               'PI Program Affiliation',
                               'PI Category',
                               'Targeted Analysis Type 1',
                               'Targeted Sample Type',
                               'Untargeted Sample Type',
                               'Untargeted Analysis Type 1',
                               'Untargeted Analysis Type 2']









'''
Time format update notes
Fields in the csv exported from the onprem version
    format example: 7/14/2023  12:00:00 AM 
        Created = mm/dd/yyyy hh:mm:ss AM
        Updated =  mm/dd/yyyy hh:mm:ss AM
        Last Viewed = mm/dd/yyyy hh:mm:ss AM
        Resolved =  mm/dd/yyyy hh:mm:ss AM
        Due Date =  mm/dd/yyyy hh:mm:ss AM

    format example: 29/Jun/23 7:45 PM
        Log Work = dd/month/yy hh:mm PM
        Comment = dd/month/yy hh:mm PM 
    
    
    unknown:
        Custom field (Change start date)
    

    NOT CSV IMPORTED
        Attachements = 28/Jun/23 7:59 PM

'''
def format_date(value):
    # Check if the value is a string or a datetime object and return "dd/Mon/yy hh:mm AM/PM" format
    if isinstance(value, str):
        try:
            # Try to parse the string as a datetime
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%b/%y %I:%M %p")
        except ValueError:
            return None
    elif isinstance(value, datetime):
        if pd.notna(value):  # Check for Not-a-Time (NaT)
            return value.strftime("%d/%b/%y %I:%M %p")
        else:
            return None
    elif pd.isna(value) or np.isnan(value):  # Check for NaT or NaN
        return None  # You can change this to any value you prefer for missing dates
    else:
        return None
    




def make_lists_of_lists_equal_length(list_of_lists, target_length):
    for inner_list in list_of_lists:
        additional_length = target_length - len(inner_list)
        if additional_length > 0:
            inner_list.extend([None] * additional_length)

    return list_of_lists



def make_list_equal_length(input_list, target_length):
    additional_length = target_length - len(input_list)
    if additional_length > 0:
        input_list.extend([None] * additional_length)

    return input_list




def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File '{file_path}' has been deleted.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def df_create_dict(dataframe, key_column, value_column):
    # Check if key and value columns exist in the DataFrame
    if key_column in dataframe.columns and value_column in dataframe.columns:
        # Create a dictionary from the DataFrame
        result_dict = dict(zip(dataframe[key_column], dataframe[value_column]))
        return result_dict
    else:
        print(f"Key column '{key_column}' or value column '{value_column}' not found in the DataFrame.")
        return None   


def check_if_parent_record_exists(df):
    # Create a set of 'Issue id' values
    issue_ids = set(df['Issue id'])
    
    # Filter rows where 'Parent id' is either None or exists in 'Issue id'
    valid_rows = df[df['Parent id'].isna() | df['Parent id'].isin(issue_ids)]

    valid_rows_id = set(valid_rows['Issue id'])
    
    # return the non valid records
    invalid_rows = df[~df['Issue id'].isin(valid_rows_id)]
    
    return valid_rows, invalid_rows


def update_email_format(input_text):
    
    if input_text != None:
    
        # Define a regular expression pattern to match email addresses with 'vcu.edu'
        pattern = r'\[~(.*?)@vcu\.edu\]'

        # Find all matches in the input_text
        matches = re.findall(pattern, input_text)

        # Iterate through the matches and update the format
        for match in matches:
            updated_email = f"@{match}@vcu.edu"
            input_text = input_text.replace(f"[~{match}@vcu.edu]", updated_email)
            
        # Remove the remaining "@vcu.edu" part
        input_text = input_text.replace("@vcu.edu", " ")

        return input_text
    

# only needed for the API use and not the migration 
# def update_time_for_worklog(df):
#     if 'STARTDATE' not in df.columns:
#         print("STARTDATE column not found in DataFrame")
#         return df

#     def format_date(dt):
#         # Localize the timestamp to your local timezone if it's naive
#         # Replace 'America/New_York' with your local timezone if different
#         if dt.tzinfo is None:
#             dt = dt.tz_localize('America/New_York')
        
#         # Convert to UTC
#         dt_utc = dt.astimezone(timezone.utc)
        
#         # Format to match Jira's expected format
#         return dt_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+0000'

#     df['STARTDATE'] = df['STARTDATE'].apply(lambda x: format_date(pd.to_datetime(x)) if not pd.isnull(x) else x)

#     return df



def update_time_for_worklog(df): # goal  '16/Dec/21 9:36 PM'
    if 'STARTDATE' not in df.columns:
        print("STARTDATE column not found in DataFrame")
        return df

    def format_date(dt):
        # Localize the timestamp to your local timezone if it's naive
        if dt.tzinfo is None:
            dt = dt.tz_localize('America/New_York')
        
        # Format to '16/Dec/21 9:36 PM'
        return dt.strftime('%d/%b/%y %I:%M %p')

    df['STARTDATE'] = df['STARTDATE'].apply(lambda x: format_date(pd.to_datetime(x)) if not pd.isnull(x) else x)

    return df



def build_custom_fields(issue_id, custom_field_name, Issue_key, cf_data, cf_options, fields_needing_options_data, custom_field_dict):#, STRINGVALUE, NUMBERVALUE, TEXTVALUE, DATEVALUE
    target_rows = cf_data[(cf_data.ISSUE == issue_id) & (cf_data.cfname == custom_field_name)]
    if len(target_rows) > 0:
        target_rows = target_rows.sort_values(by=['UPDATED'], ascending=False)

        #if len(target_rows) > 1:
            #print(len(target_rows), issue_id, custom_field_name)
        
        if custom_field_name in fields_needing_options_data:
            # process decoding
            custom_field = target_rows.iloc[0]['CUSTOMFIELD']
            stringvalue = int(target_rows.iloc[0]['STRINGVALUE'])
            try:     
                return cf_options[(cf_options.CUSTOMFIELD == custom_field) & (cf_options.ID == stringvalue)].iloc[0]['customvalue']
            except:
                print('')
                print('')
                print('*********************************')
                print(Issue_key, issue_id, custom_field_name, 'potential issue processing this, check for none')
                print('*********************************')
                print('')
                print('')

        else:
            return target_rows.iloc[0][custom_field_dict[custom_field_name]]# take the actual value
        


    else:
        return ''







# update the actionbody field to include the correct formatting Jira needs to parse the comment for dates/commenters/etc
# 11/06/2018 09:44;kmuecke;"This is my test comment"
# https://community.atlassian.com/t5/Jira-Software-questions/CSV-import-with-multiple-comments/qaq-p/630263
# def comment_parser(actionbody,commenter_name,comment_updated):
#     if actionbody != None:
#         return str(comment_updated)+';'+commenter_name.strip()+';'+actionbody
# record_set['actionbody'] = record_set.apply(lambda x: comment_parser(x.actionbody,x.commenter_name,x.comment_updated), axis=1)
# record_set.head(3)


class Jira:
    """
    A class to interact with the Jira API for various operations like fetching field configurations,
    loading attachments, and managing comments and worklogs on issues.
    
    Attributes:
        domain (str): The domain of the Jira instance.
        email (str): The email associated with the Jira account.
        api_token (str): The API token for authenticating requests.
    """

    def __init__(self, domain: str, email: str, api_token: str):
        """
        Initializes the Jira object with the domain, email, and API token.
        
        Parameters:
            domain (str): The domain of the Jira instance.
            email (str): The email associated with the Jira account.
            api_token (str): The API token for authenticating requests.
        """
        self.domain = domain
        self.email = email
        self.api_token = api_token
        self.session = self.jira_auth()


    def jira_auth(self) -> requests.Session:
        """
        Authenticates to the Jira API using the provided credentials and returns a session.
        
        Returns:
            requests.Session: The authenticated session object.
        """
        session = requests.Session()
        session.auth = HTTPBasicAuth(self.email, self.api_token)
        session.headers.update({"Accept": "application/json"})
        return session
    

    def get_field_configurations(self) -> pd.DataFrame:
        """
        Fetches field configurations from Jira and returns them as a pandas DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame containing field configurations.
        """
        field_configurations = []
        start_at = 0
        max_results = 50  # Adjust if needed

        while True:
            url = f"https://{self.domain}/rest/api/3/fieldconfiguration?startAt={start_at}&maxResults={max_results}"
            response = self.session.get(url)

            if response.status_code == 200:
                response_json = response.json()
                field_configurations.extend(response_json.get('values', []))

                if 'isLast' in response_json and response_json['isLast']:
                    break
                else:
                    start_at += max_results
            else:
                print(f"Failed to fetch field configurations: {response.status_code}")
                break

        # Convert to DataFrame
        df = pd.DataFrame(field_configurations)
        return df
 

    def get_fields_paginated(self) -> pd.DataFrame:
        """
        Fetches Jira fields with pagination and returns them as a pandas DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame containing Jira fields.
        """
        fields = []
        start_at = 0
        max_results = 50

        while True:
            url = f"https://{self.domain}/rest/api/3/field/search?startAt={start_at}&maxResults={max_results}"
            response = self.session.get(url)

            if response.status_code == 200:
                response_json = response.json()
                fields.extend(response_json.get('values', []))

                if 'isLast' in response_json and response_json['isLast']:
                    break
                else:
                    start_at += max_results
            else:
                print(f"Failed to fetch fields: {response.status_code}, {response.text}")
                break

        return pd.DataFrame(fields)

    
    
    def load_attachment_from_local(self, issue_key: str, file_path: str) -> None:
        """
        Uploads an attachment to a Jira issue from a local file path.
        
        Parameters:
            issue_key (str): The key of the issue to which the attachment will be uploaded.
            file_path (str): The path to the file to be uploaded.
        """
        url = f"https://{self.domain}/rest/api/2/issue/{issue_key}/attachments"
        auth = HTTPBasicAuth(self.email, self.api_token)

        headers = {
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check"
        }

        with open(file_path, 'rb') as file:
            files = {'file': (file_path, file, 'application-type')}
            response = requests.post(url, headers=headers, auth=auth, files=files)

        if response.status_code == 200:
            response_json = response.json()
            print(json.dumps(response_json, sort_keys=True, indent=4, separators=(",", ": ")))
        else:
            print(f"Failed to upload attachment: {response.status_code}")
    


    def load_attachment_from_url(self, issue_key: str, web_url: str, file_name: str) -> None:
        """
        Uploads an attachment to a Jira issue from a web URL.
        
        Parameters:
            issue_key (str): The key of the issue to which the attachment will be uploaded.
            web_url (str): The URL of the file to be uploaded.
            file_name (str): The name to be assigned to the file in Jira.
        """
        url = f"https://{self.domain}/rest/api/2/issue/{issue_key}/attachments"
        auth = HTTPBasicAuth(self.email, self.api_token)

        headers = {
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check"
        }

        # Fetch the file content from the web URL
        try:
            response = requests.get(web_url, verify=False)
            response.raise_for_status()
            file_content = response.content

            # Prepare the files dictionary with the file content and provided file name
            files = {'file': (file_name, file_content)}

            response = requests.post(url, headers=headers, auth=auth, files=files)

            if response.status_code == 200:
                response_json = response.json()
                print(f'{issue_key} successfully loaded')
                return 1
                #print(json.dumps(response_json, sort_keys=True, indent=4, separators=(",", ": ")))
            else:
                print(f"{issue_key} Failed to upload attachment: {response.status_code}")
                return 0
        except Exception as e:
            print(f"{issue_key} Error fetching or uploading attachment: {str(e)}")
            return 0


    
    def get_comments(self, issue_key: str) -> pd.DataFrame:
        """
        Fetches comments for a specified Jira issue and returns them as a pandas DataFrame.
        
        Parameters:
            issue_key (str): The key of the issue for which comments are to be fetched.
        
        Returns:
            pd.DataFrame: DataFrame containing comments for the specified issue.
        """
        url = f"https://{self.domain}/rest/api/3/issue/{issue_key}/comment"
        auth = HTTPBasicAuth(self.email, self.api_token)

        headers = {
            "Accept": "application/json"
        }

        response = self.session.get(url, headers=headers, auth=auth)

        if response.status_code == 200:
            response_json = response.json()
            df = pd.DataFrame(response_json['comments'])  # Assuming 'comments' is the key in the response
            df['Issue_Key'] = issue_key
            #print(json.dumps(response_json, sort_keys=True, indent=4, separators=(",", ": ")))
            return df
        else:
            print(f"Failed to fetch comments: {response.status_code}")
            return None
 

    def update_comment(self, issue_key: str, comment_id: str, new_body: str) -> None:
        """
        Updates a comment on a specified Jira issue.
        
        Parameters:
            issue_key (str): The key of the issue containing the comment to be updated.
            comment_id (str): The ID of the comment to be updated.
            new_body (str): The new text body for the comment.
        """
        url = f"https://{self.domain}/rest/api/3/issue/{issue_key}/comment/{comment_id}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = self.session.put(url, data=json.dumps(update_payload), headers=headers, auth=self.auth)

        print(f"Request URL: {url}")
        print(f"Request Headers: {headers}")
        print(f"Request Payload: {json.dumps(update_payload)}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")

        if response.status_code == 200:
            response_json = response.json()
            print("Comment in {issue_key} with id {comment_id} updated successfully.")
            #print(json.dumps(response_json, sort_keys=True, indent=4, separators=(",", ": ")))
        else:
            print(f"Failed to update comment in {issue_key} with id {comment_id}: {response.status_code}")

            
            

    def update_comment_jsd_public(self, issue_key: str, comment_id: str, new_jsd_public_value: bool, body: str) -> str:
        """
        Updates a comment in a Jira Service Desk issue, setting its visibility to the public or internal.
        
        Parameters:
            issue_key (str): The key of the issue.
            comment_id (str): The ID of the comment to update.
            new_jsd_public_value (bool): True if the comment should be public, False for internal.
            body (str): The updated text of the comment.
            
        Returns:
            str: A message indicating the update status.
        """
        url = f"https://{self.domain}/rest/api/3/issue/{issue_key}/comment/{comment_id}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        update_payload = {
            "body": body,
            "properties": [
                {
                    "key": "sd.public.comment",
                    "value": {
                        "internal": new_jsd_public_value  # Set to True or False as needed
                    }
                }
            ]
        }

        response = self.session.put(url, data=json.dumps(update_payload), headers=headers)

        # print(f"Request URL: {url}")
        # print(f"Request Headers: {headers}")
        # print(f"Request Payload: {json.dumps(update_payload)}")
        # print(f"Response Status Code: {response.status_code}")
        # print(f"Response Content: {response.text}")

        if response.status_code == 200:
            response_json = response.json()
            print(f"Comment updated successfully in {issue_key} with id {comment_id}.")
            return 'updated'
            #print(json.dumps(response_json, sort_keys=True, indent=4, separators=(",", ": ")))
        else:
            print(f"Failed to update comment in {issue_key} with id {comment_id}: {response.status_code}")
            return 'error'



            
    def add_worklog(self, issue_id_or_key: str, comment: str, started: str, time_spent_seconds: int, user_account_id: str) -> dict:
        """
        Adds a worklog to a Jira issue.
        
        Parameters:
            issue_id_or_key (str): The ID or key of the issue to which the worklog will be added.
            comment (str): The comment associated with the worklog.
            started (str): The start date and time of the worklog.
            time_spent_seconds (int): The time spent in seconds.
            user_account_id (str): The account ID of the user logging the work.
            
        Returns:
            dict: The response from the Jira API as a dictionary.
        """
        url = f"https://{self.domain}/rest/api/3/issue/{issue_id_or_key}/worklog"
        auth = HTTPBasicAuth(self.email, self.api_token)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        payload = {
            "comment": {
                "content": [
                    {
                        "content": [
                            {
                                "text": comment,
                                "type": "text"
                            }
                        ],
                        "type": "paragraph"
                    }
                ],
                "type": "doc",
                "version": 1
            },
            "started": started,
            "timeSpentSeconds": time_spent_seconds,
            "author": {
                "accountId": user_account_id
            }
        }

        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            auth=auth
        )

        return json.loads(response.text)         



    # def delete_issue(self, issue_id_or_key):
    #     url = f"https://{self.domain}/rest/api/3/issue/{issue_id_or_key}"
    #     response = self.session.delete(url)

    #     if response.status_code == 204:
    #         print(f"Issue '{issue_id_or_key}' has been deleted.")
    #     else:
    #         print(f"Failed to delete issue '{issue_id_or_key}': {response.status_code}")


    def delete_issue(self, issue_id_or_key: str) -> None:
        """
        Deletes a Jira issue based on its ID or key.
        
        Parameters:
            issue_id_or_key (str): The ID or key of the issue to be deleted.
        """
        url = f"https://{self.domain}/rest/api/3/issue/{issue_id_or_key}"

        for attempt in range(1, 4):  # Attempt deletion up to 3 times
            response = self.session.delete(url)

            if response.status_code == 204:
                print(f"Issue '{issue_id_or_key}' has been deleted.")
                break
            else:
                print(f"Failed to delete issue '{issue_id_or_key}': {response.status_code} with attempt {attempt}")

            if attempt == 3:
                print(f"Final Error: Unable to delete issue '{issue_id_or_key}'. Status code: {response.status_code}")



    # def get_request_types(self, service_desk_id):
    #     url = f"https://{self.domain}/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype"
    #     response = self.session.get(url)

    #     if response.status_code == 200:
    #         response_data = response.json()
    #         request_types = response_data.get('values', [])

    #         # Convert request_types to a DataFrame
    #         df = pd.DataFrame(request_types)
    #         return df
    #     else:
    #         print(f"Failed to fetch request types: {response.status_code}")
    #         return None

    def get_request_types(self, service_desk_ids: list) -> pd.DataFrame:
        """
        Retrieves request types from one or more Jira Service Desks.
        
        Parameters:
            service_desk_ids (list): A list of Service Desk IDs from which to retrieve request types.
            
        Returns:
            pd.DataFrame: A DataFrame containing request types from the specified Service Desks.
        """
        all_request_types = []

        for service_desk_id in service_desk_ids:
            url = f"https://{self.domain}/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype"
            response = self.session.get(url)

            if response.status_code == 200:
                response_data = response.json()
                request_types = response_data.get('values', [])
                all_request_types.extend(request_types)
            else:
                print(f"Failed to fetch request types for Service Desk ID {service_desk_id}: {response.status_code}")

        # Convert all_request_types to a DataFrame
        df = pd.DataFrame(all_request_types)
        return df


    def get_customers(self, serviceDeskId: int) -> pd.DataFrame: # not working 
        """
        ---> NOT WORKING <---
        Retrieves customers associated with a given Service Desk.
        
        Parameters:
            serviceDeskId (int): The ID of the Service Desk.
            
        Returns:
            pd.DataFrame: A DataFrame containing the customers of the specified Service Desk.
        """ 
        customers = []
        start_at = 0
        max_results = 50  # Adjust if needed

        while True:
            url = f"https://{self.domain}/rest/servicedeskapi/servicedesk/{serviceDeskId}/customer"#?start={start_at}&maxResults={max_results}"
            response = self.session.get(url)

            if response.status_code == 200:
                response_json = response.json()
                customers.extend(response_json.get('values', []))

                if response_json.get('isLastPage', True):
                    break
                else:
                    start_at += max_results
            else:
                print(f"Failed to fetch customers: {response.status_code}")
                break

        # Convert to DataFrame
        df = pd.DataFrame(customers)
        return df

    def get_service_desk(self) -> pd.DataFrame:
        """
        Retrieves information about all Service Desks available to the authenticated user.
        
        Returns:
            pd.DataFrame: A DataFrame containing information about each Service Desk.
        """
        url = f"https://{self.domain}/rest/servicedeskapi/servicedesk"
        response = self.session.get(url)

        if response.status_code == 200:
            service_desk_data = response.json().get('values', [])
            df = pd.DataFrame(service_desk_data)
            return df
        else:
            print(f"Failed to fetch service desk data: {response.status_code}")
            return pd.DataFrame()  # Return an empty DataFrame in case of failure


    def get_user(self, account_id: str) -> dict: # not working, may be permissions related  
        """
        --> NOT WORKING MAY BE PERMISSIONS RELATED <--
        Retrieves information about a Jira user based on their account ID.
        
        Parameters:
            account_id (str): The account ID of the user.
            
        Returns:
            dict: A dictionary containing information about the user.
        """ 
        url = f"https://{self.domain}/rest/api/3/user"
        headers = {
            "Accept": "application/json"
        }
        query = {
            'accountId': account_id
        }

        response = self.session.get(url, headers=headers, params=query)

        if response.status_code == 200:
            return json.loads(response.text)
        else:
            print(f"Failed to fetch user data: {response.status_code}")
            return None


    def get_account_id(self, email: str) -> dict:
        """
        Retrieves the account ID of a Jira user based on their email address.
        
        Parameters:
            email (str): The email address of the user.
            
        Returns:
            dict: A dictionary containing the account ID of the user.
        """
        url = f"https://{self.domain}/rest/api/latest/user/search"
        headers = {
            "Accept": "application/json"
        }

        params = {
            "query": email
        }

        response = self.session.get(url, headers=headers, params=params)

        if response.status_code == 200:
            return json.loads(response.text)
        else:
            print(f"Failed to fetch user data: {response.status_code}, Response: {response.text}")
            return None

    def get_all_issues(self) -> pd.DataFrame:
        """
        Retrieves all issues accessible to the authenticated user, ordered by creation date.
        
        Returns:
            pd.DataFrame: A DataFrame containing all retrieved issues.
        """
        url = f"https://{self.domain}/rest/api/2/search"
        all_issues = []
        start_at = 0
        max_results = 50
        total_issues = None

        while total_issues is None or start_at < total_issues:
            params = {
                "jql": "ORDER BY created",
                "startAt": start_at,
                "maxResults": max_results
            }
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                all_issues.extend(data["issues"])
                total_issues = data["total"]
                start_at += max_results
            else:
                print(f"Failed to fetch issues: {response.status_code}")
                break

        # Convert to DataFrame
        return pd.DataFrame(all_issues)



def get_url(input_string):
    """
    Extracts the first URL that starts with 'https://' from the given input string.
    
    Parameters:
    - input_string (str): The string to search for a URL.
    
    Returns:
    - str: The first found URL starting with 'https://'. If no such URL is found, returns 'error'.
    """

    # Define the regex pattern for URLs starting with 'https://'
    pattern = r'https://[^\s]+'

    # Find the URL in the input string
    match = re.search(pattern, input_string)
    
    # If a match is found, return it; otherwise, return None
    if match:
        return match.group(0)
    else:
        return 'error'
    


    
def get_attachment_id(input_string):
    """
    Extracts the attachment ID from a URL contained within the input string. The URL should start with 
    'https://app.informatics.vcu.edu/cts/secure/attachment/' to be processed correctly.
    
    Parameters:
    - input_string (str): The string containing the URL.
    
    Returns:
    - str: The extracted attachment ID. If the URL is not found or does not match the expected format, returns 'error'.
    """
    url = get_url(input_string)
    if url == 'error':
        return 'error'
    
    # Remove the specified part of the URL to get the attachment ID
    attachment_id = url.replace("https://app.informatics.vcu.edu/cts/secure/attachment/", "").split('/')[0]

    return attachment_id




def find_sql_records(file_name: str) -> int:
    """
    Check if the file name extension ends with .sql
    
    Parameters:
    - file_name: str - The name of the file
    
    Returns:
    - int: 1 if the file name ends with .sql, otherwise 0
    """
    # Check if the file name ends with .sql extension
    if file_name.endswith('.sql'):
        return 1
    else:
        return 0



def unique_elements(list1, list2):
    """
    Returns a list of elements that are unique to each list.
    
    Parameters:
    - list1: List of strings
    - list2: List of strings
    
    Returns:
    - List of strings that are unique to each list.
    """
    # Convert lists to sets to perform set operations
    set1 = set(list1)
    set2 = set(list2)
    
    # Find elements unique to each list
    unique_to_list1 = set1 - set2
    unique_to_list2 = set2 - set1
    
    # Combine the unique elements and convert back to a list
    unique_elements = list(unique_to_list1.union(unique_to_list2))
    
    return unique_elements




def process_attachments(issue_key, record_id, filename, jira_session):
    """
    Loads an attachment from a constructed URL into a JIRA session.
    
    Parameters:
    - issue_key (str): The key of the issue to which the attachment is linked.
    - record_id (str/int): The record ID used to construct the attachment URL.
    - filename (str): The name of the file to be attached.
    - jira_session (object): An instance of a JIRA session with a method `load_attachment_from_url` capable of loading the attachment.
    
    Returns:
    - object: The result of the attachment load operation, as returned by the `load_attachment_from_url` method of the jira_session object.
    """
    root_url = 'https://app.informatics.vcu.edu/cts/secure/attachment/'
    target_url = root_url+str(record_id)+'/'+filename

    load_attachment = jira_session.load_attachment_from_url(issue_key, target_url, filename)
    return load_attachment


