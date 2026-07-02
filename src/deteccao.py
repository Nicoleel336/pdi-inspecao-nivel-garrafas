import os
import csv
import cv2
import numpy as np

# Definições de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_ROI_DIR = os.path.join(BASE_DIR, "outputs", "intermediarios")
INPUT_MASCARAS_DIR = os.path.join(BASE_DIR, "outputs", "mascaras")
OUTPUT_FINAIS_DIR = os.path.join(BASE_DIR, "outputs", "finais")
LABELS_PATH = os.path.join(BASE_DIR, "labels.csv")

def inicializar_diretorios():
    """Garante que os diretórios de saída existam."""
    os.makedirs(OUTPUT_FINAIS_DIR, exist_ok=True)

def detectar_linha_liquido(mask_path):
    """
    Detecta a linha superior do líquido por projeção horizontal na região central da máscara.
    Busca a primeira linha que inicia uma sequência de 10 linhas consecutivas com mais de 50% de pixels brancos.
    """
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return None
        
    height, width = mask.shape
    x_start = int(0.15 * width)
    x_end = int(0.85 * width)
    checked_width = x_end - x_start
    min_white_pixels = int(0.50 * checked_width)
    consecutive_needed = 10
    
    y_liquido = None
    for y in range(height - consecutive_needed):
        all_valid = True
        for offset in range(consecutive_needed):
            row = mask[y + offset, x_start:x_end]
            white_count = np.sum(row == 255)
            if white_count < min_white_pixels:
                all_valid = False
                break
        if all_valid:
            y_liquido = y
            break
            
    return y_liquido

def executar_deteccao():
    """Processa todas as imagens do dataset detectando a linha e salvando a visualização."""
    inicializar_diretorios()
    
    if not os.path.exists(LABELS_PATH):
        print(f"Erro: Arquivo de rótulos não encontrado em {LABELS_PATH}")
        return
        
    with open(LABELS_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['arquivo']
            mask_name = f"mascara_morfologica_{filename}"
            mask_path = os.path.join(INPUT_MASCARAS_DIR, mask_name)
            roi_path = os.path.join(INPUT_ROI_DIR, f"roi_{filename}")
            
            # 1. Carregar ROI colorida
            roi_color = cv2.imread(roi_path)
            if roi_color is None:
                print(f"Erro ao carregar ROI: {roi_path}")
                continue
                
            # 2. Detectar y_liquido
            y_liquido = detectar_linha_liquido(mask_path)
            
            if y_liquido is not None:
                print(f"Imagem {filename}: Linha do líquido detectada em y = {y_liquido}")
                
                # 3. Desenhar a linha do líquido detectada
                # Desenha uma linha azul horizontal com espessura de 3 pixels
                cv2.line(roi_color, (0, y_liquido), (roi_color.shape[1], y_liquido), (255, 0, 0), 3)
                
                # Salvar a imagem final na pasta outputs/finais
                output_path = os.path.join(OUTPUT_FINAIS_DIR, f"final_{filename}")
                success = cv2.imwrite(output_path, roi_color)
                if not success:
                    print(f"Erro ao salvar imagem final para {filename}")
            else:
                print(f"Imagem {filename}: Nenhuma linha de líquido detectada.")

if __name__ == "__main__":
    print("Iniciando a etapa de detecção da linha do líquido...")
    executar_deteccao()
    print("Etapa de detecção finalizada.")
