#!/bin/bash

declare controller_mac

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

if [ ! -f /usr/bin/bluetoothctl ]; then
    echo "Please install bluez"
    exit 1
fi

while true; do
    echo "Would you like to add a new controller or connect to an existing one?"
    echo ""
    echo "1) Add new controller"
    echo "2) Connect to existing controller"
    echo ""
    read -p "Enter your choice: " choice

    # Add new controller
    if [ "$choice" == "1" ]; then
        echo "Press Start + Y on your controller for about 3 seconds to start pairing."
        echo "Press enter when you're ready to start pairing."
        read -p ""

        controller_mac="$( sudo bluetoothctl --timeout=5 scan on | grep "Pro Controller" | awk '{print $3}' | head -n 1 )"
        if [ -z "$controller_mac" ]; then
            echo "No controller found"
            exit 1
        fi
        echo "Connecting to $controller_mac ..."
        sudo bluetoothctl pair "$controller_mac"
        sudo bluetoothctl trust "$controller_mac"
        sudo bluetoothctl connect "$controller_mac"
        break
    fi

    # Connect to existing controller
    if [ "$choice" == "2" ]; then
        echo "Make sure your controller is on."
        echo "Press enter when you're ready to start connecting."
        read -p ""
        controller_mac="$( sudo bluetoothctl devices | grep "Pro Controller" | awk '{print $2}' | head -n 1 )"
        if [ -z "$controller_mac" ]; then
            echo "No controller found"
            exit 1
        fi
        echo "Connecting to $controller_mac ..."
        sudo bluetoothctl connect "$controller_mac"
        break
    fi

    echo "Invalid choice"
    echo ""
done
