import os
import csv
import cv2

# Definições de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CINZAS_DIR = os.path.join(BASE_DIR, "outputs", "intermediarios", "cinzas")
OUTPUT_FILTRADAS_DIR = os.path.join(BASE_DIR, "outputs", "intermediarios", "filtradas")
OUTPUT_MASCARAS_DIR = os.path.join(BASE_DIR, "outputs", "mascaras")
LABELS_PATH = os.path.join(BASE_DIR, "labels.csv")

def inicializar_diretorios():
    """Garante que os diretórios de saída existam."""
    os.makedirs(OUTPUT_FILTRADAS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_MASCARAS_DIR, exist_ok=True)

def aplicar_pipeline_filtragem():
    """Lê as imagens em escala de cinza, aplica o filtro de mediana e gera as máscaras."""
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
            # Escolhido para eliminar ruídos mantendo as bordas nítidas
            filtered = cv2.medianBlur(gray, 5)
            
            # Salvar imagem filtrada
            filtered_output_name = f"filtrada_{filename}"
            filtered_output_path = os.path.join(OUTPUT_FILTRADAS_DIR, filtered_output_name)
            cv2.imwrite(filtered_output_path, filtered)
            
            # 3. Limiarização de Otsu invertida (Segmentação)
            _, thresh = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Salvar máscara binária direta
            mask_bin_name = f"mascara_binaria_{filename}"
            mask_bin_path = os.path.join(OUTPUT_MASCARAS_DIR, mask_bin_name)
            cv2.imwrite(mask_bin_path, thresh)
            
            # 4. Operações Morfológicas (Melhoria da máscara)
            # Abertura para eliminar pequenos ruídos isolados fora do líquido
            kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_open)
            
            # Fechamento para preencher falhas internas no líquido devido a reflexos
            kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close)
            
            # Salvar máscara morfológica final
            mask_morph_name = f"mascara_morfologica_{filename}"
            mask_morph_path = os.path.join(OUTPUT_MASCARAS_DIR, mask_morph_name)
            
            success = cv2.imwrite(mask_morph_path, closed)
            if success:
                print(f"Processado: {filename} (Filtro Mediana 5x5 e Máscaras salvos)")
            else:
                print(f"Erro ao salvar máscaras para {filename}")

if __name__ == "__main__":
    print("Iniciando a etapa de filtragem e segmentação...")
    aplicar_pipeline_filtragem()
    print("Etapa de filtragem e segmentação finalizada.")
