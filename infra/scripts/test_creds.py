#!/usr/bin/env python3
import winrm, sys

users = ["vmgarzon", "Garzon VM", ".\\vmgarzon", ".\\Garzon VM"]

for u in users:
    print(f">>> Probando: [{u}] con password [1978]")
    sys.stdout.flush()
    try:
        s = winrm.Session("http://192.168.122.81:5985/wsman", auth=(u, "1978"), transport="ntlm")
        r = s.run_cmd("whoami")
        print(f"    EXITO! whoami={r.std_out.decode().strip()}")
        print(f"    STDERR={r.std_err.decode().strip()}")
        print("USUARIO_CORRECTO=" + u)
        sys.exit(0)
    except Exception as e:
        print(f"    FALLO: {e}")
    print()
    sys.stdout.flush()

print("NINGUNO FUNCIONO")
