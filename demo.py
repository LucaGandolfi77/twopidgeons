import os
from PIL import Image, ImageDraw
from twopidgeons.node import Node

def create_dummy_image(filename):
    """Crea un'immagine JPEG di test."""
    img = Image.new('RGB', (100, 100), color = 'red')
    d = ImageDraw.Draw(img)
    d.text((10,10), "Hello World", fill=(255,255,0))
    img.save(filename, format='JPEG')

def main():
    # 1. Setup ambiente
    print("--- Inizializzazione Nodo ---")
    node = Node(node_id="nodo_alpha", storage_dir="./node_storage")
    
    # Creiamo un'immagine sorgente temporanea
    source_img = "temp_source.jpg"
    create_dummy_image(source_img)

    # 2. Test nome file non valido
    print("\n--- Test 1: Nome file non valido ---")
    node.store_image(source_img, "wrongname.2pg") # Troppo lungo
    node.store_image(source_img, "abc.2pg")       # Troppo corto
    node.store_image(source_img, "ABCDE.2pg")     # Maiuscolo

    # 3. Test caricamento valido
    print("\n--- Test 2: Caricamento valido (abcde.2pg) ---")
    valid_name = "abcde.2pg"
    success = node.store_image(source_img, valid_name)
    
    if success:
        print("Caricamento riuscito!")

    # 4. Test Validazione
    print("\n--- Test 3: Validazione Immagine ---")
    node.validate_local_image(valid_name)

    # 5. Test Manomissione
    print("\n--- Test 4: Rilevamento Manomissione ---")
    # Modifichiamo il file su disco manualmente
    target_path = os.path.join("./node_storage", valid_name)
    with open(target_path, "wb") as f:
        f.write(b"Dati corrotti non sono piu un'immagine")
    
    print("File manomesso su disco. Tentativo di validazione...")
    node.validate_local_image(valid_name)

    # Pulizia
    if os.path.exists(source_img):
        os.remove(source_img)

if __name__ == "__main__":
    main()
