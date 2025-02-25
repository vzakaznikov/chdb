###ChDB QUERIES###
sql_chdb=("""

SELECT
    L_RETURNFLAG,
    L_LINESTATUS,
    SUM(L_QUANTITY) AS sum_qty,
    SUM(L_EXTENDEDPRICE) AS sum_base_price,
    SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS sum_disc_price,
    SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT) * (1 + L_TAX)) AS sum_charge,
    AVG(L_QUANTITY) AS avg_qty,
    AVG(L_EXTENDEDPRICE) AS avg_price,
    AVG(L_DISCOUNT) AS avg_disc,
    COUNT(*) AS count_order
FROM
    file('lineitem.parquet')
WHERE
    l_shipdate <= date '1998-09-02'
GROUP BY
    L_RETURNFLAG,
    L_LINESTATUS
ORDER BY
    L_RETURNFLAG,
    L_LINESTATUS;

SELECT
    supplier.S_ACCTBAL,
    supplier.S_NAME,
    nation.N_NAME,
    part.P_PARTKEY,
    part.P_MFGR,
    supplier.S_ADDRESS,
    supplier.S_PHONE,
    supplier.S_COMMENT
FROM
    file('part.parquet') as part
    JOIN file('partsupp.parquet') as partsupp ON part.P_PARTKEY = partsupp.PS_PARTKEY
    JOIN file('supplier.parquet') as supplier ON supplier.S_SUPPKEY = partsupp.PS_SUPPKEY
    JOIN file('nation.parquet') as nation ON nation.N_NATIONKEY = supplier.S_NATIONKEY
    JOIN file('region.parquet') as region ON region.R_REGIONKEY = nation.N_REGIONKEY,
(
        SELECT
            MIN(partsupp0.PS_SUPPLYCOST) as cp_lowest,
            part0.P_PARTKEY as cp_partkey
        FROM
            file('partsupp.parquet') as partsupp0
            JOIN file('part.parquet') as part0 ON part0.P_PARTKEY = partsupp0.PS_PARTKEY
            JOIN file('supplier.parquet') as supplier0 ON supplier0.S_SUPPKEY = partsupp0.PS_SUPPKEY
            JOIN file('nation.parquet') as nation0 ON nation0.N_NATIONKEY = supplier0.S_NATIONKEY
            JOIN file('region.parquet') as region0 ON region0.R_REGIONKEY = nation0.N_REGIONKEY
        WHERE
            region0.R_NAME = 'EUROPE'
        GROUP BY
            cp_partkey
    ) as cheapest_part
WHERE
    part.P_SIZE = 15
    AND part.P_TYPE LIKE '%BRASS'
    AND region.R_NAME = 'EUROPE'
    AND partsupp.PS_SUPPLYCOST = cp_lowest
    AND part.P_PARTKEY = cp_partkey
ORDER BY
    supplier.S_ACCTBAL DESC,
    nation.N_NAME,
    supplier.S_NAME,
    part.P_PARTKEY
LIMIT
    100;

SELECT
    line.L_ORDERKEY,
    SUM(line.L_EXTENDEDPRICE * (1 - line.L_DISCOUNT)) AS revenue,
    ord.o_orderdate,
    ord.O_SHIPPRIORITY
FROM
    file('customer.parquet') as cust
    JOIN file('orders.parquet') as ord ON cust.C_CUSTKEY = ord.O_CUSTKEY
    JOIN file('lineitem.parquet') as line ON line.L_ORDERKEY = ord.O_ORDERKEY
WHERE
    cust.C_MKTSEGMENT = 'BUILDING'
    AND ord.o_orderdate < date '1995-03-15'
    AND line.l_shipdate > date '1995-03-15'
GROUP BY
    line.L_ORDERKEY,
    ord.o_orderdate,
    ord.O_SHIPPRIORITY
ORDER BY
    revenue DESC,
    ord.o_orderdate
LIMIT
    10;

SELECT
    O_ORDERPRIORITY,
    COUNT(*) AS order_count
FROM
    file('orders.parquet')
WHERE
    o_orderdate >= date '1993-07-01'
    AND o_orderdate < date '1993-10-01'
    AND O_ORDERKEY IN (
        SELECT
            line.L_ORDERKEY
        FROM
            file('lineitem.parquet') as line
        WHERE
            line.l_commitdate < line.l_receiptdate
    )
GROUP BY
    O_ORDERPRIORITY
ORDER BY
    O_ORDERPRIORITY;

SELECT
    nation.N_NAME,
    SUM(line.L_EXTENDEDPRICE * (1 - line.L_DISCOUNT)) AS revenue
FROM
    file('customer.parquet') as cus
    JOIN file('orders.parquet') as ord ON cus.C_CUSTKEY = ord.O_CUSTKEY
    JOIN file('lineitem.parquet') as line ON line.L_ORDERKEY = ord.O_ORDERKEY
    JOIN file('supplier.parquet') as supp ON line.L_SUPPKEY = supp.S_SUPPKEY
    JOIN file('nation.parquet') as nation ON supp.S_NATIONKEY = nation.N_NATIONKEY
    JOIN file('region.parquet') as region ON nation.N_REGIONKEY = region.R_REGIONKEY
WHERE
    cus.C_NATIONKEY = supp.S_NATIONKEY
    AND region.R_NAME = 'ASIA'
    AND ord.o_orderdate >= date '1994-01-01'
    AND ord.o_orderdate < date '1995-01-01'
GROUP BY
    nation.N_NAME
ORDER BY
    revenue DESC;

SELECT
    SUM(L_EXTENDEDPRICE * L_DISCOUNT) AS revenue
FROM
    file('lineitem.parquet')
WHERE
    l_shipdate >= date '1994-01-01'
    AND l_shipdate < date '1995-01-01'
    AND L_DISCOUNT BETWEEN toDecimal64(0.05, 2)
    AND toDecimal64(0.07, 2)
    AND L_QUANTITY < 24;

SELECT
    supp_nation,
    cust_nation,
    l_year,
    SUM(volume) AS revenue
FROM
    (
        SELECT
            n1.N_NAME AS supp_nation,
            n2.N_NAME AS cust_nation,
            EXTRACT(
                year
                FROM
                    line.l_shipdate
            ) AS l_year,
            line.L_EXTENDEDPRICE * (1 - line.L_DISCOUNT) AS volume
        FROM
            file('supplier.parquet') as supp
            JOIN file('lineitem.parquet') as line ON supp.S_SUPPKEY = line.L_SUPPKEY
            JOIN file('orders.parquet') as ord ON ord.O_ORDERKEY = line.L_ORDERKEY
            JOIN file('customer.parquet') as cus ON cus.C_CUSTKEY = ord.O_CUSTKEY
            JOIN file('nation.parquet') as n2 ON cus.C_NATIONKEY = n2.N_NATIONKEY
            JOIN file('nation.parquet') as n1 ON supp.S_NATIONKEY = n1.N_NATIONKEY
        WHERE
            (
                (
                    n1.N_NAME = 'FRANCE'
                    AND n2.N_NAME = 'GERMANY'
                )
                OR (
                    n1.N_NAME = 'GERMANY'
                    AND n2.N_NAME = 'FRANCE'
                )
            )
            AND line.l_shipdate BETWEEN date '1995-01-01'
            AND date '1996-12-31'
    ) AS shipping
GROUP BY
    supp_nation,
    cust_nation,
    l_year
ORDER BY
    supp_nation,
    cust_nation,
    l_year;

SELECT
    o_year,
    SUM(
        CASE
            WHEN nation = 'BRAZIL' THEN volume
            ELSE 0
        END
    ) / SUM(volume) AS mkt_share
FROM
    (
        SELECT
            EXTRACT(
                year
                FROM
                    ord.o_orderdate
            ) AS o_year,
            line.L_EXTENDEDPRICE * (1 - line.L_DISCOUNT) AS volume,
            n2.N_NAME AS nation
        FROM
            file('part.parquet') as part
            JOIN file('lineitem.parquet') as line ON part.P_PARTKEY = line.L_PARTKEY
            JOIN file('orders.parquet') as ord ON line.L_ORDERKEY = ord.O_ORDERKEY
            JOIN file('customer.parquet') as cus ON ord.O_CUSTKEY = cus.C_CUSTKEY
            JOIN file('nation.parquet') as n1 ON cus.C_NATIONKEY = n1.N_NATIONKEY
            JOIN file('region.parquet') as reg ON n1.N_REGIONKEY = reg.R_REGIONKEY
            JOIN file('supplier.parquet') as supp ON supp.S_SUPPKEY = line.L_SUPPKEY
            JOIN file('nation.parquet') as n2 ON supp.S_NATIONKEY = n2.N_NATIONKEY
        WHERE
            R_NAME = 'AMERICA'
            AND o_orderdate BETWEEN date '1995-01-01'
            AND date '1996-12-31'
            AND P_TYPE = 'ECONOMY ANODIZED STEEL'
    ) AS all_nations
GROUP BY
    o_year
ORDER BY
    o_year;

SELECT
    nation,
    o_year,
    SUM(amount) AS sum_profit
FROM
(
        SELECT
            nat.N_NAME AS nation,
            EXTRACT(
                year
                FROM
                    ord.o_orderdate
            ) AS o_year,
            line.L_EXTENDEDPRICE * (1 - line.L_DISCOUNT) - partsupp.PS_SUPPLYCOST * line.L_QUANTITY AS amount
        FROM
            file('partsupp.parquet') as partsupp
            JOIN file('lineitem.parquet') as line ON partsupp.PS_PARTKEY = line.L_PARTKEY
            AND partsupp.PS_SUPPKEY = line.L_SUPPKEY
            JOIN file('part.parquet') as part ON part.P_PARTKEY = line.L_PARTKEY
            JOIN file('supplier.parquet') as supp ON supp.S_SUPPKEY = line.L_SUPPKEY
            JOIN file('orders.parquet') as ord ON ord.O_ORDERKEY = line.L_ORDERKEY
            JOIN file('nation.parquet') as nat ON supp.S_NATIONKEY = nat.N_NATIONKEY
        WHERE
            part.P_NAME LIKE '%green%'
    ) AS profit
GROUP BY
    nation,
    o_year
ORDER BY
    nation,
    o_year DESC;

SELECT
    cus.C_CUSTKEY,
    cus.C_NAME,
    SUM(line.L_EXTENDEDPRICE * (1 - line.L_DISCOUNT)) AS revenue,
    cus.C_ACCTBAL,
    nat.N_NAME,
    cus.C_ADDRESS,
    cus.C_PHONE,
    cus.C_COMMENT
FROM
    file('lineitem.parquet') as line
    JOIN file('orders.parquet') as ord ON line.L_ORDERKEY = ord.O_ORDERKEY
    JOIN file('customer.parquet') as cus ON cus.C_CUSTKEY = ord.O_CUSTKEY
    JOIN file('nation.parquet') as nat ON cus.C_NATIONKEY = nat.N_NATIONKEY
WHERE
    ord.o_orderdate >= date '1993-10-01'
    AND ord.o_orderdate < date '1994-01-01'
    AND line.L_RETURNFLAG = 'R'
GROUP BY
    cus.C_CUSTKEY,
    cus.C_NAME,
    cus.C_ACCTBAL,
    cus.C_PHONE,
    nat.N_NAME,
    cus.C_ADDRESS,
    cus.C_COMMENT
ORDER BY
    revenue DESC
LIMIT
    20;

SELECT
    partsupp.PS_PARTKEY,
    SUM(partsupp.PS_SUPPLYCOST * partsupp.PS_AVAILQTY) AS value
FROM
    file('partsupp.parquet') as partsupp
    JOIN file('supplier.parquet') as supp ON partsupp.PS_SUPPKEY = supp.S_SUPPKEY
    JOIN file('nation.parquet') as nat ON supp.S_NATIONKEY = nat.N_NATIONKEY
WHERE
    nat.N_NAME = 'GERMANY'
GROUP BY
    partsupp.PS_PARTKEY
HAVING
    SUM(partsupp.PS_SUPPLYCOST * partsupp.PS_AVAILQTY) > (
        SELECT
            SUM(partsupp0.PS_SUPPLYCOST * partsupp0.PS_AVAILQTY) * (0.0001 / 10)
        FROM
            file('partsupp.parquet') as partsupp0
            JOIN file('supplier.parquet') as supp0 ON partsupp0.PS_SUPPKEY = supp0.S_SUPPKEY
            JOIN file('nation.parquet') as nat0 ON supp0.S_NATIONKEY = nat0.N_NATIONKEY
        WHERE
            nat0.N_NAME = 'GERMANY'
    )
ORDER BY
    value DESC;

SELECT
    line.L_SHIPMODE,
    SUM(
        CASE
            WHEN ord.O_ORDERPRIORITY = '1-URGENT'
            OR ord.O_ORDERPRIORITY = '2-HIGH' THEN 1
            ELSE 0
        END
    ) AS high_line_count,
    SUM(
        CASE
            WHEN ord.O_ORDERPRIORITY <> '1-URGENT'
            AND ord.O_ORDERPRIORITY <> '2-HIGH' THEN 1
            ELSE 0
        END
    ) AS low_line_count
FROM
    file('orders.parquet') as ord
    JOIN file('lineitem.parquet') as line ON ord.O_ORDERKEY = line.L_ORDERKEY
WHERE
    line.L_SHIPMODE IN ('MAIL', 'SHIP')
    AND line.l_commitdate < line.l_receiptdate
    AND line.l_shipdate < line.l_commitdate
    AND line.l_receiptdate >= date '1994-01-01'
    AND line.l_receiptdate < date '1995-01-01'
GROUP BY
    line.L_SHIPMODE
ORDER BY
    line.L_SHIPMODE;

SELECT
    c_count,
    COUNT(*) AS custdist
FROM
(
        SELECT
            cus.C_CUSTKEY,
            COUNT(ord.O_ORDERKEY) AS c_count
        FROM
            file('customer.parquet') as cus
            LEFT OUTER JOIN file('orders.parquet') as ord ON cus.C_CUSTKEY = ord.O_CUSTKEY
            AND ord.O_COMMENT NOT LIKE '%special%requests%'
        GROUP BY
            cus.C_CUSTKEY
    ) AS c_orders
GROUP BY
    c_count
ORDER BY
    custdist DESC,
    c_count DESC;

SELECT
    toDecimal64(100.00, 2) * SUM(
        CASE
            WHEN part.P_TYPE LIKE 'PROMO%' THEN line.L_EXTENDEDPRICE * (1 - line.L_DISCOUNT)
            ELSE 0
        END
    ) / SUM(line.L_EXTENDEDPRICE * (1 - line.L_DISCOUNT)) AS promo_revenue
FROM
    file('lineitem.parquet') as line
    JOIN file('part.parquet') as part ON line.L_PARTKEY = part.P_PARTKEY
WHERE
    line.l_shipdate >= date '1995-09-01'
    AND line.l_shipdate < date '1995-10-01';

SELECT
    supp.S_SUPPKEY,
    supp.S_NAME,
    supp.S_ADDRESS,
    supp.S_PHONE,
    revenue0.total_revenue
FROM
    file('supplier.parquet') as supp,
(
        SELECT
            line1.L_SUPPKEY AS supplier_no,
            SUM(line1.L_EXTENDEDPRICE * (1 - line1.L_DISCOUNT)) AS total_revenue
        FROM
            file('lineitem.parquet') as line1
        WHERE
            line1.l_shipdate >= date '1996-01-01'
            AND line1.l_shipdate < date '1996-04-01'
        GROUP BY
            supplier_no
    ) as revenue0
WHERE
    supp.S_SUPPKEY = revenue0.supplier_no
    AND revenue0.total_revenue = (
        SELECT
            MAX(revenue1.total_revenue)
        FROM
            (
                SELECT
                    line0.L_SUPPKEY AS supplier_no,
                    SUM(line0.L_EXTENDEDPRICE * (1 - line0.L_DISCOUNT)) AS total_revenue
                FROM
                    file('lineitem.parquet') as line0
                WHERE
                    line0.l_shipdate >= date '1996-01-01'
                    AND line0.l_shipdate < date '1996-04-01'
                GROUP BY
                    supplier_no
            ) as revenue1
    )
ORDER BY
    supp.S_SUPPKEY;

SELECT
    part.P_BRAND,
    part.P_TYPE,
    part.P_SIZE,
    COUNT(DISTINCT partsupp.PS_SUPPKEY) AS supplier_cnt
FROM
    file('partsupp.parquet') as partsupp
    JOIN file('part.parquet') as part ON part.P_PARTKEY = partsupp.PS_PARTKEY
WHERE
    part.P_BRAND <> 'Brand#45'
    AND part.P_TYPE NOT LIKE 'MEDIUM POLISHED%'
    AND part.P_SIZE IN (49, 14, 23, 45, 19, 3, 36, 9)
    AND partsupp.PS_SUPPKEY NOT IN (
        SELECT
            supp.S_SUPPKEY
        FROM
            file('supplier.parquet') as supp
        WHERE
            supp.S_COMMENT LIKE '%Customer%Complaints%'
    )
GROUP BY
    part.P_BRAND,
    part.P_TYPE,
    part.P_SIZE
ORDER BY
    supplier_cnt DESC,
    part.P_BRAND,
    part.P_TYPE,
    part.P_SIZE;

SELECT
    SUM(line.L_EXTENDEDPRICE) / toDecimal64(7.0, 2) AS avg_yearly
FROM
    file('lineitem.parquet') as line
    JOIN file('part.parquet') as part ON part.P_PARTKEY = line.L_PARTKEY,
(
        SELECT
            toDecimal64(0.2 * AVG(line0.L_QUANTITY), 12) as limit_qty,
            line0.L_PARTKEY as lpk
        FROM
            file('lineitem.parquet') as line0
        GROUP BY
            lpk
    ) as part_avg
WHERE
    part.P_BRAND = 'Brand#23'
    AND part.P_CONTAINER = 'MED BOX'
    AND part.P_PARTKEY = lpk
    AND line.L_QUANTITY < limit_qty;

SELECT
    cus.C_NAME,
    cus.C_CUSTKEY,
    ord.O_ORDERKEY,
    ord.o_orderdate,
    ord.O_TOTALPRICE,
    SUM(line.L_QUANTITY)
FROM
    file('customer.parquet') as cus
    JOIN file('orders.parquet') as ord ON cus.C_CUSTKEY = ord.O_CUSTKEY
    JOIN file('lineitem.parquet') as line ON ord.O_ORDERKEY = line.L_ORDERKEY
WHERE
    ord.O_ORDERKEY IN (
        SELECT
            line0.L_ORDERKEY
        FROM
            file('lineitem.parquet') as line0
        GROUP BY
            line0.L_ORDERKEY
        HAVING
            SUM(line0.L_QUANTITY) > 300
    )
GROUP BY
    cus.C_NAME,
    cus.C_CUSTKEY,
    ord.O_ORDERKEY,
    ord.o_orderdate,
    ord.O_TOTALPRICE
ORDER BY
    ord.O_TOTALPRICE DESC,
    ord.o_orderdate
LIMIT
    100;

SELECT
    SUM(line.L_EXTENDEDPRICE * (1 - line.L_DISCOUNT)) AS revenue
FROM
    file('lineitem.parquet') as line
    JOIN file('part.parquet') as part ON part.P_PARTKEY = line.L_PARTKEY
WHERE
    (
        part.P_BRAND = 'Brand#12'
        AND part.P_CONTAINER IN ('SM CASE', 'SM BOX', 'SM PACK', 'SM PKG')
        AND line.L_QUANTITY >= 1
        AND line.L_QUANTITY <= 1 + 10
        AND (
            part.P_SIZE BETWEEN 1
            AND 5
        )
        AND line.L_SHIPMODE IN ('AIR', 'AIR REG')
        AND line.L_SHIPINSTRUCT = 'DELIVER IN PERSON'
    )
    OR (
        part.P_PARTKEY = line.L_PARTKEY
        AND part.P_BRAND = 'Brand#23'
        AND part.P_CONTAINER IN ('MED BAG', 'MED BOX', 'MED PKG', 'MED PACK')
        AND line.L_QUANTITY >= 10
        AND line.L_QUANTITY <= 10 + 10
        AND (
            part.P_SIZE BETWEEN 1
            AND 10
        )
        AND line.L_SHIPMODE IN ('AIR', 'AIR REG')
        AND line.L_SHIPINSTRUCT = 'DELIVER IN PERSON'
    )
    OR (
        part.P_PARTKEY = line.L_PARTKEY
        AND part.P_BRAND = 'Brand#34'
        AND part.P_CONTAINER IN ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG')
        AND line.L_QUANTITY >= 20
        AND line.L_QUANTITY <= 20 + 10
        AND (
            part.P_SIZE BETWEEN 1
            AND 15
        )
        AND line.L_SHIPMODE IN ('AIR', 'AIR REG')
        AND line.L_SHIPINSTRUCT = 'DELIVER IN PERSON'
    );

SELECT
    supp.S_NAME,
    supp.S_ADDRESS
FROM
    file('supplier.parquet') as supp
    JOIN file('nation.parquet') as nat ON supp.S_NATIONKEY = nat.N_NATIONKEY
WHERE
    supp.S_SUPPKEY IN (
        SELECT
            partsupp1.PS_SUPPKEY
        FROM
            file('partsupp.parquet') as partsupp1,
(
                SELECT
                    0.5 * SUM(line0.L_QUANTITY) as ps_halfqty,
                    line0.L_PARTKEY as pkey,
                    line0.L_SUPPKEY as skey
                FROM
                    file('lineitem.parquet') as line0
                WHERE
                    line0.l_shipdate >= date '1994-01-01'
                    AND line0.l_shipdate < date '1995-01-01'
                group by
                    pkey,
                    skey
            ) as availability_part_supp
        WHERE
            partsupp1.PS_PARTKEY IN (
                SELECT
                    part0.P_PARTKEY
                FROM
                    file('part.parquet') as part0
                WHERE
                    part0.P_NAME LIKE 'forest%'
            )
            AND partsupp1.PS_AVAILQTY > availability_part_supp.ps_halfqty
            AND partsupp1.PS_SUPPKEY = availability_part_supp.skey
            AND partsupp1.PS_PARTKEY = availability_part_supp.pkey
    )
    AND nat.N_NAME = 'CANADA'
ORDER BY
    supp.S_NAME;

SELECT
    cntrycode,
    COUNT(*) AS numcust,
    SUM(c_acctbal) AS totacctbal
FROM
    (
        SELECT
            SUBSTRING(cus2.C_PHONE, 1, 2) AS cntrycode,
            cus2.C_ACCTBAL as c_acctbal
        FROM
            file('customer.parquet') as cus2
        WHERE
            SUBSTRING(cus2.C_PHONE, 1, 2) IN ('13', '31', '23', '29', '30', '18', '17')
            AND cus2.C_ACCTBAL > (
                SELECT
                    AVG(cus1.C_ACCTBAL)
                FROM
                    file('customer.parquet') as cus1
                WHERE
                    cus1.C_ACCTBAL > 0.00
                    AND SUBSTRING(cus1.C_PHONE, 1, 2) IN ('13', '31', '23', '29', '30', '18', '17')
            )
            AND cus2.C_CUSTKEY NOT IN (
                SELECT
                    ord.O_CUSTKEY
                FROM
                    file('orders.parquet') as ord
            )
    ) AS custsale
GROUP BY
    cntrycode
ORDER BY
    cntrycode;
    
""")

##python script##
#pip install chdb

import time
import chdb
import pandas as pd
import matplotlib.pyplot as plt

pd.set_option('display.max_columns', 20)

def execute_query(sql_script):
    import chdb
    #df = pd.DataFrame(columns=['dur'])
    sql_arr = sql_script.split(";")
    chdb_dict={}
    for index, value in enumerate(sql_arr,start=1):
        val=value.strip()
        if len(val) > 0:
          start = time.time()
          qnum='Q'+str(index)
          print(qnum)       
          try:
              qnum=chdb.query(val,'DataFrame')
              print(qnum)
              stop = time.time()
              duration = stop-start            
          except  Exception as er:
              print(er)
              duration =0
          print(duration)
          #row = {'dur': duration}
          #df = pd.concat([df,pd.DataFrame(row, index=[index])], axis=0, ignore_index=True)
          chdb_dict[index]=duration
    #print(chdb_dict)
    return chdb_dict

mydict_chdb=execute_query(sql_chdb)
#print(mydict_chdb)


##appending values of mydict into mychdblist##
mychdblist=[]
for key, value in mydict_chdb.items():
    mychdblist.append(value)
#print(mychdblist)

##creating dataframe
df=pd.DataFrame(columns=['chDB'],data=mychdblist)
#changing index to start from 1
df.index += 1 
print(df)

#plotting graph
df.plot.bar(rot=0)
plt.xlabel("Queries")
plt.ylabel("Duration in Second. Lower is Better")
plt.title("TPCH-SF10")
plt.legend(loc=0)
plt.show()

