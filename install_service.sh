sudo cp ~/prj/zamyotek/zamyotek.service /etc/systemd/system
chmod u+x /home/lukjetson/prj/zamyotek/zamyotek_startup.sh
sudo systemctl enable zamyotek
sudo systemctl start zamyotek
