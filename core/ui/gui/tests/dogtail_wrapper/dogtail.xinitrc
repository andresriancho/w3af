gsettings set org.gnome.desktop.interface toolkit-accessibility true
. /etc/X11/xinit/xinitrc
gnome-settings-daemon &
gnome-panel &
nautilus -n &
metacity &
sleep 10
