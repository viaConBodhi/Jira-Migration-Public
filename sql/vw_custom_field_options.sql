USE [jira]
GO

/****** Object:  View [dbo].[vw_custom_field_options]    Script Date: 2/16/2024 10:02:54 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO





-- Create the view
-- =============================================
-- Author: 
-- Create date: 01/18/2024
-- Description: View that gets the options for the custom fields and their data to assist with the migration
-- =============================================
CREATE VIEW [dbo].[vw_custom_field_options] AS

SELECT *
FROM 
	[CTS_JiraSvcMgmt].[dbo].customfieldoption


GO


