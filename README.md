# Wikipedia Category Hierarchy

To make category hierarchy, using wikipedia dump files and mysql.

You can do it if using MediaWiki API, but if using this method, you can expect faster performance time.

## Download Wikipedia dump files

You can download wikidepdia dump files in https://dumps.wikimedia.org/enwiki/latest/. This is for the latest version and you can also download previous version.

To use this code, you should download "enwiki-latest-categorylinks.sql" and "enwiki-latest-page.sql". Both files are big size.

You can get each table's information in https://www.mediawiki.org/wiki/Manual:Categorylinks_table and https://www.mediawiki.org/wiki/Manual:Page_table.

## Loading sql file to mysql

You must download mysql and perform initial setup. Since both files have lots of insert query, It takes a lot of time.

`mysql -u <db_id> -p <db_password>`

`source enwiki-latest-categorylinks.sql`

`source enwiki-latest-page.sql`

## Implementation

`python categorytree.py --db_id <your db_id> --db_password <your db_password> --mode <a, u, l> --depth 5(default)`

When mode is 'a', you can get upper and lower hierarchy. 'u' is only upper and 'l' is only lower.

