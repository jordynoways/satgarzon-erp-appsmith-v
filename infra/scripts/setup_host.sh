#!/bin/bash
set -e

echo "=== [1/6] Limpiando paquetes problemáticos ==="
echo 'jordy' | sudo -S dpkg --configure -a || true
echo 'jordy' | sudo -S apt --fix-broken install -y || true

echo "=== [2/6] Instalando stack de virtualización ==="
export DEBIAN_FRONTEND=noninteractive
echo 'jordy' | sudo -S apt install -y cockpit cockpit-machines qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst || {
    echo "WARN: apt install falló, intentando con --fix-broken..."
    echo 'jordy' | sudo -S apt --fix-broken install -y
    echo 'jordy' | sudo -S apt install -y cockpit cockpit-machines qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst
}

echo "=== [3/6] Habilitando servicios ==="
echo 'jordy' | sudo -S systemctl enable --now libvirtd
echo 'jordy' | sudo -S systemctl enable --now cockpit.socket

echo "=== [4/6] Configurando red virtual ==="
echo 'jordy' | sudo -S virsh net-start default 2>/dev/null || echo "Red default ya activa"
echo 'jordy' | sudo -S virsh net-autostart default

echo "=== [5/6] Añadiendo usuario al grupo libvirt ==="
echo 'jordy' | sudo -S usermod -aG libvirt garzon
echo 'jordy' | sudo -S usermod -aG kvm garzon

echo "=== [6/6] Verificación ==="
echo "--- KVM soportado:"
kvm-ok 2>/dev/null || echo 'jordy' | sudo -S kvm-ok || echo "kvm-ok no disponible, verificando /dev/kvm..."
ls -la /dev/kvm 2>/dev/null || echo "/dev/kvm no existe"

echo "--- Servicios activos:"
systemctl is-active libvirtd
systemctl is-active cockpit.socket

echo "--- Cockpit en puerto 9090:"
ss -tunelp | grep 9090 || echo "Puerto 9090 no detectado aún"

echo "--- Virsh lista de VMs:"
virsh list --all 2>/dev/null || echo "virsh no accesible"

echo "=== SETUP COMPLETADO ==="
