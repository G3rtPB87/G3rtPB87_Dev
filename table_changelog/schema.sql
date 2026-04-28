-- =============================================================
-- Table Change Log System — Schema + Trigger
-- SQL Server (Express / Azure SQL)
-- =============================================================

-- 1. Primary table -------------------------------------------
IF OBJECT_ID('dbo.Inventory', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Inventory (
        InventoryID   INT           IDENTITY(1,1) PRIMARY KEY,
        SKU           VARCHAR(50)   NOT NULL UNIQUE,
        ProductName   NVARCHAR(200) NOT NULL,
        Category      NVARCHAR(100) NULL,
        Quantity      INT           NOT NULL DEFAULT 0,
        UnitPrice     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        Location      NVARCHAR(100) NULL,
        IsActive      BIT           NOT NULL DEFAULT 1,
        CreatedAt     DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        UpdatedAt     DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

-- 2. Audit / shadow table ------------------------------------
IF OBJECT_ID('dbo.Inventory_AuditLog', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Inventory_AuditLog (
        AuditID       BIGINT        IDENTITY(1,1) PRIMARY KEY,
        Operation     VARCHAR(10)   NOT NULL,          -- INSERT | UPDATE | DELETE
        ChangedAt     DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        ChangedBy     NVARCHAR(256) NOT NULL,          -- DB login / app user
        RecordID      INT           NULL,              -- Inventory.InventoryID affected
        BeforeData    NVARCHAR(MAX) NULL,              -- JSON snapshot before change
        AfterData     NVARCHAR(MAX) NULL               -- JSON snapshot after change
    );

    -- Index for fast querying by record and time
    CREATE NONCLUSTERED INDEX IX_AuditLog_RecordID
        ON dbo.Inventory_AuditLog (RecordID, ChangedAt DESC);
END;
GO

-- 3. Trigger -------------------------------------------------
-- Handles INSERT, UPDATE, and DELETE in a single trigger.
-- Uses the virtual INSERTED / DELETED tables and FOR JSON PATH
-- to capture full row snapshots.

CREATE OR ALTER TRIGGER dbo.trg_Inventory_Audit
ON dbo.Inventory
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @operation VARCHAR(10);

    -- Determine operation type from virtual tables
    IF EXISTS (SELECT 1 FROM INSERTED) AND EXISTS (SELECT 1 FROM DELETED)
        SET @operation = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM INSERTED)
        SET @operation = 'INSERT';
    ELSE
        SET @operation = 'DELETE';

    -- For INSERT: no BeforeData, AfterData = inserted row(s)
    -- For UPDATE: BeforeData = deleted row(s), AfterData = inserted row(s)
    -- For DELETE: BeforeData = deleted row(s), no AfterData

    INSERT INTO dbo.Inventory_AuditLog
        (Operation, ChangedAt, ChangedBy, RecordID, BeforeData, AfterData)
    SELECT
        @operation,
        SYSUTCDATETIME(),
        SYSTEM_USER,
        COALESCE(i.InventoryID, d.InventoryID),
        -- BeforeData: serialize the DELETED (old) row as JSON
        (
            SELECT
                d2.InventoryID,
                d2.SKU,
                d2.ProductName,
                d2.Category,
                d2.Quantity,
                d2.UnitPrice,
                d2.Location,
                d2.IsActive,
                d2.CreatedAt,
                d2.UpdatedAt
            FROM DELETED d2
            WHERE d2.InventoryID = COALESCE(i.InventoryID, d.InventoryID)
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        ),
        -- AfterData: serialize the INSERTED (new) row as JSON
        (
            SELECT
                i2.InventoryID,
                i2.SKU,
                i2.ProductName,
                i2.Category,
                i2.Quantity,
                i2.UnitPrice,
                i2.Location,
                i2.IsActive,
                i2.CreatedAt,
                i2.UpdatedAt
            FROM INSERTED i2
            WHERE i2.InventoryID = COALESCE(i.InventoryID, d.InventoryID)
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        )
    FROM
        (SELECT InventoryID FROM INSERTED
         UNION
         SELECT InventoryID FROM DELETED) AS combined(InventoryID)
    LEFT JOIN INSERTED i ON i.InventoryID = combined.InventoryID
    LEFT JOIN DELETED  d ON d.InventoryID = combined.InventoryID;

END;
GO
