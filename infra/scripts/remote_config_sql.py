#!/usr/bin/env python3
"""Configura SQL Server en la VM via WinRM."""
import winrm
import sys

VM_IP = "192.168.122.81"
USER = "vmgarzon"
PASS = "1978"

def run_ps(session, script, label=""):
    if label:
        print(f"\n=== {label} ===")
    r = session.run_ps(script)
    out = r.std_out.decode("utf-8", errors="replace").strip()
    err = r.std_err.decode("utf-8", errors="replace").strip()
    if out:
        print(out)
    if err:
        print(f"[STDERR] {err}")
    return r.status_code, out, err

def main():
    print(f"Conectando a {VM_IP} via WinRM...")
    s = winrm.Session(
        f"http://{VM_IP}:5985/wsman",
        auth=(USER, PASS),
        transport="ntlm"
    )

    # 1. Buscar SQL Server
    run_ps(s, 'Get-Service | Where-Object { $_.Name -like "MSSQL*" -or $_.Name -like "SQL*" } | Select-Object Name, Status | Format-Table -AutoSize', "SERVICIOS SQL SERVER")

    # 2. Abrir Firewall puerto 1433
    run_ps(s, '''
$rule = Get-NetFirewallRule -DisplayName "SQL Server 1433" -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule -DisplayName "SQL Server 1433" -Direction Inbound -Protocol TCP -LocalPort 1433 -Action Allow | Out-Null
    Write-Output "Regla firewall CREADA: Puerto 1433 abierto"
} else {
    Write-Output "Regla firewall YA EXISTIA"
}
''', "FIREWALL")

    # 3. Abrir Firewall ICMP (para ping)
    run_ps(s, '''
$rule = Get-NetFirewallRule -DisplayName "Allow ICMPv4" -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule -DisplayName "Allow ICMPv4" -Protocol ICMPv4 -IcmpType 8 -Action Allow -Direction Inbound | Out-Null
    Write-Output "ICMP habilitado (ping)"
} else {
    Write-Output "ICMP ya estaba habilitado"
}
''', "ICMP/PING")

    # 4. Buscar instancia SQL y habilitar TCP/IP via registro
    run_ps(s, r'''
$instances = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL" -ErrorAction SilentlyContinue
if ($instances) {
    $props = $instances.PSObject.Properties | Where-Object { $_.Name -notlike "PS*" }
    foreach ($p in $props) {
        Write-Output "Instancia encontrada: $($p.Name) -> $($p.Value)"
        $basePath = "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\$($p.Value)\MSSQLServer\SuperSocketNetLib\Tcp"
        if (Test-Path $basePath) {
            Set-ItemProperty -Path $basePath -Name "Enabled" -Value 1
            Write-Output "TCP/IP HABILITADO en registro"
            $ipAllPath = "$basePath\IPAll"
            if (Test-Path $ipAllPath) {
                Set-ItemProperty -Path $ipAllPath -Name "TcpPort" -Value "1433"
                Set-ItemProperty -Path $ipAllPath -Name "TcpDynamicPorts" -Value ""
                Write-Output "Puerto fijo 1433 configurado en IPAll"
            }
        } else {
            Write-Output "AVISO: No se encontro ruta TCP en registro"
        }
    }
} else {
    Write-Output "ERROR: No se encontraron instancias SQL Server en el registro"
}
''', "HABILITAR TCP/IP")

    # 5. Reiniciar SQL Server
    run_ps(s, '''
$svc = Get-Service | Where-Object { $_.Name -like "MSSQL*" -and $_.Name -ne "MSSQLFDLauncher" -and $_.Name -notlike "*Agent*" } | Select-Object -First 1
if ($svc) {
    Restart-Service $svc.Name -Force
    Start-Sleep -Seconds 3
    $check = Get-Service $svc.Name
    Write-Output "SQL Server reiniciado: $($check.Name) = $($check.Status)"
} else {
    Write-Output "ERROR: No se encontro servicio SQL Server"
}
''', "REINICIAR SQL SERVER")

    # 6. Verificar puerto 1433
    run_ps(s, '''
Start-Sleep -Seconds 2
$listening = netstat -an | Select-String ":1433.*LISTENING"
if ($listening) {
    Write-Output "EXITO! Puerto 1433 escuchando:"
    $listening | ForEach-Object { Write-Output $_.Line.Trim() }
} else {
    Write-Output "AVISO: Puerto 1433 no detectado"
    netstat -an | Select-String ":14" | ForEach-Object { Write-Output $_.Line.Trim() }
}
''', "VERIFICAR PUERTO 1433")

    print("\n=== CONFIGURACION COMPLETADA ===")

if __name__ == "__main__":
    main()
