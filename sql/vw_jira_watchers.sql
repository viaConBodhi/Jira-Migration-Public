USE [jira]
GO

/****** Object:  View [dbo].[vw_jira_watchers]    Script Date: 2/16/2024 10:11:43 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



-- Create the view
-- =============================================
-- Author: 
-- Create date: 01/08/2024
-- Description: View to assist with the migration process by returning data on watchers for an issue
-- =============================================
CREATE VIEW [dbo].[vw_jira_watchers] AS
SELECT 
	i.ID AS 'issue_id',
	i.issuenum, 
	i.PROJECT,
	a.SINK_NODE_ID, 
	a.SOURCE_NAME,
	a.ASSOCIATION_TYPE,
	p.ID AS 'project_id',
	p.pname,
	p.pkey,
	p.ORIGINALKEY,
	p.PROJECTTYPE,
	u.lower_user_name,
	p.pkey + '-' + CAST(i.issuenum AS VARCHAR) AS Ticket_Key
FROM 
	[CTS_JiraSvcMgmt].[dbo].jiraissue i
JOIN 
	[CTS_JiraSvcMgmt].[dbo].userassociation a ON i.ID = a.SINK_NODE_ID
JOIN 
	[CTS_JiraSvcMgmt].[dbo].project p ON i.project = p.id
JOIN 
	[CTS_JiraSvcMgmt].[dbo].[app_user] u ON a.SOURCE_NAME = u.user_key
WHERE 
	a.ASSOCIATION_TYPE = 'WatchIssue'



GO


