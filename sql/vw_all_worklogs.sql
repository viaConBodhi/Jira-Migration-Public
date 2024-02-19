USE [jira]
GO

/****** Object:  View [dbo].[vw_all_worklogs]    Script Date: 2/16/2024 9:45:11 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


-- Alter the view
-- =============================================
-- Author: 
-- Update date: [Your update date]
-- Description: View that gets all Jira worklogs with additional issue details
-- =============================================
CREATE VIEW [dbo].[vw_all_worklogs] AS

SELECT 
    w.*, 
    a.lower_user_name AS 'user_account',
    CAST(i.Project_Key AS VARCHAR) + '-' + CAST(i.Issue_Ticket_Number AS VARCHAR) AS 'Ticket_Key'
FROM 
    [CTS_JiraSvcMgmt].[dbo].[worklog] w
JOIN 
    [CTS_JiraSvcMgmt].[dbo].[app_user] a ON w.AUTHOR = a.user_key
LEFT JOIN 
    [CTS_JiraSvcMgmt].[cic].[vw_jira_issue] i ON w.issueid = i.Issue_ID;
GO







