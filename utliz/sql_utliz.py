import pyodbc
import concurrent.futures
from sqlalchemy import Column, Integer, String, Enum as EnumColumn, Float, create_engine, text, Table, inspect, MetaData 
from sqlalchemy.orm import column_property, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pandas as pd



class SysInfoServices:
    '''
    This class creates a link with sql database to support getting and posting data

    Usage example:
    sys_info = SysInfoServices(server, database, username, password)
    tables = sys_info.GetTables()
    columns = sys_info.GetColumns()
    views = sys_info.GetViews()
    procedures = sys_info.GetProcedures()     


    '''


    def __init__(self, server, database, username, password):
        self.server = server
        self.database = database
        self.username = username
        self.password = password

    def _establish_db_connection(self):
        conn_str = f'DRIVER={{SQL Server}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}'
        return pyodbc.connect(conn_str)

    def get_tables(self):
        TABLE_SQL = '''
        select 
            st.object_id as TableId,
            st.[Schema] as [Schema],
            st.name as [Name],
            IsView
        from (
            select [object_id], s.[name] [Schema],t.[name], 0 as IsView from sys.tables t
            inner join sys.schemas s on t.schema_id = s.schema_id
            where s.[name] = 'dbo'
            union 
            select [object_id], s.[name] [Schema], v.[name], 1 as IsView from sys.views v
            inner join sys.schemas s on v.schema_id = s.schema_id
            where s.[name] = 'dbo'
        ) st
        '''

        try:
            with self._establish_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(TABLE_SQL)
                return cursor.fetchall()
        except Exception as ex:
            print(f"Error: {ex}")
            raise

    def get_columns(self):
        COLUMN_SQL = '''
        select 
            st.object_id as TableObjectId,
            sc.column_id as ColumnOrdinal,
            s.[name] as [Schema],
            sc.name as [Name],
            sc.is_nullable as IsNullable,
            sc.is_identity as IsIdentity,
            CASE typ.name
                WHEN 'nvarchar' THEN 'nvarchar('+ case when sc.max_length < 0 then 'max' else CAST((sc.max_length) as varchar) end +')'
                WHEN 'varchar' THEN 'varchar('+CAST(sc.max_length as varchar)+')'
                WHEN 'char' THEN 'char('+CAST(sc.max_length as varchar)+')'
                WHEN 'nchar' THEN 'nchar('+CAST((sc.max_length / 2) as varchar)+')'
                WHEN 'binary' THEN 'binary('+CAST(sc.max_length as varchar)+')'
                WHEN 'varbinary' THEN 'varbinary('+CAST(sc.max_length as varchar)+')'
                WHEN 'numeric' THEN 'numeric('+CAST(sc.precision as varchar)+(CASE WHEN sc.scale = 0 THEN '' ELSE ','+CAST(sc.scale as varchar) END) +')'
                WHEN 'decimal' THEN 'decimal('+CAST(sc.precision as varchar)+(CASE WHEN sc.scale = 0 THEN '' ELSE ','+CAST(sc.scale as varchar) END) +')'
                ELSE typ.name
                END DataType,
            fk.ForeignKey
        from (
            select [object_id], [schema_id], [name] from sys.tables
            union 
            select [object_id], [schema_id], [name] from sys.views
        ) st
        inner join sys.schemas s on st.[schema_id] = s.[schema_id]
        inner join sys.columns sc 
            on st.[object_id] = sc.[object_id]
        inner join sys.types typ 
            on typ.system_type_id = sc.system_type_id and typ.name <> 'sysname'
        outer apply(
            select 
                OBJECT_NAME(f.parent_object_id) + '.' + COL_NAME(fc.parent_object_id,fc.parent_column_id) as ForeignKey
            from sys.foreign_keys f 
            inner join sys.foreign_key_columns fc 
                on f.[object_id] = fc.constraint_object_id
            where f.parent_object_id = st.[object_id] and fc.parent_column_id = sc.column_id
        ) fk
        where s.[name] = 'dbo'
        '''

        try:
            with self._establish_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(COLUMN_SQL)
                return cursor.fetchall()
        except Exception as ex:
            print(f"Error: {ex}")
            raise

    def get_views(self):
        try:
            sql = f'''
                select  
                    s.name as [Schema],
                    v.name as [Procedure],
                    OBJECT_DEFINITION(v.object_id) as [Definition]
                from sys.views v, sys.schemas s
                where v.[schema_id] = s.[schema_id] and s.[name] = 'dbo'
            '''

            with self._establish_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                return cursor.fetchall()
        except Exception as ex:
            print(f"Error: {ex}")
            raise

    def get_procedures(self):
        SPROC_SQL = '''
        select distinct
            s.name as [Schema],
            o.name as [Procedure],
            m.definition as [Definition]
        from sys.sql_modules m
        inner join sys.objects o on m.object_id = o.object_id
        inner join sys.schemas s on o.schema_id = s.schema_id
        where type_desc = 'SQL_STORED_PROCEDURE' and s.name = 'dbo' and o.name like 'sp_lri_edw%'
        '''

        try:
            with self._establish_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(SPROC_SQL)
                return cursor.fetchall()
        except Exception as ex:
            print(f"Error: {ex}")
            raise

    def get_column_is_always_null(self, column):
        try:
            ALWAYS_NULL_SQL = f'''
                select 
                    case when not exists (select top 1 [{column.Name}] FROM [{column.Table.Name}] WHERE [{column.Name}] IS NOT NULL) then 1 
                    else 0 end
            '''

            with self._establish_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(ALWAYS_NULL_SQL)
                return cursor.fetchone()[0] == 1
        except Exception as ex:
            print(f"Error: {ex}")
            raise

    def get_table_is_empty(self, table):
        try:
            EMPTY_TABLE_SQL = f'''
                select 
                    case when not exists (select top 1 1 FROM [{table.Name}]) then 1 
                    else 0 end
            '''

            with self._establish_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(EMPTY_TABLE_SQL)
                return cursor.fetchone()[0] == 1
        except Exception as ex:
            print(f"Error: {ex}")
            raise





    def get_tables_and_columns(self):
        TABLES_COLUMNS_SQL = '''
            SELECT 
                t.[name] AS TableName,
                c.[name] AS ColumnName,
                'Table' AS ObjectType
            FROM sys.tables t
            INNER JOIN sys.columns c ON t.object_id = c.object_id
            WHERE t.schema_id = SCHEMA_ID('dbo')
            UNION ALL
            SELECT 
                v.[name] AS ViewName,
                c.[name] AS ColumnName,
                'View' AS ObjectType
            FROM sys.views v
            INNER JOIN sys.columns c ON v.object_id = c.object_id
            WHERE v.schema_id = SCHEMA_ID('dbo')
        '''

        try:
            with self._establish_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(TABLES_COLUMNS_SQL)
                results = cursor.fetchall()

                data = []
                for row in results:
                    table_or_view_name = row.TableName.lower()
                    column_name = row.ColumnName.lower()
                    object_type = row.ObjectType
                    data.append([table_or_view_name, column_name, object_type])

                # Create a DataFrame with appropriate column names
                df = pd.DataFrame(data, columns=['table_or_view_name', 'column_name', 'object_type'])
                return df

        except Exception as ex:
            print(f"Error: {ex}")
            raise


    def get_view_dependencies(self, view_name):
        try:
            sql = f'''
                SELECT referenced_entity_name
                FROM sys.sql_expression_dependencies
                WHERE referencing_id = OBJECT_ID('{view_name}')
            '''

            with self._establish_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                dependencies = [row.referenced_entity_name for row in cursor]

            return dependencies

        except Exception as ex:
            print(f"Error: {ex}")
            raise


    def get_table_or_view_data(self, table_name):
        try:
            # Establishing the database connection
            conn_str = f'DRIVER={{SQL Server}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}'
            conn = pyodbc.connect(conn_str)

            # SQL query to fetch the data
            query1 = f'SELECT * FROM {table_name}'

            # Executing the query and fetching the data
            data_df = pd.read_sql_query(query1, conn)

            # Closing the database connection
            conn.close()

            return data_df

        except Exception as ex:
            print(f"Error: {ex}")
            raise


    def get_primary_key_columns(self, table_name):
        try:
            PRIMARY_KEY_SQL = f'''
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_NAME), 'IsPrimaryKey') = 1
                AND TABLE_NAME = '{table_name}'
            '''

            with self._establish_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(PRIMARY_KEY_SQL)
                #primary_key_columns = [row.COLUMN_NAME for row in cursor] # commenting out cause we need it lowered
                primary_key_columns = [row.COLUMN_NAME.lower() for row in cursor]

            return primary_key_columns

        except Exception as ex:
            print(f"Error: {ex}")
            raise




    def update_sql_table_with_dataframe(self, df, table_name):
        # Connect to the database using SQLAlchemy
        engine = create_engine(f'mssql+pyodbc://{self.username}:{self.password}@{self.server}/{self.database}?driver=SQL Server')
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = metadata.tables.get(table_name)

        with engine.connect() as connection:
            if table is None:
                # Table does not exist, create it from the DataFrame
                df.to_sql(table_name, engine, if_exists='replace', index=False)
                print(f"Table '{table_name}' created.")
            else:
                # Table exists, compare the DataFrame columns with the table columns
                trans = connection.begin()
                try:
                    # Get the existing columns from the table
                    existing_columns = {column.name.lower() for column in table.columns}

                    # Find new columns in the DataFrame that are not in the table
                    new_columns = set(df.columns) - existing_columns

                    # Add any new columns to the table
                    for col in new_columns:
                        dtype = Integer if df[col].dtype == 'int64' else String
                        col_type = 'INT' if dtype == Integer else 'NVARCHAR(MAX)'
                        alter_stmt = f"ALTER TABLE {table_name} ADD {col} {col_type};"
                        connection.execute(alter_stmt)  # Execute the alter statement
                        print(f"Column '{col}' added to the table.")

                    # Remove all data from the current table and insert new data
                    connection.execute(table.delete())
                    df.to_sql(table_name, engine, if_exists='append', index=False)

                    trans.commit()
                    print(f"Table '{table_name}' updated.")
                except Exception as e:
                    trans.rollback()
                    raise e


