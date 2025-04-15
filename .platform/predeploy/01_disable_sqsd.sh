# filepath: .platform/hooks/predeploy/01_disable_sqsd.sh
#!/bin/bash
echo "Disabling sqsd service..."
systemctl stop sqsd.service
systemctl disable sqsd.service