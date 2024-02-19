USE [jira]
GO

/****** Object:  View [dbo].[vw_jira_comments]    Script Date: 2/16/2024 10:06:44 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO




-- Create the view
-- =============================================
-- Author: 
-- Create date: 01/08/2024
-- Description: View that gets all Jira comments to assist with the migration
-- =============================================
CREATE VIEW [dbo].[vw_jira_comments] AS

SELECT
    project.pkey,
    jiraissue.issuenum,
    jiraissue.summary,
    jiraaction.actionbody AS 'comment_text',
	jiraaction.UPDATED AS 'comment_updated',
	jiraaction.ID as 'unique_comment_id',
    ep.json_value AS entity_property_json,
    jiraissue_ticket.Issue_Ticket_Number,
	jiraissue_ticket.Parent_Issue_ID,
	jiraissue_ticket.Issue_ID,
	jiraissue_ticket.Project_Key + '-' + CAST(jiraissue_ticket.Issue_Ticket_Number AS VARCHAR) AS Ticket_Key,
	app_user.lower_user_name AS 'commenter_name'
FROM
    [CTS_JiraSvcMgmt].[dbo].jiraaction
INNER JOIN
    [CTS_JiraSvcMgmt].[dbo].jiraissue ON jiraaction.issueid = jiraissue.id
INNER JOIN
    [CTS_JiraSvcMgmt].[dbo].project ON project.id = jiraissue.project
LEFT JOIN
    [CTS_JiraSvcMgmt].[dbo].entity_property ep ON jiraaction.id = ep.entity_id
    AND ep.entity_name = 'sd.comment.property'
INNER JOIN
    [CTS_JiraSvcMgmt].[cic].[vw_jira_issue] jiraissue_ticket ON jiraissue.id = jiraissue_ticket.Issue_ID
LEFT JOIN
    [CTS_JiraSvcMgmt].[dbo].[app_user] app_user ON jiraaction.UPDATEAUTHOR = app_user.user_key
WHERE
    jiraaction.id NOT IN (
        SELECT
            entity_id
        FROM
            [CTS_JiraSvcMgmt].[dbo].entity_property
        WHERE
            jiraaction.id = entity_id
            AND entity_name = 'sd.comment.property'
            AND (CAST(json_value AS NVARCHAR(MAX)) = '{"internal:true"}')
    );

GO


