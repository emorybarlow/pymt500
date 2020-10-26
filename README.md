# pymt500

```
sudo apt-get install ansible git build-essential vim

# Add iflows users to sudo group (this assumes the user you created when provisioning is iflows)
sudo visudo

# Add the following line
iflows  ALL=(ALL:ALL) ALL

cd mt500-playbook
ansible-playbook -K mt500.yml
```

If you want to specify config values from a json file:
```
ansible-playbook -K mt500.yml --extra-vars "@configs/100.json"
```
