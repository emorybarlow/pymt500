# pymt500

```
sudo apt-get install ansible git build-essential vim

# Add iflows users to sudo group (this assumes the user you created when provisioning is iflows)
sudo visudo

# Add the following line
administrator  ALL=(ALL:ALL) ALL

cd mt500-playbook
ansible-playbook -K mt500.yml
```

If you want to specify config values from a json file:
```
ansible-playbook -K mt500.yml --extra-vars "@configs/100.json"
```

You'll need to upgrade ansible
```
sudo apt-get install software-properties-common
sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update
sudo apt-get install ansible
```
