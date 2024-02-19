#####################
#   file to delete all issue records in the cloud using the csv that loaded the records
#
####################


from jm_utilz import *
from utliz.jira_config import *
from multiprocessing import Process

api_token = jconfig['api_token']
url=jconfig['url']
jira_session = Jira(url, jconfig['jira_user_name'], api_token)

#validate the CSV records exist in the cloud
output_path = jconfig['output_path'] # location of the csv that is loaded into the cloud
df = pd.read_csv(output_path, header=None, encoding = "ISO-8859-1")
df.columns = df.iloc[0]
df = df.reindex(df.index.drop(0)).reset_index(drop=True)
df['Parent_Issue_ID'] = pd.to_numeric(df['Parent_Issue_ID'], errors='coerce').astype('Int64')
df = df.sort_values(by='Parent_Issue_ID', na_position='last')
csv_issue_keys = list(df['Issue_key'])


get_all_cloud_issues = jira_session.get_all_issues()
cloud_issue_keys = set(list(get_all_cloud_issues.key))
print(len(get_all_cloud_issues), ' <-- len of the cloud issue records') #key
missing_cloud_records = set(csv_issue_keys) - cloud_issue_keys
print(len(missing_cloud_records), ' <-- number of missing csv records from the cloud')
new_cloud_records = list(cloud_issue_keys - set(csv_issue_keys))


# if len(cloud_issue_keys) > 0:
#     for l in list(cloud_issue_keys):
#         jira_session.delete_issue(l)

df_child = df[~df.Parent_Issue_ID.isna()]
df_parent = df[df.Parent_Issue_ID.isna()]


for i in list(df_child['Issue_key']):
    
    jira_session.delete_issue(i)
    print('delete subtask')
    print('')


for i in list(df_parent['Issue_key']):
    
    jira_session.delete_issue(i)
    print('delete parent')
    print('')


if len(missing_cloud_records) > 0:
    for l in list(missing_cloud_records):
        jira_session.delete_issue(l)


if len(new_cloud_records) > 0:
    for l in new_cloud_records:
        jira_session.delete_issue(l)    
        

# limit of items multiprocessed based on cores
# limit = 4
# # counter 
# current = 0
# instrument_counter = 0
# files_list = list(cloud_issue_keys)

# while current < len(files_list):
#     processes = []
#     todo = len(files_list) - current
#     if todo < limit:
#         limit = todo

#     for _ in range(limit):
#         processes.append(Process(target=jira_session.delete_issue, args=(files_list[current]) ))
#         current += 1

#     for p in processes:
#         p.start()

#     for p in processes:
#         p.join()


print('')
print('')
print('*******************')
print('Delete is done son')
