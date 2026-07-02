import os
import sys
import csv
import cv2
import json
import numpy as np

# Adicionar o diretório src ao path do Python para permitir importação direta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from deteccao import detectar_linha_liquido

# Definições de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_ROI_DIR = os.path.join(BASE_DIR, "outputs", "intermediarios")
INPUT_MASCARAS_DIR = os.path.join(BASE_DIR, "outputs", "mascaras")
OUTPUT_FINAIS_DIR = os.path.join(BASE_DIR, "outputs", "finais")
CALIBRACAO_PATH = os.path.join(BASE_DIR, "outputs", "calibracao.json")
LABELS_PATH = os.path.join(BASE_DIR, "labels.csv")
RESULTADOS_PATH = os.path.join(BASE_DIR, "outputs", "resultados.csv")

# Parâmetros de Nível Útil da Garrafa
Y_TOPO_UTIL = 100
Y_BASE_UTIL = 1100
TOLERANCIA = 10

def inicializar_diretorios():
    """Garante que os diretórios de saída existam."""
    os.makedirs(OUTPUT_FINAIS_DIR, exist_ok=True)

def executar_classificacao():
    """Executa a classificação e o cálculo de nível para cada imagem e salva os resultados."""
    inicializar_diretorios()
    
    # 1. Carregar valores de calibração
    if not os.path.exists(CALIBRACAO_PATH):
        print(f"Erro: Arquivo de calibração não encontrado em {CALIBRACAO_PATH}. Rode a etapa de calibração primeiro.")
        return
        
    with open(CALIBRACAO_PATH, mode='r', encoding='utf-8') as f:
        calib = json.load(f)
        y_limInf = calib["y_limInf"]
        y_limSup = calib["y_limSup"]
        
    print(f"Calibração carregada: y_limSup={y_limSup}, y_limInf={y_limInf}")
    print(f"Tolerância aplicada: {TOLERANCIA} pixels")
    print("-" * 70)
    
    if not os.path.exists(LABELS_PATH):
        print(f"Erro: Arquivo de rótulos não encontrado em {LABELS_PATH}")
        return
        
    resultados = []
    
    with open(LABELS_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['arquivo']
            classe_real = row['classe_real']
            
            mask_name = f"mascara_morfologica_{filename}"
            mask_path = os.path.join(INPUT_MASCARAS_DIR, mask_name)
            roi_path = os.path.join(INPUT_ROI_DIR, f"roi_{filename}")
            
            # Carregar imagem ROI colorida
            roi_color = cv2.imread(roi_path)
            if roi_color is None:
                print(f"Erro ao carregar ROI: {roi_path}")
                continue
                
            # 2. Detectar y_liquido
            y_liquido = detectar_linha_liquido(mask_path)
            if y_liquido is None:
                print(f"Aviso: Nível não detectado para {filename}")
                continue
                
            # 3. Calcular Nível Normalizado
            # Garante que o nível fique entre 0 e 1
            nivel = (Y_BASE_UTIL - y_liquido) / (Y_BASE_UTIL - Y_TOPO_UTIL)
            nivel = max(0.0, min(1.0, nivel))
            
            # 4. Classificação com Tolerância
            if y_liquido > y_limInf + TOLERANCIA:
                classe_prevista = "abaixo"
            elif y_liquido < y_limSup - TOLERANCIA:
                classe_prevista = "acima"
            else:
                classe_prevista = "ok"
                
            resultados.append({
                "arquivo": filename,
                "classe_real": classe_real,
                "y_detectado": y_liquido,
                "nivel_detectado": round(nivel, 4),
                "classe_prevista": classe_prevista
            })
            
            # 5. Desenhar e Anotar Imagem
            height, width, _ = roi_color.shape
            
            # Linhas de Limites de Calibração (Vermelho)
            cv2.line(roi_color, (0, y_limInf), (width, y_limInf), (0, 0, 255), 2)
            cv2.line(roi_color, (0, y_limSup), (width, y_limSup), (0, 0, 255), 2)
            cv2.putText(roi_color, "Min", (5, y_limInf - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(roi_color, "Max", (5, y_limSup - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Linha do Líquido Detectada (Azul)
            cv2.line(roi_color, (0, y_liquido), (width, y_liquido), (255, 0, 0), 3)
            
            # Texto da Classe e Porcentagem de Preenchimento (Verde se OK, Amarelo se fora do limite)
            cor_texto = (0, 255, 0) if classe_prevista == "ok" else (0, 255, 255)
            texto_info = f"Nivel: {nivel*100:.1f}% ({classe_prevista.upper()})"
            cv2.putText(roi_color, texto_info, (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_texto, 2)
            cv2.putText(roi_color, f"y={y_liquido}", (15, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor_texto, 1)
            
            # Salvar imagem final na pasta outputs/finais/
            output_path = os.path.join(OUTPUT_FINAIS_DIR, f"final_{filename}")
            cv2.imwrite(output_path, roi_color)
            
    # 6. Salvar os resultados em CSV
    with open(RESULTADOS_PATH, mode='w', newline='', encoding='utf-8') as f:
        fieldnames = ["arquivo", "classe_real", "y_detectado", "nivel_detectado", "classe_prevista"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resultados)
        
    # 7. Exibir tabela resumo
    print(f"{'Arquivo':<25} | {'Classe Real':<12} | {'Y Detectado':<12} | {'Nível %':<9} | {'Classe Prevista':<15}")
    print("-" * 75)
    for r in resultados:
        nivel_pct = f"{r['nivel_detectado']*100:.1f}%"
        print(f"{r['arquivo']:<25} | {r['classe_real']:<12} | {r['y_detectado']:<12} | {nivel_pct:<9} | {r['classe_prevista']:<15}")
        
    print("-" * 75)
    print(f"Resultados de classificação salvos em: {RESULTADOS_PATH}")

if __name__ == "__main__":
    print("Iniciando a classificação e o cálculo de nível normalizado...")
    executar_classificacao()
    print("Etapa de classificação finalizada.")
