import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

def bind_enter_to_buttons(widget):
    if isinstance(widget, tk.Button):
        widget.bind("<Return>", lambda event: widget.invoke())
    for child in widget.winfo_children():
        bind_enter_to_buttons(child)

def add_entry():
    key = key_entry.get()
    value = value_entry.get()

    if not key:
        messagebox.showwarning("Errore", "La chiave non può essere vuota!")
        return

    # Try to parse the value as a number, list, or dictionary
    try:
        parsed_value = eval(value)
    except:
        parsed_value = value  # Treat as a string

    try:
        selected_item = tree.selection()[0]
        keys = get_full_key_path(selected_item)
        nested_dict = get_nested_dict(data, keys)
        if isinstance(nested_dict, dict):
            if key in nested_dict:
                messagebox.showwarning("Errore", "La chiave esiste già!")
                return
            nested_dict[key] = parsed_value
            add_tree_item(selected_item, key, parsed_value)
        else:
            messagebox.showwarning("Errore", "L'elemento selezionato non è un dizionario!")
            return
    except IndexError:  # No selection, add to root
        if key in data:
            messagebox.showwarning("Errore", "La chiave esiste già!")
            return
        data[key] = parsed_value
        add_tree_item("", key, parsed_value)

    key_entry.delete(0, tk.END)
    value_entry.delete(0, tk.END)

def remove_entry():
    try:
        selected_item = tree.selection()[0]
        keys = get_full_key_path(selected_item)
        if not keys:
            messagebox.showwarning("Errore", "Seleziona un elemento valido da rimuovere!")
            return

        parent_id = tree.parent(selected_item)
        if len(keys) == 1:  # Remove from root
            del data[keys[0]]
        else:  # Remove from a nested dictionary
            nested_dict = get_nested_dict(data, keys[:-1])
            del nested_dict[keys[-1]]

        tree.delete(selected_item)  # Remove the item directly from the tree
        if parent_id:
            tree.selection_set(parent_id)  # Keep the focus on the parent
    except IndexError:
        messagebox.showwarning("Errore", "Seleziona un elemento da rimuovere!")
def move_item_up():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Errore", "Seleziona un elemento da spostare!")
        return

    item_id = selected_item[0]
    parent_id = tree.parent(item_id)
    siblings = list(tree.get_children(parent_id))
    index = siblings.index(item_id)

    if index > 0:  # Only proceed if the item is not the first among its siblings
        swap_items_in_data(parent_id, index, index - 1)
        # Move the item in the treeview
        tree.move(item_id, parent_id, index - 1)
        tree.selection_set(item_id)


def move_item_down():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Errore", "Seleziona un elemento da spostare!")
        return

    item_id = selected_item[0]
    parent_id = tree.parent(item_id)
    siblings = list(tree.get_children(parent_id))
    index = siblings.index(item_id)

    if index < len(siblings) - 1:  # Only proceed if the item is not the last among its siblings
        swap_items_in_data(parent_id, index, index + 1)
        # Move the item in the treeview
        tree.move(item_id, parent_id, index + 1)
        tree.selection_set(item_id)

def swap_items_in_data(parent_id, index1, index2):
    """Helper function to swap items in the actual data dictionary."""
    if parent_id == "":  # Root-level items
        keys_at_root = list(data.keys())
        key1, key2 = keys_at_root[index1], keys_at_root[index2]
        data[key1], data[key2] = data[key2], data[key1]
    else:  # Nested items
        keys = get_full_key_path(parent_id)
        parent_dict = get_nested_dict(data, keys)
        keys_at_level = list(parent_dict.keys())
        key1, key2 = keys_at_level[index1], keys_at_level[index2]
        parent_dict[key1], parent_dict[key2] = parent_dict[key2], parent_dict[key1]

def get_expanded_nodes(tree):
    expanded_nodes = []
    def collect_expanded(node):
        if tree.item(node, "open"):
            expanded_nodes.append(node)
        for child in tree.get_children(node):
            collect_expanded(child)
    collect_expanded("")  # Start from the root
    return expanded_nodes

def restore_expanded_nodes(tree, expanded_nodes):
    for node in expanded_nodes:
        if tree.exists(node):
            tree.item(node, open=True)

def update_treeview():
    expanded_nodes = get_expanded_nodes(tree)  # Save expanded state
    tree.delete(*tree.get_children())
    display_tree(data)
    restore_expanded_nodes(tree, expanded_nodes)  # Restore expanded state

def display_tree(d, parent=""):
    for key, value in d.items():
        add_tree_item(parent, key, value)

def add_tree_item(parent, key, value):
    if isinstance(value, dict):
        node_id = tree.insert(parent, "end", text=key, values=["(dict)"])
        for sub_key, sub_value in value.items():
            add_tree_item(node_id, sub_key, sub_value)
    elif isinstance(value, list):
        node_id = tree.insert(parent, "end", text=key, values=["(list)"])
        for i, item in enumerate(value):
            add_tree_item(node_id, f"[{i}]", item)
    else:
        tree.insert(parent, "end", text=key, values=[repr(value)])

def get_full_key_path(node_id):
    path = []
    while node_id:
        path.insert(0, tree.item(node_id, "text"))
        node_id = tree.parent(node_id)
    return path

def get_nested_dict(d, keys):
    for key in keys:
        d = d[key]
    return d

def save_json():
    if not data:
        messagebox.showwarning("Errore", "Non ci sono dati da salvare!")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        messagebox.showinfo("Salvato", "File JSON salvato con successo!")

def load_json():
    global data
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])

    if file_path and os.path.splitext(file_path)[1] == ".json":
        try:
            with open(file_path, 'r') as file:
                loaded_data = json.load(file)
                if isinstance(loaded_data, dict):
                    data = loaded_data
                    update_treeview()
                    messagebox.showinfo("Caricato", "File JSON caricato con successo!")
                else:
                    messagebox.showerror("Errore", "Il file JSON deve contenere un oggetto di tipo dizionario!")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il caricamento del file JSON: {e}")
    else:
        messagebox.showwarning("Errore", "Seleziona un file JSON valido!")
    
def deselect_item(event):
    tree.selection_remove(tree.selection())


# Data storage
data = {}

# GUI Setup
root = tk.Tk()
root.title("JSON Builder con Visualizzazione ad Albero")

# Main frame
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill="both", expand=True)

# Key and value entry fields
tk.Label(frame, text="Chiave:").grid(row=0, column=0, sticky=tk.W)
key_entry = tk.Entry(frame, width=30)
key_entry.grid(row=0, column=1, sticky="ew")

tk.Label(frame, text="Valore (stringa, numero, lista, dizionario):").grid(row=1, column=0, sticky=tk.W)
value_entry = tk.Entry(frame, width=30)
value_entry.grid(row=1, column=1, sticky="ew")

# Add and remove buttons
add_button = tk.Button(frame, text="Aggiungi", command=add_entry)
add_button.grid(row=2, column=0, pady=5)

remove_button = tk.Button(frame, text="Rimuovi selezionato", command=remove_entry)
remove_button.grid(row=2, column=1, pady=5)

# Treeview and scrollbar
tree = ttk.Treeview(frame, columns=("Type"), show="tree")
tree.heading("#0", text="Chiave")
tree.heading("Type", text="Tipo")
tree.grid(row=3, column=0, columnspan=2, pady=5, sticky="nsew")

tree_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
tree_scrollbar.grid(row=3, column=2, sticky="ns")
tree.configure(yscrollcommand=tree_scrollbar.set)

# Buttons for file operations
load_button = tk.Button(frame, text="Carica JSON", command=load_json)
load_button.grid(row=4, column=1, pady=5, sticky="ew")

save_button = tk.Button(frame, text="Salva come JSON", command=save_json)
save_button.grid(row=5, column=1, pady=5, sticky="ew")

# Buttons to move items
up_button = tk.Button(frame, text="Sposta Su", command=move_item_up)
up_button.grid(row=4, column=0, pady=5, sticky="ew")

down_button = tk.Button(frame, text="Sposta Giù", command=move_item_down)
down_button.grid(row=5, column=0, pady=5, sticky="ew")

# Label to display the value of the hovered item
hover_label = tk.Label(root, text="Hover over an item to see its value", fg="blue", padx=10, pady=5)
hover_label.pack(side=tk.BOTTOM, fill="x")

# Function to update hover label
def show_hover_value(event):
    item_id = tree.identify_row(event.y)
    if item_id:
        keys = get_full_key_path(item_id)
        try:
            value = get_nested_dict(data, keys)
            hover_label.config(text=f"{repr(value)}") # config the displayed value
        except KeyError:
            hover_label.config(text="Value: Not found")
    else:
        hover_label.config(text="Hover over an item to see its value")

# Bind mouse motion to the Treeview
tree.bind("<Motion>", show_hover_value)

# Configure resizing behavior
frame.grid_rowconfigure(3, weight=1)  # Allow the Treeview to expand vertically
frame.grid_columnconfigure(0, weight=1)  # Allow column 0 (Treeview) to expand
frame.grid_columnconfigure(1, weight=1)  # Allow column 1 (Treeview) to expand

# Bind Enter key to buttons
bind_enter_to_buttons(root)

# Deselect item when clicking outside any node
tree.bind("<Button-1>", deselect_item)

root.mainloop()
