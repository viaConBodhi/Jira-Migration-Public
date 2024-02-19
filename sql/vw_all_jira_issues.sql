USE [jira]
GO

/****** Object:  View [dbo].[vw_all_jira_issues]    Script Date: 2/16/2024 9:43:35 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


-- Alter the view
-- =============================================
-- Author: 
-- Create date: 01/08/2024
-- Description: View that gets all Jira issues with priority and time tracking fields
-- =============================================
CREATE VIEW [dbo].[vw_all_jira_issues] AS
SELECT
    ji.*,
    j.TIMEORIGINALESTIMATE, -- Adding Original Estimate from jiraissue
    j.TIMEESTIMATE, -- Adding Remaining Estimate from jiraissue
    j.TIMESPENT, -- Adding Time Spent from jiraissue
    vf.NAME AS [Customer Request Type],
    pr.pname AS IssuePriority, -- Existing IssuePriority column
	ji.Project_Key + '-' + CAST(ji.Issue_Ticket_Number AS VARCHAR) AS 'Issue_key'
FROM
    [CTS_JiraSvcMgmt].[cic].[vw_jira_issue] ji
JOIN
    [CTS_JiraSvcMgmt].[dbo].jiraissue j ON ji.Issue_ID = j.ID -- Joining with jiraissue table
LEFT JOIN
    (
        SELECT
            cfv.ISSUE,
            vf.NAME
        FROM
            [CTS_JiraSvcMgmt].[dbo].[customfieldvalue] cfv
        JOIN
            [CTS_JiraSvcMgmt].[dbo].AO_54307E_VIEWPORTFORM vf
        ON
            LTRIM(RTRIM(REPLACE(cfv.STRINGVALUE, 'hrds/', ''))) = vf.[KEY]
        WHERE
            cfv.CUSTOMFIELD = 10001
    ) AS vf
ON
    ji.Issue_ID = vf.ISSUE
LEFT JOIN
    [CTS_JiraSvcMgmt].[dbo].[priority] pr
ON
    ji.Issue_Priority = pr.id; -- Assuming ji.Issue_Priority holds the priority ID
GO





