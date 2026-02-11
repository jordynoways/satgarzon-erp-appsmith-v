# ============================================
# CONFIGURAR SQL SERVER PARA ACCESO REMOTO
# Ejecutar como Administrador en la VM Windows
# ============================================

Write-Host "=== [1/4] Buscando instancia de SQL Server ===" -ForegroundColor Cyan

# Buscar el servicio de SQL Server
$sqlService = Get-Service | Where-Object { $_.Name -like "MSSQL*" -and $_.Status -eq "Running" }
if ($sqlService) {
    Write-Host "SQL Server encontrado: $($sqlService.Name) - Estado: $($sqlService.Status)" -ForegroundColor Green
} else {
    $sqlService = Get-Service | Where-Object { $_.Name -like "MSSQL*" }
    if ($sqlService) {
        Write-Host "SQL Server encontrado pero NO corriendo: $($sqlService.Name) - Intentando iniciar..." -ForegroundColor Yellow
        Start-Service $sqlService.Name
    } else {
        Write-Host "ERROR: No se encontro SQL Server instalado!" -ForegroundColor Red
        pause
        exit 1
    }
}

# Detectar nombre de instancia
$instanceName = $sqlService.Name -replace "MSSQL\$", ""
if ($sqlService.Name -eq "MSSQLSERVER") {
    $instanceName = "MSSQLSERVER"
    $sqlInstance = "localhost"
} else {
    $sqlInstance = "localhost\$instanceName"
}
Write-Host "Instancia: $instanceName ($sqlInstance)" -ForegroundColor Green

Write-Host ""
Write-Host "=== [2/4] Habilitando TCP/IP en SQL Server ===" -ForegroundColor Cyan

# Cargar el modulo SMO para configurar protocolos
try {
    [System.Reflection.Assembly]::LoadWithPartialName("Microsoft.SqlServer.SqlWmiManagement") | Out-Null
    $wmi = New-Object Microsoft.SqlServer.Management.Smo.Wmi.ManagedComputer
    $tcp = $wmi.ServerInstances[$instanceName].ServerProtocols["Tcp"]
    
    if ($tcp.IsEnabled) {
        Write-Host "TCP/IP ya estaba habilitado" -ForegroundColor Green
    } else {
        $tcp.IsEnabled = $true
        $tcp.Alter()
        Write-Host "TCP/IP HABILITADO con exito" -ForegroundColor Green
    }

    # Configurar puerto 1433
    $ipAll = $tcp.IPAddresses | Where-Object { $_.Name -eq "IPAll" }
    if ($ipAll) {
        $ipAll.IPAddressProperties["TcpPort"].Value = "1433"
        $ipAll.IPAddressProperties["TcpDynamicPorts"].Value = ""
        $tcp.Alter()
        Write-Host "Puerto fijo 1433 configurado en IPAll" -ForegroundColor Green
    }
} catch {
    Write-Host "No se pudo configurar via WMI. Intentando via registro..." -ForegroundColor Yellow
    
    # Buscar en registro
    $regPaths = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server" -Recurse -ErrorAction SilentlyContinue | 
        Where-Object { $_.Name -like "*SuperSocketNetLib\Tcp" }
    
    if ($regPaths) {
        foreach ($p in $regPaths) {
            Set-ItemProperty -Path $p.PSPath -Name "Enabled" -Value 1 -ErrorAction SilentlyContinue
            Write-Host "TCP habilitado en registro: $($p.PSPath)" -ForegroundColor Green
        }
        
        # Buscar IPAll para puerto
        $ipAllPaths = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server" -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "*SuperSocketNetLib\Tcp\IPAll" }
        foreach ($p in $ipAllPaths) {
            Set-ItemProperty -Path $p.PSPath -Name "TcpPort" -Value "1433" -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $p.PSPath -Name "TcpDynamicPorts" -Value "" -ErrorAction SilentlyContinue
            Write-Host "Puerto 1433 configurado en: $($p.PSPath)" -ForegroundColor Green
        }
    } else {
        Write-Host "AVISO: No se encontraron entradas de registro TCP" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== [3/4] Configurando Firewall ===" -ForegroundColor Cyan

# Abrir puerto 1433 en firewall
$existingRule = Get-NetFirewallRule -DisplayName "SQL Server 1433" -ErrorAction SilentlyContinue
if ($existingRule) {
    Write-Host "Regla de firewall ya existe" -ForegroundColor Green
} else {
    New-NetFirewallRule -DisplayName "SQL Server 1433" -Direction Inbound -Protocol TCP -LocalPort 1433 -Action Allow | Out-Null
    Write-Host "Regla de firewall creada: Puerto 1433 TCP abierto" -ForegroundColor Green
}

# Tambien abrir SQL Browser (para instancias con nombre)
$browserRule = Get-NetFirewallRule -DisplayName "SQL Browser UDP" -ErrorAction SilentlyContinue
if (-not $browserRule) {
    New-NetFirewallRule -DisplayName "SQL Browser UDP" -Direction Inbound -Protocol UDP -LocalPort 1434 -Action Allow | Out-Null
    Write-Host "Regla de firewall para SQL Browser (UDP 1434) creada" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== [4/4] Reiniciando SQL Server ===" -ForegroundColor Cyan

Restart-Service $sqlService.Name -Force
Write-Host "SQL Server reiniciado" -ForegroundColor Green

# Verificar que esta corriendo
Start-Sleep -Seconds 3
$sqlCheck = Get-Service $sqlService.Name
Write-Host "Estado final: $($sqlCheck.Status)" -ForegroundColor $(if ($sqlCheck.Status -eq "Running") { "Green" } else { "Red" })

# Verificar puerto
Start-Sleep -Seconds 2
$listening = netstat -an | Select-String ":1433"
if ($listening) {
    Write-Host ""
    Write-Host "EXITO! SQL Server escuchando en puerto 1433:" -ForegroundColor Green
    $listening | ForEach-Object { Write-Host $_.Line -ForegroundColor White }
} else {
    Write-Host ""
    Write-Host "AVISO: Puerto 1433 no detectado aun. Puede necesitar reiniciar la VM." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== CONFIGURACION COMPLETADA ===" -ForegroundColor Green
Write-Host "Ahora puedes conectarte desde Linux con: sqlcmd -S 192.168.122.81,1433" -ForegroundColor White
Write-Host ""
pause
