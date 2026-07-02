import os
import csv
import json
import numpy as np

# Definições de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTADOS_PATH = os.path.join(BASE_DIR, "outputs", "resultados.csv")
OUTPUT_PLOT_PATH = os.path.join(BASE_DIR, "matriz_confusao.png")

def calcular_metricas():
    if not os.path.exists(RESULTADOS_PATH):
        print(f"Erro: Arquivo de resultados não encontrado em {RESULTADOS_PATH}. Rode a etapa de classificação primeiro.")
        return None
        
    resultados = []
    with open(RESULTADOS_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            resultados.append(row)
            
    total = len(resultados)
    if total == 0:
        print("Erro: Nenhum resultado encontrado no arquivo CSV.")
        return None
        
    # --- 1. Acurácia Geral (Multiclasse) ---
    acertos_multiclasse = sum(1 for r in resultados if r['classe_real'] == r['classe_prevista'])
    acuracia_multiclasse = acertos_multiclasse / total
    
    # --- 2. Matriz de Confusão Multiclasse ---
    labels_multi = ["abaixo", "ok", "acima"]
    idx_multi = {label: i for i, label in enumerate(labels_multi)}
    conf_multi = np.zeros((3, 3), dtype=int)
    
    for r in resultados:
        real_label = r['classe_real']
        prev_label = r['classe_prevista']
        conf_multi[idx_multi[real_label], idx_multi[prev_label]] += 1
        
    # --- 3. Acurácia Binária ---
    # Mapeamento: "ok" -> "OK", "abaixo"/"acima" -> "Defeituosa"
    acertos_binario = 0
    for r in resultados:
        real_bin = "OK" if r['classe_real'] == "ok" else "Defeituosa"
        prev_bin = "OK" if r['classe_prevista'] == "ok" else "Defeituosa"
        if real_bin == prev_bin:
            acertos_binario += 1
    acuracia_binaria = acertos_binario / total
    
    # --- 4. Matriz de Confusão Binária ---
    labels_bin = ["OK", "Defeituosa"]
    idx_bin = {label: i for i, label in enumerate(labels_bin)}
    conf_bin = np.zeros((2, 2), dtype=int)
    
    for r in resultados:
        real_bin = "OK" if r['classe_real'] == "ok" else "Defeituosa"
        prev_bin = "OK" if r['classe_prevista'] == "ok" else "Defeituosa"
        conf_bin[idx_bin[real_bin], idx_bin[prev_bin]] += 1
        
    # Exibir no Console
    print("==================================================")
    print("            RELATÓRIO DE AVALIAÇÃO                ")
    print("==================================================")
    print(f"Total de imagens testadas: {total}")
    print(f"Acurácia Geral (Multiclasse): {acuracia_multiclasse * 100:.2f}% ({acertos_multiclasse}/{total})")
    print(f"Acurácia Binária:             {acuracia_binaria * 100:.2f}% ({acertos_binario}/{total})")
    print("-" * 50)
    
    print("\nMatriz de Confusão Multiclasse (Real \\ Previsto):")
    print(f"{'':<10} | {'Abaixo':<8} | {'OK':<8} | {'Acima':<8}")
    print("-" * 42)
    for i, label in enumerate(labels_multi):
        print(f"{label.capitalize():<10} | {conf_multi[i, 0]:<8} | {conf_multi[i, 1]:<8} | {conf_multi[i, 2]:<8}")
        
    print("\nMatriz de Confusão Binária (Real \\ Previsto):")
    print(f"{'':<11} | {'OK':<10} | {'Defeituosa':<10}")
    print("-" * 38)
    for i, label in enumerate(labels_bin):
        print(f"{label:<11} | {conf_bin[i, 0]:<10} | {conf_bin[i, 1]:<10}")
    print("==================================================")
    
    return conf_multi, labels_multi, conf_bin, labels_bin

def plotar_matrizes(conf_multi, labels_multi, conf_bin, labels_bin):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nAviso: Matplotlib não está instalado. Não foi possível gerar 'matriz_confusao.png'.")
        print("Para instalar, execute: pip install matplotlib")
        return
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    def plot_matrix(ax, matrix, labels, title):
        im = ax.imshow(matrix, cmap="Blues", interpolation="nearest")
        ax.set_title(title, fontsize=12, fontweight="bold", pad=15)
        
        # Color bar
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        
        # Ticks e labels
        tick_marks = np.arange(len(labels))
        ax.set_xticks(tick_marks)
        ax.set_xticklabels(labels)
        ax.set_yticks(tick_marks)
        ax.set_yticklabels(labels)
        
        ax.set_xlabel("Classe Prevista", fontsize=10, labelpad=10)
        ax.set_ylabel("Classe Real", fontsize=10, labelpad=10)
        
        # Valores nas células
        thresh = matrix.max() / 2.0
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                color = "white" if matrix[i, j] > thresh else "black"
                ax.text(j, i, format(matrix[i, j], 'd'),
                        ha="center", va="center",
                        color=color, fontsize=12, fontweight="bold")
                        
    # Plotar as duas matrizes
    plot_matrix(ax1, conf_multi, [l.capitalize() for l in labels_multi], "Matriz de Confusão Multiclasse")
    plot_matrix(ax2, conf_bin, labels_bin, "Matriz de Confusão Binária")
    
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT_PATH, dpi=150)
    plt.close()
    print(f"\nGráficos das Matrizes de Confusão salvos em: {OUTPUT_PLOT_PATH}")

if __name__ == "__main__":
    res = calcular_metricas()
    if res:
        plotar_matrizes(*res)
