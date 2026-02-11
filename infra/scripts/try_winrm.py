#!/usr/bin/env python3
"""Prueba diferentes credenciales WinRM."""
import winrm

VM_IP = "192.168.122.81"
PASS = "1978"

users = [
    "vmgarzon",
    "Garzon VM",
    ".\\vmgarzon",
    ".\\Garzon VM",
    "VMGARZON\\vmgarzon",
]

for u in users:
    try:
        print(f"Probando: {u}")
        s = winrm.Session(
            f"http://{VM_IP}:5985/wsman",
            auth=(u, PASS),
            transport="ntlm"
        )
        r = s.run_cmd("hostname")
        out = r.std_out.decode().strip()
        print(f"  EXITO! hostname={out}")
        
        # Si funciona, configurar SQL Server
        print("\nConfigurando SQL Server...")
        
        # Firewall
        r2 = s.run_ps('New-NetFirewallRule -DisplayName "SQL1433" -Direction Inbound -Protocol TCP -LocalPort 1433 -Action Allow -ErrorAction SilentlyContinue; Write-Output "FW OK"')
        print(f"  Firewall: {r2.std_out.decode().strip()}")
        
        # ICMP
        r3 = s.run_ps('New-NetFirewallRule -DisplayName "ICMP" -Protocol ICMPv4 -IcmpType 8 -Action Allow -Direction Inbound -ErrorAction SilentlyContinue; Write-Output "ICMP OK"')
        print(f"  ICMP: {r3.std_out.decode().strip()}")
        
        # Buscar SQL Server
        r4 = s.run_ps('Get-Service | Where-Object { $_.Name -like "MSSQL*" } | Format-Table Name, Status -AutoSize')
        print(f"  SQL Services:\n{r4.std_out.decode().strip()}")
        
        # Habilitar TCP/IP via registro
        r5 = s.run_ps(r'''
$instances = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL" -ErrorAction SilentlyContinue
if ($instances) {
    $props = $instances.PSObject.Properties | Where-Object { $_.Name -notlike "PS*" }
    foreach ($p in $props) {
        Write-Output "Instancia: $($p.Name) = $($p.Value)"
        $basePath = "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\$($p.Value)\MSSQLServer\SuperSocketNetLib\Tcp"
        if (Test-Path $basePath) {
            Set-ItemProperty -Path $basePath -Name "Enabled" -Value 1
            Write-Output "TCP habilitado"
            $ipAllPath = "$basePath\IPAll"
            if (Test-Path $ipAllPath) {
                Set-ItemProperty -Path $ipAllPath -Name "TcpPort" -Value "1433"
                Set-ItemProperty -Path $ipAllPath -Name "TcpDynamicPorts" -Value ""
                Write-Output "Puerto 1433 fijado"
            }
        }
    }
} else {
    Write-Output "No se encontraron instancias SQL"
}
''')
        print(f"  TCP/IP: {r5.std_out.decode().strip()}")
        if r5.std_err:
            print(f"  [err]: {r5.std_err.decode().strip()[:200]}")
        
        # Reiniciar SQL Server
        r6 = s.run_ps('''
$svc = Get-Service | Where-Object { $_.Name -like "MSSQL$*" -or $_.Name -eq "MSSQLSERVER" } | Select-Object -First 1
if ($svc) {
    Restart-Service $svc.Name -Force
    Start-Sleep -Seconds 3
    $check = Get-Service $svc.Name
    Write-Output "Reiniciado: $($check.Name) = $($check.Status)"
}
''')
        print(f"  Restart: {r6.std_out.decode().strip()}")
        
        # Verificar puerto
        r7 = s.run_ps('Start-Sleep 2; netstat -an | Select-String ":1433.*LISTEN"')
        print(f"  Puerto 1433: {r7.std_out.decode().strip()}")
        
        print("\nCONFIGURACION COMPLETADA!")
        break
        
    except Exception as e:
        print(f"  FALLO: {str(e)[:80]}")
        print()

