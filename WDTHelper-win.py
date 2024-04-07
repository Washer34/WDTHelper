import tkinter as tk
from tkinter import filedialog
import json
import cv2
import pyautogui
import numpy as np
import keyboard
from threading import Thread
from time import sleep
import random

is_mapping_key = False
actions = []
is_paused = False

def load_config_dialog():
    global actions
    filename = filedialog.askopenfilename(initialdir="/", title="Select file",
                                            filetypes=(("json files", "*.json"), ("all files", "*.*")))
    if filename:
        try:
            with open(filename, 'r') as config_file:
                actions = json.load(config_file)
                update_ui()
                print("Configuration chargée avec succès !")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erreur lors du chargement du fichier de configuration : {e}")

def monitor_ctrl_and_click(image_path):
    global is_paused
    while True:
        if keyboard.is_pressed('ctrl') and not is_paused:
            original_position = pyautogui.position()
            
            find_and_hold_click(image_path)
            
            pyautogui.moveTo(original_position)
        sleep(0.1)

def find_and_hold_click(image_path):
    screenshot = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    
    button_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if button_image is None:
        print("Erreur lors de la lecture de l'image du bouton. Vérifiez le chemin.")
        return

    if len(button_image.shape) == 3:
        button_image_gray = cv2.cvtColor(button_image, cv2.COLOR_BGR2GRAY)
    else:
        button_image_gray = button_image

    result = cv2.matchTemplate(screen_gray, button_image_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val > 0.8:
        button_center = (max_loc[0] + button_image.shape[1] // 2, max_loc[1] + button_image.shape[0] // 2)
        pyautogui.moveTo(button_center[0], button_center[1])
        pyautogui.mouseDown()
        while keyboard.is_pressed('ctrl'):
            sleep(0.1)
        pyautogui.mouseUp()

def load_config():
    try:
        with open('config.json', 'r') as config_file:
            return json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_config():
    with open('config.json', 'w') as config_file:
        json.dump(actions, config_file, indent=4)

def add_action():
    action_name = action_name_entry.get()
    if action_name and all(action['name'] != action_name for action in actions):
        actions.append({'name': action_name, 'key': 'Mapper une touche'})
        update_ui()
        save_config()

def begin_key_mapping(action):
    global is_mapping_key
    if is_paused:
        return
    is_mapping_key = True
    print(f"Press the key you want to map for '{action['name']}' action...")
    Thread(target=lambda: wait_for_key(action)).start()

def wait_for_key(action):
    global is_mapping_key
    key = keyboard.read_event(suppress=True)
    if key.event_type == keyboard.KEY_DOWN and is_mapping_key:
        action['key'] = key.name
        save_config()
        update_ui()
        is_mapping_key = False
        setup_global_key_listener()

def setup_global_key_listener():
    for action in actions:
        if action['key'] != 'Mapper une touche':
            keyboard.add_hotkey(action['key'], lambda a=action: find_and_click_button(f"Images/{a['name']}.png"), suppress=True)
    keyboard.add_hotkey('esc', toggle_pause)
    keyboard.add_hotkey('space', lambda: find_and_click_button("Images/ready.png", "Images/end_of_turn.png"), suppress=True)

def toggle_pause():
    global is_paused
    is_paused = not is_paused
    pause_label.config(text="État: Pause" if is_paused else "État: Actif")

def find_and_click_button(image_path, alternative_image_path=None):
    if is_paused:
        return
    screenshot = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    
    button_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    matched = match_and_click(button_image, screen_gray)
    
    if not matched and alternative_image_path:
        button_image = cv2.imread(alternative_image_path, cv2.IMREAD_UNCHANGED)
        match_and_click(button_image, screen_gray)
    
def match_and_click(button_image, screen_gray):
    if button_image is None:
        print("Erreur lors de la lecture de l'image du bouton. Vérifiez le chemin.")
        return False

    if len(button_image.shape) == 3:
        button_image_gray = cv2.cvtColor(button_image, cv2.COLOR_BGR2GRAY)
    else:
        button_image_gray = button_image

    result = cv2.matchTemplate(screen_gray, button_image_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val > 0.8:
        print("Bouton trouvé avec une correspondance de :", max_val)
        
        center_x = max_loc[0] + button_image.shape[1] // 2
        center_y = max_loc[1] + button_image.shape[0] // 2
        
        random_x = center_x + random.randint(-10, 10)  # Ajustez ces valeurs selon la taille de l'image
        random_y = center_y + random.randint(-10, 10)
        
        original_position = pyautogui.position()
        
        pyautogui.click(random_x, random_y)
        
        pyautogui.moveTo(original_position)
        
        print(f"Tentative de clic à : ({random_x}, {random_y}) et retour à la position {original_position}")
        return True
    else:
        print("Bouton non trouvé.")
        return False

def update_ui():
    for widget in action_frame.winfo_children():
        widget.destroy()
    for action in actions:
        tk.Label(action_frame, text=f"{action['name']} - {action['key']}").pack()
        tk.Button(action_frame, text=f"Mapper {action['name']}", command=lambda a=action: begin_key_mapping(a)).pack()

def main():
    global actions, pause_label
    actions = load_config()
    
    Thread(target=monitor_ctrl_and_click, args=("Images/mobs.png",), daemon=True).start()

    global root
    root = tk.Tk()
    root.title("WasherHelper")
    root.geometry("400x300")

    tk.Button(root, text="Charger une configuration", command=load_config_dialog).pack()
    
    global action_name_entry
    action_name_entry = tk.Entry(root)
    action_name_entry.pack()

    tk.Button(root, text="Ajouter une action", command=add_action).pack()
    
    pause_label = tk.Label(root, text="État: Actif")
    pause_label.pack()

    global action_frame
    action_frame = tk.Frame(root)
    action_frame.pack()

    update_ui()
    setup_global_key_listener()

    root.mainloop()

if __name__ == "__main__":
    main()