import tkinter as tk
import json
import cv2
import pyautogui
import numpy as np
import keyboard
import numpy as np
import keyboard
from threading import Thread
import Quartz


is_mapping_key = False
key_mapping = {}

def get_game_window():
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for window in windows:
        if window.get("kCGWindowOwnerName") == "RP02":
            window_rect = window.get("kCGWindowBounds")
            return (window_rect["X"], window_rect["Y"], window_rect["Width"], window_rect["Height"])
    return None

def load_config():
    try:
        with open('config.json', 'r') as config_file:
            return json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(key_mapping):
    with open('config.json', 'w') as config_file:
        json.dump(key_mapping, config_file)

def begin_key_mapping():
    global is_mapping_key
    is_mapping_key = True
    print("Press the key you want to map for 'prêt' action...")
    Thread(target=wait_for_key).start()

def wait_for_key():
    global is_mapping_key
    key = keyboard.read_event(suppress=True)
    if key.event_type == keyboard.KEY_DOWN and is_mapping_key:
        key_mapping['prêt'] = key.name
        save_config()
        update_button_text()
        is_mapping_key = False
        setup_global_key_listener()

def wait_for_key():
    global is_mapping_key
    key = keyboard.read_event(suppress=True)
    if key.event_type == keyboard.KEY_DOWN and is_mapping_key:
        key_mapping['prêt'] = key.name
        save_config()
        update_button_text()
        is_mapping_key = False
        setup_global_key_listener()

def setup_global_key_listener():
    if 'prêt' in key_mapping:
        keyboard.add_hotkey(key_mapping['prêt'], lambda: find_and_click_button("Images/bouton_pret.png"), suppress=True)

def update_button_text():
    current_key = key_mapping.get('prêt', 'Mapper une touche')
    mapping_button.config(text=f"Prêt: {current_key}")

def find_and_click_button(image_path):
    game_window_coords = get_game_window()
    if game_window_coords is not None:
        button_location = pyautogui.locateOnScreen(image_path, region=game_window_coords)
        if button_location is not None:
            button_center = pyautogui.center(button_location)
            pyautogui.click(button_center)
            print(f"clic effectué aux coords: {button_center}")
        else:
            print("Bouton non trouvé dans la fenêtre du jeu.")
    else:
        print("Fenêtre du jeu non trouvée.")
    # screenshot = pyautogui.screenshot()
    # screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    # screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    
    # button_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    # if button_image is None:
    #     print("Erreur lors de la lecture de l'image du bouton. Vérifiez le chemin.")
    #     return

    # # Assuming the button_image is already grayscale if it has no alpha channel
    # if len(button_image.shape) == 3:
    #     button_image_gray = cv2.cvtColor(button_image, cv2.COLOR_BGR2GRAY)
    # else:
    #     button_image_gray = button_image
    
    # result = cv2.matchTemplate(screen_gray, button_image_gray, cv2.TM_CCOEFF_NORMED)
    # _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
    # if max_val > 0.8:
    #     print("Bouton trouvé avec une correspondance de :", max_val)
    #     button_center = (max_loc[0] + button_image.shape[1] / 2, max_loc[1] + button_image.shape[0] / 2)
    #     pyautogui.FAILSAFE = False
    #     pyautogui.click(int(button_center[0]), int(button_center[1]))
    #     print(f"Tentative de clic à : {button_center}")
    # else:
    #     print("Bouton non trouvé.")

def main():
    global key_mapping
    key_mapping = load_config()

    global root
    root = tk.Tk()
    root.title("WasherHelper")
    root.geometry("400x300")

    global mapping_button
    mapping_button = tk.Button(root, text="Mapper une touche", command=begin_key_mapping)
    mapping_button.pack()

    update_button_text()
    setup_global_key_listener()

    root.mainloop()

if __name__ == "__main__":
    main()