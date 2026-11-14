from sqlalchemy import text

from w1_lab.db import engine

with engine.begin() as conn:
    conn.execute(text("DELETE FROM log_entries")) #执行 DELETE FROM log_entries，清空整张表（保留表结构）。
    #这是核心：一条 INSERT ... SELECT 语句，用 PostgreSQL 的 generate_series 一次性生成 10 万行插入。
    conn.execute(
        text(         
            """
            INSERT INTO log_entries(ip,ts,method,path,status,size,latency)
            SELECT '10.0.' || mod(i, 256) || '.' || mod(i, 200),
                    now() - (i || ' seconds')::interval,      
                    'GET',
                    '/api/' || i,
                    200,i,1.5       
            FROM generate_series(1,100000) AS i
            """
        )
    )

with engine.connect() as conn:
    #"SELECT count(*) FROM log_entries" 是一条原生 SQL 字符串，统计表里有多少行，在 Result 上调用 .scalar()，语义是：取结果集的第一行、第一列的那个值。.execute(语句) 把这条 SQL 发送到数据库执行。
    n=conn.execute(text("SELECT count(*) FROM log_entries")).scalar()
    #pg_total_relation_size('log_entries')：PostgreSQL 内置函数，返回该表占用的总字节数
    size=conn.execute(text("SELECT pg_size_pretty(pg_total_relation_size('log_entries'))")).scalar()
    print(f"行数: {n}  表大小: {size}")