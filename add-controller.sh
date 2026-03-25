#!/bin/bash

declare controller_mac

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

if [ ! -f /usr/bin/bluetoothctl ]; then
    echo "Please install bluez: sudo apt install bluez"
    exit 1
fi

# Ensure Bluetooth service is running and adapter is powered on
echo "Starting Bluetooth service..."
systemctl start bluetooth 2>/dev/null
sleep 1

rfkill unblock bluetooth 2>/dev/null

echo "Powering on Bluetooth adapter..."
bluetoothctl power on
sleep 2

# Verify adapter is ready
if ! bluetoothctl show | grep -q "Powered: yes"; then
    echo "ERROR: Bluetooth adapter failed to power on."
    echo "Check 'rfkill list' and '/boot/config.txt' for Bluetooth settings."
    exit 1
fi

echo "Bluetooth adapter is ready."
echo ""

while true; do
    echo "Would you like to add a new controller or connect to an existing one?"
    echo ""
    echo "1) Add new controller"
    echo "2) Connect to existing controller"
    echo ""
    read -p "Enter your choice: " choice

    # Add new controller
    if [ "$choice" == "1" ]; then
        echo ""
        echo "Put your controller in pairing mode:"
        echo "  - 8BitDo SN30 Pro: Hold Start + Y for ~3 seconds (LED blinks rapidly)"
        echo ""
        read -p "Press Enter when the controller LED is blinking..."

        echo "Scanning for 10 seconds..."
        controller_mac="$( bluetoothctl --timeout=10 scan on | grep -i "8Bitdo SN30 Pro\|Pro Controller" | awk '{print $3}' | head -n 1 )"
        if [ -z "$controller_mac" ]; then
            echo ""
            echo "No controller found. Tips:"
            echo "  - Make sure the controller LED is blinking rapidly (pairing mode)"
            echo "  - Try holding Start + Y again for 5 seconds"
            echo "  - Move the controller closer to the Pi"
            echo "  - Try: bluetoothctl scan on   (and watch for your device manually)"
            exit 1
        fi
        echo "Found controller: $controller_mac"
        echo "Pairing..."
        bluetoothctl pair "$controller_mac"
        bluetoothctl trust "$controller_mac"
        bluetoothctl connect "$controller_mac"
        echo "Done!"
        break
    fi

    # Connect to existing controller
    if [ "$choice" == "2" ]; then
        echo "Make sure your controller is on."
        read -p "Press Enter when ready..."
        controller_mac="$( bluetoothctl devices | grep -i "8Bitdo SN30 Pro\|Pro Controller" | awk '{print $2}' | head -n 1 )"
        if [ -z "$controller_mac" ]; then
            echo "No paired controller found. Try option 1 to pair a new one."
            exit 1
        fi
        echo "Connecting to $controller_mac ..."
        bluetoothctl connect "$controller_mac"
        echo "Done!"
        break
    fi

    echo "Invalid choice"
    echo ""
done
