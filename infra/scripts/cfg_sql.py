#!/usr/bin/env python3
import winrm, sys

s = winrm.Session("http://192.168.122.81:5985/wsman", auth=("vmgarzon", "1978"), transport="ntlm")

def ps(cmd, label):
    print(f"\n=== {label} ===")
    sys.stdout.flush()
    r = s.run_ps(cmd)
    o = r.std_out.decode("utf-8", errors="replace").strip()
    e = r.std_err.decode("utf-8", errors="replace").strip()
    if o: print(o)
    if e: print(f"[ERR] {e[:200]}")
    sys.stdout.flush()
    return o

ps('Get-Service MSSQL* | Format-Table Name,Status -Auto', '1-SERVICIOS SQL')
ps('New-NetFirewallRule -DisplayName SQL1433 -Direction Inbound -Protocol TCP -LocalPort 1433 -Action Allow -EA SilentlyContinue; echo OK', '2-FIREWALL')
ps('New-NetFirewallRule -DisplayName ICMP4 -Protocol ICMPv4 -IcmpType 8 -Action Allow -Direction Inbound -EA SilentlyContinue; echo OK', '3-ICMP')
o = ps(r'Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL" -EA SilentlyContinue | Format-List', '4-INSTANCIAS')
ps(r'''
$k = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL" -EA Stop
$k.PSObject.Properties | Where-Object {$_.Name -notlike "PS*"} | ForEach-Object {
  $v = $_.Value
  $tcp = "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\$v\MSSQLServer\SuperSocketNetLib\Tcp"
  if(Test-Path $tcp){
    Set-ItemProperty $tcp -Name Enabled -Value 1
    $ia = "$tcp\IPAll"
    if(Test-Path $ia){ Set-ItemProperty $ia TcpPort 1433; Set-ItemProperty $ia TcpDynamicPorts "" }
    echo "TCP habilitado para $v"
  }
}''', '5-TCP/IP')
ps('''
$svc = Get-Service MSSQL* | Where-Object {$_.Name -notlike "*Launch*" -and $_.Name -notlike "*Agent*"} | Select -First 1
if($svc){ Restart-Service $svc.Name -Force; Start-Sleep 3; Get-Service $svc.Name | Format-Table Name,Status -Auto }
''', '6-RESTART')
ps('Start-Sleep 2; netstat -an | Select-String ":1433.*LISTEN"', '7-PUERTO')
print("\nDONE")
