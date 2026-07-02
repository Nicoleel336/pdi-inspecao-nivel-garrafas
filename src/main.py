import os
import csv
import cv2

# Definições de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
OUTPUT_INTERMEDIARIOS_DIR = os.path.join(BASE_DIR, "outputs", "intermediarios")
LABELS_PATH = os.path.join(BASE_DIR, "labels.csv")

# Definição das coordenadas da Região de Interesse (ROI)
# Resolução original das imagens: 902 (largura) x 1600 (altura)
ROI_Y_MIN = 200
ROI_Y_MAX = 1400
ROI_X_MIN = 150
ROI_X_MAX = 650

def inicializar_diretorios():
    """Garante que os diretórios de saída existam."""
    os.makedirs(OUTPUT_INTERMEDIARIOS_DIR, exist_ok=True)

def processar_pipeline():
    """Executa o pipeline de processamento de imagens (ROI, Conversão para cinza)."""
    inicializar_diretorios()
    
    if not os.path.exists(LABELS_PATH):
        print(f"Erro: Arquivo de rótulos não encontrado em {LABELS_PATH}")
        return
        
    with open(LABELS_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['arquivo']
            img_path = os.path.join(DATASET_DIR, filename)
            
            # 1. Carregar imagem
            img = cv2.imread(img_path)
            if img is None:
                print(f"Erro ao carregar imagem: {img_path}")
                continue
                
            # 2. Recortar a Região de Interesse (ROI)
            # No numpy, o fatiamento é [Y, X]
            roi = img[ROI_Y_MIN:ROI_Y_MAX, ROI_X_MIN:ROI_X_MAX]
            
            # Salvar imagem da ROI
            roi_output_name = f"roi_{filename}"
            roi_output_path = os.path.join(OUTPUT_INTERMEDIARIOS_DIR, roi_output_name)
            cv2.imwrite(roi_output_path, roi)
            
            # 3. Conversão para escala de cinza
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Salvar imagem em escala de cinza
            gray_output_name = f"cinza_{filename}"
            gray_output_path = os.path.join(OUTPUT_INTERMEDIARIOS_DIR, gray_output_name)
            
            success = cv2.imwrite(gray_output_path, gray)
            if success:
                print(f"Processado: {filename} (ROI e Cinza salvos)")
            else:
                print(f"Erro ao salvar saídas para {filename}")

if __name__ == "__main__":
    print("Iniciando o pipeline de processamento...")
    processar_pipeline()
    print("Pipeline de processamento finalizado.")
