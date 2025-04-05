# aquastilla-softener
A Home Assistant integration and Python library for interacting with Aquastilla water softeners via their API.

## 📦 Installation

You can install the package using pip:

`pip install aquastilla-softener`

## 🚀 Usage

    from aquastilla_softener import AquastillaSoftener
    softener = AquastillaSoftener(email="user@example.com", password="your_password")
    devices = softener.list_devices()

    print("Devices:")
        for device in devices:
        print(f"UUID: {device['uuid']}, Model: {device['model']['model']}")
    
    if devices:
        for device in devices:
            device_data = softener.get_device_data(device)
            print(f"\nDevice UUID: {device_data.uuid}")
            print(f"Model: {device_data.model}")
            print(f"State: {device_data.state}")
            print(f"Salt Level: {device_data.salt_level_percent}%")
            print(f"Salt Days Remaining: {device_data.salt_days_remaining}")
            print(f"Water Available: {device_data.water_available_liters} l")
            print(f"Max Water Capacity: {device_data.max_water_capacity_liters} l")
            print(f"Expected Regeneration: {device_data.expected_regeneration_date}")
            print(f"Current Water Usage: {device_data.current_water_usage_liters} l")
            print(f"Today Water Usage: {device_data.today_water_usage_liters} l")
            print(f"Last Regeneration: {device_data.last_regeneration}")


# 🧠  Features

    ✅ Login to the Aquastilla cloud API

    ✅ Fetch current softener status

