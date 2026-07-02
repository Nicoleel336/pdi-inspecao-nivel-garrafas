import os
import sys
import json

# Adicionar o diretório src ao path do Python para permitir importação direta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from deteccao import detectar_linha_liquido

# Definições de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_MASCARAS_DIR = os.path.join(BASE_DIR, "outputs", "mascaras")
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "outputs", "calibracao.json")

# Nomes das imagens de calibração
IMG_LIM_INF = "08_limInf.jpeg"
IMG_LIM_SUP = "13_limSup.jpeg"

def executar_calibracao():
    """Detecta as coordenadas de y_limInf e y_limSup e as salva em um arquivo JSON."""
    mask_inf_path = os.path.join(INPUT_MASCARAS_DIR, f"mascara_morfologica_{IMG_LIM_INF}")
    mask_sup_path = os.path.join(INPUT_MASCARAS_DIR, f"mascara_morfologica_{IMG_LIM_SUP}")
    
    if not os.path.exists(mask_inf_path):
        print(f"Erro: Máscara para limite inferior não encontrada em {mask_inf_path}")
        return
        
    if not os.path.exists(mask_sup_path):
        print(f"Erro: Máscara para limite superior não encontrada em {mask_sup_path}")
        return
        
    # Detectar y para limite inferior
    y_limInf = detectar_linha_liquido(mask_inf_path)
    # Detectar y para limite superior
    y_limSup = detectar_linha_liquido(mask_sup_path)
    
    if y_limInf is None or y_limSup is None:
        print("Erro: Não foi possível detectar a linha do líquido em uma ou ambas as imagens de calibração.")
        return
        
    print("--- Resultados da Calibração ---")
    print(f"Limite Inferior (y_limInf) em {IMG_LIM_INF}: y = {y_limInf}")
    print(f"Limite Superior (y_limSup) em {IMG_LIM_SUP}: y = {y_limSup}")
    
    # Validação do sentido vertical
    if y_limSup >= y_limInf:
        print("Aviso: Sentido vertical inesperado (y_limSup deve ser menor que y_limInf na coordenada de imagem).")
    else:
        print("Validação de coordenadas: OK (y_limSup < y_limInf).")
        
    # Salvar em JSON
    dados_calibracao = {
        "y_limInf": int(y_limInf),
        "y_limSup": int(y_limSup)
    }
    
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    with open(OUTPUT_JSON_PATH, mode='w', encoding='utf-8') as f:
        json.dump(dados_calibracao, f, indent=4)
        
    print(f"Calibração salva com sucesso em: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    print("Iniciando a etapa de calibração dos limites...")
    executar_calibracao()
    print("Etapa de calibração finalizada.")
