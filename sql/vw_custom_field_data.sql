USE [jira]
GO

/****** Object:  View [dbo].[vw_custom_field_data]    Script Date: 2/16/2024 9:58:40 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO




-- Create the view
-- =============================================
-- Author: 
-- Create date: 01/18/2024
-- Description: View that gets the custom fields and their data to assist with the migration
-- =============================================
CREATE VIEW [dbo].[vw_custom_field_data] AS

SELECT
	cfv.ID as 'custom_field_value_record_id',
	cfv.ISSUE,
	cfv.CUSTOMFIELD,
	cfv.UPDATED,
	cfv.PARENTKEY,
	cfv.STRINGVALUE,
	cfv.NUMBERVALUE,
	cfv.TEXTVALUE,
	cfv.DATEVALUE,
	cv.ID,
	cv.cfname,
	cv.DESCRIPTION
FROM 
	[CTS_JiraSvcMgmt].[dbo].customfieldvalue cfv
JOIN
	[CTS_JiraSvcMgmt].[dbo].customfield cv
ON
	cfv.CUSTOMFIELD = cv.ID

GO










