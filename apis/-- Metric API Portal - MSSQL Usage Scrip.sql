-- Metric API Portal - MSSQL Usage Script
-- Generated for 'api_portal_prod' database
-- NOTE: This script approximates the Django model definitions in T-SQL.
--       It is intended for manual preparation. 
--       The recommended way to sync is 'python manage.py migrate' with mssql-django installed.

USE api_portal_prod;
GO

-- 1. Departments
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_department]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_department] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [name] NVARCHAR(100) NOT NULL UNIQUE,
        [description] NVARCHAR(MAX) NOT NULL DEFAULT ''
    );
END
GO

-- 2. Categories
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_category]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_category] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [name] NVARCHAR(100) NOT NULL UNIQUE,
        [description] NVARCHAR(MAX) NOT NULL DEFAULT ''
    );
END
GO

-- 3. Users (Custom User Model)
-- Includes standard Django AbstractUser fields + Custom fields
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_user]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_user] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [password] NVARCHAR(128) NOT NULL,
        [last_login] DATETIME2 NULL,
        [is_superuser] BIT NOT NULL DEFAULT 0,
        [username] NVARCHAR(150) NOT NULL UNIQUE,
        [first_name] NVARCHAR(150) NOT NULL,
        [last_name] NVARCHAR(150) NOT NULL,
        [email] NVARCHAR(254) NOT NULL,
        [is_staff] BIT NOT NULL DEFAULT 0,
        [is_active] BIT NOT NULL DEFAULT 1,
        [date_joined] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        -- Custom Fields
        [role] NVARCHAR(20) NOT NULL DEFAULT 'DEVELOPER',
        [department_id] INT NULL,
        [profile_picture] NVARCHAR(100) NULL,
        [environment_access] NVARCHAR(MAX) NOT NULL DEFAULT '[]', -- JSON
        [must_reset_password] BIT NOT NULL DEFAULT 0,
        [last_password_change] DATETIME2 NULL,
        [is_sso_user] BIT NOT NULL DEFAULT 0,
        [sso_pending_approval] BIT NOT NULL DEFAULT 0,
        [manager] NVARCHAR(255) NOT NULL DEFAULT '',
        [office_location] NVARCHAR(255) NOT NULL DEFAULT '',
        [office_phone] NVARCHAR(50) NOT NULL DEFAULT '',
        [mobile_phone] NVARCHAR(50) NOT NULL DEFAULT '',
        [office_address] NVARCHAR(500) NOT NULL DEFAULT '',
        [timezone] NVARCHAR(100) NOT NULL DEFAULT '',
        
        CONSTRAINT [FK_core_user_department] FOREIGN KEY ([department_id]) REFERENCES [dbo].[core_department] ([id])
    );
END
GO

-- 4. Applications
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_application]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_application] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [name] NVARCHAR(255) NOT NULL,
        [description] NVARCHAR(MAX) NOT NULL DEFAULT '',
        [owner_id] INT NOT NULL,
        [environment] NVARCHAR(20) NOT NULL DEFAULT 'dev',
        [endpoints] NVARCHAR(MAX) NOT NULL DEFAULT '',
        [auth_type] NVARCHAR(20) NOT NULL DEFAULT 'NONE',
        [auth_config] NVARCHAR(MAX) NOT NULL DEFAULT '{}', -- JSON
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_application_owner] FOREIGN KEY ([owner_id]) REFERENCES [dbo].[core_user] ([id])
    );
END
GO

-- 5. Application Users (Many-to-Many)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_application_users]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_application_users] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [application_id] INT NOT NULL,
        [user_id] INT NOT NULL,
        
        CONSTRAINT [FK_core_app_users_app] FOREIGN KEY ([application_id]) REFERENCES [dbo].[core_application] ([id]),
        CONSTRAINT [FK_core_app_users_user] FOREIGN KEY ([user_id]) REFERENCES [dbo].[core_user] ([id]),
        CONSTRAINT [UQ_core_app_users] UNIQUE ([application_id], [user_id])
    );
END
GO

-- 6. Environment Variables
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_environmentvariable]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_environmentvariable] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [application_id] INT NULL,
        [key] NVARCHAR(255) NOT NULL,
        [value] NVARCHAR(MAX) NOT NULL,
        [is_sensitive] BIT NOT NULL DEFAULT 0,
        [description] NVARCHAR(MAX) NOT NULL DEFAULT '',
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_env_var_app] FOREIGN KEY ([application_id]) REFERENCES [dbo].[core_application] ([id]),
        CONSTRAINT [UQ_core_env_var_key] UNIQUE ([application_id], [key]) -- Note: Logic implies unique per app
    );
END
GO

-- 7. APIs
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_api]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_api] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [title] NVARCHAR(200) NOT NULL,
        [description] NVARCHAR(MAX) NOT NULL,
        [version] NVARCHAR(50) NOT NULL,
        [version_group_id] UNIQUEIDENTIFIER NOT NULL, -- UUID
        [status] NVARCHAR(20) NOT NULL DEFAULT 'production',
        [category] NVARCHAR(100) NOT NULL DEFAULT 'Other',
        [endpoint_url] NVARCHAR(500) NOT NULL,
        [headers] NVARCHAR(MAX) NOT NULL DEFAULT '[]', -- JSON
        [documentation] NVARCHAR(MAX) NOT NULL,
        [json_spec] NVARCHAR(MAX) NOT NULL DEFAULT '{}', -- JSON
        [is_public] BIT NOT NULL DEFAULT 0,
        [rate_limit_per_hour] INT NOT NULL DEFAULT 1000,
        [rate_limit_per_day] INT NOT NULL DEFAULT 10000,
        [application_id] INT NULL,
        [use_parent_auth] BIT NOT NULL DEFAULT 1,
        [authentication_type] NVARCHAR(20) NULL,
        [auth_config] NVARCHAR(MAX) NOT NULL DEFAULT '{}', -- JSON
        [gateway_id] NVARCHAR(255) NULL,
        [source] NVARCHAR(20) NOT NULL DEFAULT 'PORTAL',
        [gateway_details] NVARCHAR(MAX) NOT NULL DEFAULT '{}', -- JSON
        [sync_status] NVARCHAR(20) NOT NULL DEFAULT 'NOT_SYNCED',
        [last_synced] DATETIME2 NULL,
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_api_application] FOREIGN KEY ([application_id]) REFERENCES [dbo].[core_application] ([id])
    );
END
GO

-- 8. API Allowed Departments (Many-to-Many)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_api_allowed_departments]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_api_allowed_departments] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [api_id] INT NOT NULL,
        [department_id] INT NOT NULL,
        
        CONSTRAINT [FK_core_api_dept_api] FOREIGN KEY ([api_id]) REFERENCES [dbo].[core_api] ([id]),
        CONSTRAINT [FK_core_api_dept_dept] FOREIGN KEY ([department_id]) REFERENCES [dbo].[core_department] ([id]),
        CONSTRAINT [UQ_core_api_dept] UNIQUE ([api_id], [department_id])
    );
END
GO

-- 9. Azure Gateway Config
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_azuregatewayconfig]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_azuregatewayconfig] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [enabled] BIT NOT NULL DEFAULT 0,
        [tenant_id] NVARCHAR(255) NOT NULL DEFAULT '',
        [subscription_id] NVARCHAR(255) NOT NULL DEFAULT '',
        [resource_group] NVARCHAR(255) NOT NULL DEFAULT '',
        [service_name] NVARCHAR(255) NOT NULL DEFAULT '',
        [client_id] NVARCHAR(255) NOT NULL DEFAULT '',
        [client_secret] NVARCHAR(255) NOT NULL DEFAULT '',
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_by_id] INT NULL,
        
        CONSTRAINT [FK_core_gateway_config_user] FOREIGN KEY ([updated_by_id]) REFERENCES [dbo].[core_user] ([id])
    );
END
GO

-- 10. Analytics Logs
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_analyticslog]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_analyticslog] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [api_id] INT NULL,
        [application_id] INT NULL,
        [user_id] INT NULL,
        [endpoint] NVARCHAR(500) NOT NULL,
        [method] NVARCHAR(10) NOT NULL,
        [status_code] INT NOT NULL,
        [response_time_ms] INT NOT NULL,
        [response_data] NVARCHAR(MAX) NULL, -- JSON
        [timestamp] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_analytics_api] FOREIGN KEY ([api_id]) REFERENCES [dbo].[core_api] ([id]),
        CONSTRAINT [FK_core_analytics_app] FOREIGN KEY ([application_id]) REFERENCES [dbo].[core_application] ([id]),
        CONSTRAINT [FK_core_analytics_user] FOREIGN KEY ([user_id]) REFERENCES [dbo].[core_user] ([id])
    );
    CREATE INDEX [IX_core_analytics_timestamp] ON [dbo].[core_analyticslog] ([timestamp]);
END
GO

-- 11. GitHub Integration
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_githubintegration]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_githubintegration] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [user_id] INT NOT NULL UNIQUE,
        [access_token] NVARCHAR(MAX) NOT NULL,
        [repository] NVARCHAR(255) NOT NULL DEFAULT '',
        [branch] NVARCHAR(255) NOT NULL DEFAULT 'main',
        [last_synced] DATETIME2 NULL,
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_github_user] FOREIGN KEY ([user_id]) REFERENCES [dbo].[core_user] ([id])
    );
END
GO

-- 12. API Example Payloads
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_apiexamplepayload]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_apiexamplepayload] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [api_id] INT NOT NULL,
        [method] NVARCHAR(10) NOT NULL,
        [endpoint] NVARCHAR(500) NOT NULL DEFAULT '/',
        [payload] NVARCHAR(MAX) NOT NULL, -- JSON
        [description] NVARCHAR(255) NOT NULL DEFAULT '',
        [response_code] INT NOT NULL DEFAULT 200,
        [latency_ms] INT NOT NULL DEFAULT 0,
        [content_type] NVARCHAR(100) NOT NULL DEFAULT 'application/json',
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_example_api] FOREIGN KEY ([api_id]) REFERENCES [dbo].[core_api] ([id]),
        CONSTRAINT [UQ_core_example_payload] UNIQUE ([api_id], [method], [endpoint])
    );
END
GO

-- 13. Saved Test Configs
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_savedtestconfig]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_savedtestconfig] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [api_id] INT NOT NULL,
        [user_id] INT NOT NULL,
        [name] NVARCHAR(255) NOT NULL,
        [description] NVARCHAR(MAX) NOT NULL DEFAULT '',
        [method] NVARCHAR(10) NOT NULL DEFAULT 'GET',
        [url] NVARCHAR(2048) NOT NULL DEFAULT '',
        [url_params] NVARCHAR(MAX) NOT NULL DEFAULT '[]', -- JSON
        [headers] NVARCHAR(MAX) NOT NULL DEFAULT '[]', -- JSON
        [body] NVARCHAR(MAX) NOT NULL DEFAULT '',
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_savedtest_api] FOREIGN KEY ([api_id]) REFERENCES [dbo].[core_api] ([id]),
        CONSTRAINT [FK_core_savedtest_user] FOREIGN KEY ([user_id]) REFERENCES [dbo].[core_user] ([id]),
        CONSTRAINT [UQ_core_savedtest_name] UNIQUE ([api_id], [user_id], [name])
    );
END
GO

-- 14. SAML Config
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_samlconfig]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_samlconfig] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [enabled] BIT NOT NULL DEFAULT 0,
        [entity_id] NVARCHAR(500) NOT NULL,
        [idp_entity_id] NVARCHAR(500) NOT NULL,
        [idp_sso_url] NVARCHAR(200) NOT NULL,
        [idp_slo_url] NVARCHAR(200) NOT NULL DEFAULT '',
        [idp_x509_cert] NVARCHAR(MAX) NOT NULL,
        [attr_username] NVARCHAR(100) NOT NULL DEFAULT 'uid',
        [attr_email] NVARCHAR(100) NOT NULL DEFAULT 'email',
        [attr_first_name] NVARCHAR(100) NOT NULL DEFAULT 'givenName',
        [attr_last_name] NVARCHAR(100) NOT NULL DEFAULT 'sn',
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_by_id] INT NULL,
        
        CONSTRAINT [FK_core_saml_user] FOREIGN KEY ([updated_by_id]) REFERENCES [dbo].[core_user] ([id])
    );
END
GO

-- 15. API Feedback
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_apifeedback]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_apifeedback] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [api_id] INT NOT NULL,
        [user_id] INT NOT NULL,
        [category] NVARCHAR(20) NOT NULL DEFAULT 'QUESTION',
        [status] NVARCHAR(20) NOT NULL DEFAULT 'OPEN',
        [title] NVARCHAR(255) NOT NULL DEFAULT '',
        [message] NVARCHAR(MAX) NOT NULL,
        [parent_id] INT NULL,
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_feedback_api] FOREIGN KEY ([api_id]) REFERENCES [dbo].[core_api] ([id]),
        CONSTRAINT [FK_core_feedback_user] FOREIGN KEY ([user_id]) REFERENCES [dbo].[core_user] ([id]),
        CONSTRAINT [FK_core_feedback_parent] FOREIGN KEY ([parent_id]) REFERENCES [dbo].[core_apifeedback] ([id])
    );
END
GO

-- 16. API API Requests (New Feature)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_apirequest]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_apirequest] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [submitter_id] INT NOT NULL,
        [status] NVARCHAR(20) NOT NULL DEFAULT 'PENDING',
        
        -- API Details
        [api_name] NVARCHAR(255) NOT NULL,
        [source_system_name] NVARCHAR(255) NOT NULL,
        [available_in_azure] NVARCHAR(20) NOT NULL,
        [system_type] NVARCHAR(50) NOT NULL,
        [target_environment] NVARCHAR(MAX) NOT NULL DEFAULT '[]', -- JSON
        [purpose] NVARCHAR(MAX) NOT NULL,
        
        -- Security
        [consumer_app_name] NVARCHAR(255) NOT NULL,
        [auth_method] NVARCHAR(50) NOT NULL,
        [auth_method_other] NVARCHAR(255) NULL,
        [is_internal_external] NVARCHAR(50) NOT NULL,
        [expected_volume] NVARCHAR(50) NOT NULL,
        
        -- Rate Limits
        [rate_limit_min] NVARCHAR(100) NULL,
        [burst_limit_sec] NVARCHAR(100) NULL,
        
        -- Additional
        [specific_endpoints] NVARCHAR(MAX) NOT NULL,
        [data_sensitivity] NVARCHAR(50) NOT NULL,
        [other_notes] NVARCHAR(MAX) NOT NULL DEFAULT '',
        [attachment] NVARCHAR(100) NULL, -- FilePath
        
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_request_submitter] FOREIGN KEY ([submitter_id]) REFERENCES [dbo].[core_user] ([id])
    );
END
GO

-- 17. Notifications
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_notification]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_notification] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [recipient_id] INT NOT NULL,
        [message] NVARCHAR(MAX) NOT NULL,
        [related_request_id] INT NULL,
        [is_read] BIT NOT NULL DEFAULT 0,
        [created_at] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_notify_recipient] FOREIGN KEY ([recipient_id]) REFERENCES [dbo].[core_user] ([id]),
        CONSTRAINT [FK_core_notify_request] FOREIGN KEY ([related_request_id]) REFERENCES [dbo].[core_apirequest] ([id])
    );
END
GO

-- 18. Audit Logs
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[core_auditlog]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[core_auditlog] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [actor_id] INT NULL,
        [action] NVARCHAR(20) NOT NULL,
        [resource_type] NVARCHAR(100) NOT NULL,
        [resource_id] NVARCHAR(255) NOT NULL DEFAULT '',
        [details] NVARCHAR(MAX) NOT NULL DEFAULT '{}', -- JSON
        [ip_address] NVARCHAR(39) NULL, -- Supports IPv6
        [timestamp] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        
        CONSTRAINT [FK_core_audit_actor] FOREIGN KEY ([actor_id]) REFERENCES [dbo].[core_user] ([id])
    );
    CREATE INDEX [IX_core_audit_timestamp] ON [dbo].[core_auditlog] ([timestamp]);
END
GO

PRINT 'MSSQL Table Creation Script Completed Successfully';
