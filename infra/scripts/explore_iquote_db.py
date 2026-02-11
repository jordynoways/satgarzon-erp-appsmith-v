#!/usr/bin/env python3
"""Explora la BD de iQuote via WinRM + PowerShell + sqlcmd."""
import winrm, sys

s = winrm.Session("http://192.168.122.81:5985/wsman", auth=("vmgarzon", "1978"), transport="ntlm")

def ps_sql(query, label):
    print(f"\n=== {label} ===")
    sys.stdout.flush()
    # Usar PowerShell Invoke-Sqlcmd para evitar problemas de comillas
    ps_cmd = f'''
$q = @"
{query}
"@
try {{
    Invoke-Sqlcmd -ServerInstance "localhost\\IQUOTE" -Query $q -TrustServerCertificate | Format-Table -AutoSize | Out-String -Width 300
}} catch {{
    # Fallback a sqlcmd
    $escaped = $q -replace '"', '""'
    sqlcmd -S "localhost\\IQUOTE" -E -Q $q -W -s "|"
}}
'''
    r = s.run_ps(ps_cmd)
    o = r.std_out.decode("utf-8", errors="replace").strip()
    e = r.std_err.decode("utf-8", errors="replace").strip()
    if o: print(o)
    if e and "CLIXML" not in e and "Warning" not in e: 
        print(f"[ERR] {e[:300]}")
    sys.stdout.flush()
    return o

# 1. Listar BDs
ps_sql("SELECT name FROM sys.databases ORDER BY name", "BASES DE DATOS")

# 2. Listar todas las tablas de iQuote
o = ps_sql("""
USE [iQuote]
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME
""", "TODAS LAS TABLAS")

# 3. Buscar tablas de productos/precios
ps_sql("""
USE [iQuote]
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE' 
AND (TABLE_NAME LIKE '%product%' OR TABLE_NAME LIKE '%price%' 
     OR TABLE_NAME LIKE '%item%' OR TABLE_NAME LIKE '%catalog%'
     OR TABLE_NAME LIKE '%article%' OR TABLE_NAME LIKE '%part%')
ORDER BY TABLE_NAME
""", "TABLAS PRODUCTOS/PRECIOS")

# 4. Buscar columnas interesantes
ps_sql("""
USE [iQuote]
SELECT t.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS c
JOIN INFORMATION_SCHEMA.TABLES t ON c.TABLE_NAME = t.TABLE_NAME AND c.TABLE_SCHEMA = t.TABLE_SCHEMA
WHERE t.TABLE_TYPE = 'BASE TABLE'
AND (c.COLUMN_NAME LIKE '%ref%' OR c.COLUMN_NAME LIKE '%sku%' 
     OR c.COLUMN_NAME LIKE '%code%' OR c.COLUMN_NAME LIKE '%price%'
     OR c.COLUMN_NAME LIKE '%name%' OR c.COLUMN_NAME LIKE '%desc%')
ORDER BY t.TABLE_NAME
""", "COLUMNAS CON REF/SKU/PRICE/NAME")

print("\nDONE")
