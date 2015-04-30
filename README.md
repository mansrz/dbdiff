## dbdiff.py

Little script to make database schema comparisons.

It was the result of, repeatedly, having to deal with failed database migrations. Whether it be provoked by automatic migrations when using some framework (Django, web2py) or by manual modification.

It's intended to show you all the manual modifications needed to complete the migration.

### Usage

* As a command line tool:

```shell
$ dbdiff.py "dbname='db1' user='username'" "host='10.0.0.5' dbname='db1' user='username'"
```

* As a module:

```python
from dbdiff import calc_diff, schema_to_dict
_, _, cols_to_change, _ = calc_diff(
    schema_to_dict(psycopg2.connect(database="db1", user="username")),
    schema_to_dict(psycopg2.connect(database="db2", user="username")),
)
```

The steps to solve this kind of problems is:

1. Get a copy your current database schema with data.
2. Create a database with the desired schema. No need for data here.
3. Run dbdiff.py against your current and desired schema to see the differences.
4. Get a beer or a coffee and do CREATE, DROP, ALTER, UPDATE and INSERT all around your current schema.
5. Repeat 3. and 4. until dbdiff.py doen't show any difference.

**TODO**

* Add support for MySQL/MariaDB. Currently only supports PostgreSQL.
* Generate the DDLs (CREATE, DROP, ALTER) to eliminate the differences.
