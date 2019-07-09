VirtualBox Set-up
-----------------

#. Download Ubutnu Server ISO: https://www.ubuntu.com/download/server
#. Create VM with a NAT (Adapter 1) and a Host-only Adapter (Adapter 2) networking settings;
#. (Optional) if you want to provide access to your VM form the "outside world", you need to add a "Bridge Adatpter" and ensure that you firewall allows connections to you host machine (port 80 and 443).
#. Mount the CD media (Ubuntu Server ISO), start up VM and install the server system;
#. Loging and install the extension pack and VM exensions on your server following https://www.mobilefish.com/developer/virtualbox/virtualbox_quickguide_install_virtualbox_guest_editions_ubuntu.html
#. Shut down the server and restarts it "headless": ``VBoxManage startvm <YOUR SERVER> --type headless`` (use ``VBoxManage list vms`` to find out the name of your server);
#. Find out the IP address to connect from your host: ``VBoxManage guestcontrol <YOUR SERVER> run --exe "/sbin/ifconfig" --username <USERNAME> --password '<PASSWORD>' | grep 'inet '`` (by default it starts with **192...**)
#. Connect to your server: ``ssh <USERNAME>@<IP ADDRESS>``
