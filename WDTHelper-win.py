import tkinter as tk
from tkinter import ttk 
from tkinter import ttk, filedialog, simpledialog, messagebox
import json
import cv2
import pyautogui
import pygetwindow as gw
import numpy as np
import keyboard
from threading import Thread
from time import sleep
import random

is_mapping_key = False
actions = []
is_paused = False
esc_pressed = False

def screenshot_active_window():
    try:
        active_window = gw.getActiveWindow()
        if active_window is None:
            print("Aucune fenêtre active détectée.")
            return None
        
        x, y, width, height = active_window.left, active_window.top, active_window.width, active_window.height
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return screenshot
    except Exception as e:
        print(f"Erreur lors de la capture de la fenêtre active: {e}")
        return None

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
    screenshot = screenshot_active_window()
    if screenshot is None:
        print("Aucun screenshot disponible.")
        return
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

    if max_val > 0.75:
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

actions = load_config()

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
    if is_paused or is_mapping_key:
        return
    is_mapping_key = True
    new_key = simpledialog.askstring("Key Mapping", f"Press new key for action '{action['name']}':", parent=root)
    if new_key:
        action['key'] = new_key
        save_config()
        update_ui()
    is_mapping_key = False

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
            keyboard.add_hotkey(action['key'], lambda a=action: execute_action(a), suppress=False)

    keyboard.add_hotkey('esc', toggle_pause, suppress=False)
    keyboard.add_hotkey('space', lambda: execute_space_action(), suppress=False)

def execute_action(action):
    if not is_paused:
        find_and_click_button(f"Images/{action['name']}.png")

def execute_space_action():
    if not is_paused:
        find_and_click_button("Images/ready.png", "Images/end_of_turn.png")

def toggle_pause():
    global is_paused, pause_label
    is_paused = not is_paused
    update_pause_label()

def update_pause_label():
    if is_paused:
        pause_label.config(text="État: Pause", background='red3')
    else:
        pause_label.config(text="État: Actif", background='DeepSkyBlue2')


def find_and_click_button(image_path, alternative_image_path=None):
    if is_paused:
        return
    screenshot = screenshot_active_window()
    if screenshot is None:
        print("Aucun screenshot disponible.")
        return
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
        
        random_x = center_x + random.randint(-10, 10)
        random_y = center_y + random.randint(-10, 10)
        
        original_position = pyautogui.position()
        
        pyautogui.click(random_x, random_y)
        
        pyautogui.moveTo(original_position)
        
        print(f"Tentative de clic à : ({random_x}, {random_y}) et retour à la position {original_position}")
        return True
    else:
        print("Bouton non trouvé.")
        return False

def setup_ui():
    global action_frame, action_treeview, action_name_entry, root, control_frame

    action_frame = ttk.Frame(root, padding=10)
    action_frame.pack(fill=tk.BOTH, expand=True)

    cols = ('Action', 'Key')
    action_treeview = ttk.Treeview(action_frame, columns=cols, show='headings')
    for col in cols:
        action_treeview.heading(col, text=col)
        action_treeview.column(col, width=150)
    action_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(action_frame, orient='vertical', command=action_treeview.yview)
    scrollbar.pack(side=tk.RIGHT, fill='y')
    action_treeview.configure(yscrollcommand=scrollbar.set)
    action_treeview.bind("<Double-1>", on_treeview_double_click)

    control_frame = ttk.Frame(root, padding=(10, 10))
    control_frame.pack(fill=tk.X)

    action_name_entry = ttk.Entry(control_frame, width=20)
    action_name_entry.pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(control_frame, text="Ajouter une action", command=add_action).pack(side=tk.LEFT)
    ttk.Button(control_frame, text="Delete Action", command=delete_action).pack(side=tk.LEFT)

    ttk.Button(control_frame, text="Charger une configuration", command=load_config_dialog).pack(side=tk.LEFT)

def on_treeview_double_click(event):
    item_id = action_treeview.selection()[0]
    item = action_treeview.item(item_id)
    action = next((a for a in actions if a['name'] == item['values'][0]), None)
    if action:
        begin_key_mapping(action)

def delete_action():
    selected_item = action_treeview.selection()
    if not selected_item:
        messagebox.showerror("Error", "No action selected")
        return
    item = action_treeview.item(selected_item[0])
    action_name = item['values'][0]
    answer = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete action '{action_name}'?")
    if answer:
        global actions
        actions = [action for action in actions if action['name'] != action_name]
        save_config()
        update_ui()

def on_treeview_click(event):
    region = action_treeview.identify("region", event.x, event.y)
    if region == "cell":
        item_id = action_treeview.identify_row(event.y)
        item = action_treeview.item(item_id)
        action_name = item['values'][0]
        if item['values'][1] == 'Mapper une touche':
            action = next((a for a in actions if a['name'] == action_name), None)
            if action:
                begin_key_mapping(action)

def update_ui():
    action_treeview.delete(*action_treeview.get_children())
    for action in actions:
        action_treeview.insert('', 'end', values=(action['name'], action['key']))

def main():
    global actions, pause_label, action_name_entry, action_frame, root

    Thread(target=monitor_ctrl_and_click, args=("Images/mobs.png",), daemon=True).start()

    root = tk.Tk()
    root.title("WasherHelper")
    root.geometry("600x400")

    style = ttk.Style()
    style.configure("TButton", font=('Helvetica', 12, 'bold'), borderwidth='4')
    style.configure("TLabel", font=('Helvetica', 12, 'bold'), background='light grey', foreground='black')
    style.configure("TEntry", font=('Helvetica', 12), foreground='blue')
    style.configure("TFrame", background='light grey')

    pause_label = ttk.Label(root, text="État: Actif", background='DeepSkyBlue2', font=('Helvetica', 14, 'bold'))
    pause_label.pack(side=tk.TOP, fill=tk.X)

    setup_ui()
    update_ui()
    setup_global_key_listener()

    root.mainloop()

if __name__ == "__main__":
    main()