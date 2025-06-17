from core.database import get_admin_engine
from sqlalchemy import text
from sqlmodel import Session

def check_rls_policies():
    """Check current RLS policies and table configurations"""
    with Session(get_admin_engine()) as session:
        # Check if RLS policies exist and are enabled
        result = session.execute(text("""
            SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
            FROM pg_policies 
            WHERE schemaname = 'public'
            ORDER BY tablename, policyname;
        """))
        
        policies = result.fetchall()
        print('Current RLS Policies:')
        for policy in policies:
            print(f'  Table: {policy[1]}, Policy: {policy[2]}, Command: {policy[5]}, Condition: {policy[6]}')
        
        if not policies:
            print('No RLS policies found!')
        
        # Check if RLS is enabled on tables (using pg_class instead of pg_tables)
        result = session.execute(text("""
            SELECT n.nspname as schemaname, c.relname as tablename, c.relrowsecurity, c.relforcerowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r' AND (c.relrowsecurity = true OR c.relforcerowsecurity = true)
            ORDER BY c.relname;
        """))
        
        rls_tables = result.fetchall()
        print('\nTables with RLS enabled:')
        for table in rls_tables:
            print(f'  {table[1]}: rowsecurity={table[2]}, forcerowsecurity={table[3]}')
        
        if not rls_tables:
            print('No tables have RLS enabled!')
        
        # Test the session variable setting
        print('\nTesting session variable:')
        session.execute(text("SET LOCAL multi_tenancy.current_company_id = '1'"))
        result = session.execute(text("SELECT current_setting('multi_tenancy.current_company_id', true)"))
        print(f'Session variable value: {result.scalar()}')

if __name__ == "__main__":
    check_rls_policies() 