import requests
import time
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

OUTLET_MAP = {
    "cdp": "Outlet 1",
    "pump": "Outlet 2",
}


def get_outlets():
    """Fetch all outlet statuses."""
    response = requests.get(f"{BASE_URL}/status", auth=(USERNAME, PASSWORD))
    response.raise_for_status()
    data = response.json()
    return data.get("status", {}).get("outlet", [])


def print_outlets():
    """Print all outlets and their current status."""
    outlets = get_outlets()
    for outlet in outlets:
        name = outlet.get("name")
        status = "ON" if outlet.get("status") else "OFF"
        print(f"{name}: {status}")


def set_outlet(outlet_name, action):
    """Change the state of a specific outlet."""
    response = requests.post(
        f"{BASE_URL}/control",
        params={"target": outlet_name.lower().replace(" ", ""), "action": action},
        data={"user": USERNAME, "password": PASSWORD},
        headers={"Accept-Encoding": "gzip, deflate", "Accept": "*/*"},
    )

    if not response.ok:
        return False

    time.sleep(4)  # allow time for the state change

    outlets = get_outlets()
    for outlet in outlets:
        if outlet.get("name") == outlet_name:
            expected = action.lower() == "on"
            return outlet.get("status") == expected
    return False


def toggle_outlet(outlet_name):
    """Toggle the state of a specific outlet."""
    outlets = get_outlets()
    for outlet in outlets:
        if outlet.get("name") == outlet_name:
            new_state = "off" if outlet.get("status") else "on"
            return set_outlet(outlet_name, new_state)
    return False


# Convenience wrappers
def turn_on_cdp(): return set_outlet(OUTLET_MAP["cdp"], "on")
def turn_off_cdp(): return set_outlet(OUTLET_MAP["cdp"], "off")
def toggle_cdp(): return toggle_outlet(OUTLET_MAP["cdp"])

def turn_on_pump(): return set_outlet(OUTLET_MAP["pump"], "on")
def turn_off_pump(): return set_outlet(OUTLET_MAP["pump"], "off")
def toggle_pump(): return toggle_outlet(OUTLET_MAP["pump"])


if __name__ == "__main__":
    print("Testing power switch module...")
    print_outlets()
    print("Turning on pump...")
    turn_on_pump()
    print_outlets()
    print("Turning off pump...")
    turn_off_pump()
    print_outlets()
