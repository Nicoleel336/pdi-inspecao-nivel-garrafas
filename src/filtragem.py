import os
import csv
import cv2
import numpy as np

# Definições de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CINZAS_DIR = os.path.join(BASE_DIR, "outputs", "intermediarios", "cinzas")
OUTPUT_FILTRADAS_DIR = os.path.join(BASE_DIR, "outputs", "intermediarios", "filtradas")
OUTPUT_MASCARAS_DIR = os.path.join(BASE_DIR, "outputs", "mascaras")
OUTPUT_MORFOLOGICO_DIR = os.path.join(BASE_DIR, "outputs", "morfologico")
OUTPUT_ABERTURA_DIR = os.path.join(OUTPUT_MORFOLOGICO_DIR, "abertura")
OUTPUT_ABERTURA_FECHAMENTO_DIR = os.path.join(OUTPUT_MORFOLOGICO_DIR, "abertura_fechamento")
LABELS_PATH = os.path.join(BASE_DIR, "labels.csv")

def inicializar_diretorios():
    """Garante que os diretórios de saída existam."""
    os.makedirs(OUTPUT_FILTRADAS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_MASCARAS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_ABERTURA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_ABERTURA_FECHAMENTO_DIR, exist_ok=True)

def aplicar_pipeline_filtragem():
    """Lê as imagens em escala de cinza, aplica o filtro de mediana, binariza e aplica morfologia."""
    inicializar_diretorios()
    
    if not os.path.exists(LABELS_PATH):
        print(f"Erro: Arquivo de rótulos não encontrado em {LABELS_PATH}")
        return
        
    with open(LABELS_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['arquivo']
            gray_img_name = f"cinza_{filename}"
            gray_img_path = os.path.join(INPUT_CINZAS_DIR, gray_img_name)
            
            # 1. Carregar imagem em escala de cinza
            gray = cv2.imread(gray_img_path, cv2.IMREAD_GRAYSCALE)
            if gray is None:
                print(f"Erro ao carregar imagem em escala de cinza: {gray_img_path}")
                continue
            
            # 2. Filtragem com Filtro de Mediana (Kernel 5x5)
            filtered = cv2.medianBlur(gray, 5)
            
            # Salvar imagem filtrada
            filtered_output_name = f"filtrada_{filename}"
            filtered_output_path = os.path.join(OUTPUT_FILTRADAS_DIR, filtered_output_name)
            cv2.imwrite(filtered_output_path, filtered)
            
            # 3. Limiarização de Otsu invertida (Segmentação)
            _, thresh = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Salvar máscara binária direta na pasta "mascaras"
            mask_bin_name = f"mascara_binaria_{filename}"
            mask_bin_path = os.path.join(OUTPUT_MASCARAS_DIR, mask_bin_name)
            cv2.imwrite(mask_bin_path, thresh)
            
            # 4. Operações Morfológicas (Melhoria da máscara)
            # Abertura com kernel retangular 5x3
            kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
            opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_open)
            
            # Salvar resultado apenas da abertura
            abertura_name = f"abertura_{filename}"
            abertura_path = os.path.join(OUTPUT_ABERTURA_DIR, abertura_name)
            cv2.imwrite(abertura_path, opened)
            
            # Seleção do componente inferior principal (líquido na garrafa)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(opened)
            component_mask = np.zeros_like(opened)
            
            if num_labels > 1:
                # Filtrar componentes por área mínima para evitar ruídos minúsculos
                min_area = 500
                candidates = []
                for i in range(1, num_labels):
                    area = stats[i, cv2.CC_STAT_AREA]
                    if area >= min_area:
                        candidates.append(i)
                
                # Caso nenhum atinja o limite, considerar todos os candidatos do primeiro plano
                if not candidates:
                    candidates = list(range(1, num_labels))
                
                if candidates:
                    # O componente inferior principal é aquele que se estende mais abaixo no eixo Y (maior top + height)
                    best_label = max(candidates, key=lambda i: stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT])
                    component_mask[labels == best_label] = 255
            
            # Fechamento horizontal com kernel retangular 21x5
            kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 5))
            closed = cv2.morphologyEx(component_mask, cv2.MORPH_CLOSE, kernel_close)
            
            # Salvar resultado final de abertura + seleção + fechamento
            abertura_fechamento_name = f"abertura_fechamento_{filename}"
            abertura_fechamento_path = os.path.join(OUTPUT_ABERTURA_FECHAMENTO_DIR, abertura_fechamento_name)
            
            # Também salvar como a mascara_morfologica final na pasta "mascaras"
            mask_morph_name = f"mascara_morfologica_{filename}"
            mask_morph_path = os.path.join(OUTPUT_MASCARAS_DIR, mask_morph_name)
            cv2.imwrite(mask_morph_path, closed)
            
            success = cv2.imwrite(abertura_fechamento_path, closed)
            if success:
                print(f"Processado: {filename} (Abertura 5x3, Seleção Componente Inferior e Fechamento 21x5 concluídos)")
            else:
                print(f"Erro ao salvar saídas morfológicas para {filename}")

if __name__ == "__main__":
    print("Iniciando a etapa de filtragem e segmentação...")
    aplicar_pipeline_filtragem()
    print("Etapa de filtragem e segmentação finalizada.")
