USE [jira]
GO

/****** Object:  View [dbo].[vw_all_jira_attachments_details]    Script Date: 2/16/2024 9:39:52 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO




-- Create the view
-- =============================================
-- Author:		
-- Create date: 01/08/2024
-- Description:	View to assist with migrating jira attachments 
-- =============================================
CREATE VIEW [dbo].[vw_all_jira_attachments_details] AS
SELECT
    fa.*,
    bi.Project_Key + '-' + CAST(bi.Issue_Ticket_Number AS VARCHAR) AS Ticket_Key,
	bi.Project_Key,
	bi.Reporter_User_Display_Name,
	bi.Assignee_User_Display_Name
FROM
    [CTS_JiraSvcMgmt].[dbo].[fileattachment] fa
JOIN
    [CTS_JiraSvcMgmt].[cic].[vw_jira_issue] bi ON fa.issueid = bi.Issue_ID
GO


