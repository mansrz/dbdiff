#!/usr/bin/env python2
import psycopg2

"""
Little script to make database schema comparisons

Currently only supports PostgreSQL.

Usage:

$ dbdiff.py "dbname='db1' user='username'" "dbname='db2' user='username'"

Can also be used as a module

>>> from dbdiff import calc_diff, schema_to_dict
>>> _, _, cols_to_change, _ = calc_diff(
>>>     schema_to_dict(psycopg2.connect(database="db1", user="username")),
>>>     schema_to_dict(psycopg2.connect(database="db1", user="username")),
>>> )
"""

def schema_to_dict(conn):
    """
    Return a db schema as a dict structured this way:
    {
      'table1': [('col1', 'typeA'), ('col2', 'typeB'), ..., ('colI', 'typeC')],
      'table2': [('col1', 'typeA'), ('col2', 'typeB'), ..., ('colJ', 'typeC')],
      ...
      'tableN': [('col1', 'typeA'), ('col2', 'typeB'), ..., ('colK', 'typeC')],
    }
    """
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_catalog.pg_tables "
                "WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'")

    tables = [r[0] for r in cur.fetchall()]

    # Empty database
    if not tables: return {}

    # Initialize the schema as a dict of empty lists
    schema = {}
    for t in tables:
        schema[t] = []

    cur.execute("SELECT table_name, column_name, data_type FROM information_schema.columns "
                "WHERE %s" % " or ".join(["table_name = '%s'" % t for t in tables]))

    # Add a 2-tuple containing column name and type to the match table
    for table_name, column_name, data_type in cur.fetchall():
        schema[table_name].append((column_name, data_type))

    return schema

def col_type(cols, col_name):
    """
    Look for a column in a schema-dict a return its type
    """
    for c in cols:
        if c[0] == col_name:
            return c[1]

    raise ValueError("Column '%s' not found in %s" % (col_name, cols))


def diff(a, b):
    """
    Compare two iterables, return a 3-tuple cointaing the elements to delete
    and to add in order to convert 'a' into 'b'. The 3rd tuple, are the common
    elements
    """

    return (
        [e for e in a if e not in b], # To delete
        [e for e in b if e not in a], # To add
        [e for e in a if e in b],     # Common
    )

def calc_diff(a, b, show=False):
    """
    Print the db differences and return a tuple with the list of tables to
    drop, the list of tables to create, the list of columns to change, and
    a list of unchanged tables
    """

    t_to_drop, t_to_create, t_to_compare = diff(a.keys(), b.keys())

    if show:
        print '[+] Tables to drop:', t_to_drop
        print '[+] Tables to create:', t_to_create

    unchanged_tables = []

    for table in t_to_compare:

        cols_a = [c[0] for c in a[table]] # Column names
        cols_b = [c[0] for c in b[table]] # Column names
        c_to_drop, c_to_create, c_to_compare = diff(cols_a, cols_b)

        c_to_change = []
        for col_name in c_to_compare:
            col_a_type = col_type(a[table], col_name)
            col_b_type = col_type(b[table], col_name)
            if  col_a_type != col_b_type:
                c_to_change.append((table, col_name, col_a_type, col_b_type))

        if c_to_drop or c_to_create or c_to_change:
            if show:
                print '[+] Table', table
                if c_to_drop:
                    print '- Columns to drop:', c_to_drop
                if c_to_create:
                    print '- Columns to create:', c_to_create
                if c_to_change:
                    print '- Columns to change:'
                    for c in c_to_change:
                        print '--- %s: %s -> %s' % c[1:]
        else:
            unchanged_tables.append(table)

    if show: print '[+] Unchanged tables:', unchanged_tables

    return (t_to_drop,
            t_to_create,
            c_to_change,
            unchanged_tables)

if __name__ == '__main__':
    import sys

    try:
        conn = psycopg2.connect(sys.argv[1]), psycopg2.connect(sys.argv[2])
    except:
        print "Can't connect to the database"
        raise

    a, b = schema_to_dict(conn[0]), schema_to_dict(conn[1])

    t_to_drop, t_to_create, c_to_change, unchanged_tables = calc_diff(a, b, show=True)
