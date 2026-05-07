import math
from gerbonara import GerberFile
import serial

# ==========================================
# USTAWIENIA MASZYNY ASYMTEK (ACL) I PASTY
# ==========================================
TIME_PER_SQMM = 1.0  # [sekundy/mm²] Czas włączenia zaworu na 1 mm² powierzchni
Z_OFFSET_PER_SEC = 0.2  # [mm/sekundę] Wysokość igły nad płytką na 1 s podawania
Z_SAFE_HEIGHT = 100.0  # [mm] Wysokość bezpieczna przelotu igły (0.5 cm = 5.0 mm)
STEPSXY_PER_MM = 100 # [mm] Ilość króków na mm XY
STEPSZ_PER_MM = 100 # [mm] Ilość kroków na mm Z
# ==========================================
# USTAWIENIA SERIAL PORT
# ==========================================

# ==========================================
def get_aperture_area(aperture):
    """Oblicza pole powierzchni narzędzia (apertury) w mm²."""
    shape_name = type(aperture).__name__
    if shape_name == 'CircleAperture':
        diameter = getattr(aperture, 'diameter', getattr(aperture, 'd', 0))
        r = diameter / 2.0
        return math.pi * (r ** 2)
    elif shape_name == 'RectangleAperture':
        return aperture.w * aperture.h
    elif shape_name == 'ObroundAperture':
        w, h = aperture.w, aperture.h
        r = min(w, h) / 2.0
        if w > h:
            return (w - h) * h + math.pi * (r ** 2)
        else:
            return w * (h - w) + math.pi * (r ** 2)
    else:
        return 0.0


# Wczytanie pliku gerber
layer = GerberFile.open('rekawiczka_Paste_Top.gbr')

# START PROGRAMU MASZYNY
print(f"MA 0, 0; AZ {Z_SAFE_HEIGHT:.3f};")

for obj in layer.objects:
    if type(obj).__name__ == 'Flash':
        x = obj.x * STEPSXY_PER_MM
        y = obj.y * STEPSXY_PER_MM
        area = get_aperture_area(obj.aperture)

        # Ignoruj błyski bez powierzchni
        if area <= 0:
            continue

        # --- OBLICZENIA DLA PASTY ---
        dispense_time_sec = area * TIME_PER_SQMM
        z_dispense_height = - dispense_time_sec * Z_OFFSET_PER_SEC * STEPSZ_PER_MM
        delay = dispense_time_sec

        # --- GENEROWANIE KODU ACL ---
        # 1. Przejazd XY nad pad (Z zostaje na bezpiecznym Z_SAFE_HEIGHT)
        print(f"MA {x:.3f}, {y:.3f};")

        # 2. Zjazd w dół na wyliczoną wysokość podawania pasty
        print(f"AZ {z_dispense_height:.3f};")

        # 3. Włączenie zaworu
        print("CD2;")

        # 4. Oczekiwanie
        print(f"WA {delay:.3f};")

        # 5. Wyłączenie zaworu
        print("CD0;")

        # 6. Podniesienie igły z powrotem na bezpieczną wysokość przed kolejnym ruchem
        print(f"AZ {Z_SAFE_HEIGHT:.3f};")

# KONIEC PROGRAMU
print(f"MA 0, 0; AZ {Z_SAFE_HEIGHT:.3f};")