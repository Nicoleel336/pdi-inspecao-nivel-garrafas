# Pipeline do Projeto — Inspeção Automática do Nível de Preenchimento de Garrafas

## 1. Tema do trabalho

**Tema escolhido:** Inspeção de qualidade automática em linhas de produção.

**Aplicação específica:** Detecção automática do nível de preenchimento de garrafas.

O objetivo do sistema é simular uma inspeção visual industrial capaz de classificar garrafas de acordo com o nível do líquido presente em seu interior.

A classificação proposta é:

| Situação observada | Classe multiclasse | Classe binária |
|---|---|---|
| Líquido abaixo do limite mínimo aceitável | Abaixo | Defeituosa |
| Líquido dentro da faixa aceitável | OK | OK |
| Líquido acima do limite máximo aceitável | Acima | Defeituosa |

A versão multiclasse permite identificar o tipo de erro. A versão binária pode ser derivada posteriormente, agrupando as classes `Abaixo` e `Acima` como `Defeituosa`.

---

## 2. Organização do dataset

O dataset foi criado com fotos próprias de garrafas sob condições semelhantes de iluminação, fundo e posição da câmera.

A organização sugerida dos arquivos é:

| Arquivos | Interpretação | Classe real |
|---|---|---|
| `01_abaixo.jpeg` até `07_abaixo.jpeg` | Nível abaixo do limite mínimo | Abaixo |
| `08_limInf.jpeg` | Imagem de calibração do limite inferior | OK / Calibração |
| `09_noLimite.jpeg` até `12_noLimite.jpeg` | Nível dentro da faixa aceitável | OK |
| `13_limSup.jpeg` | Imagem de calibração do limite superior | OK / Calibração |
| `14_acima(analisar).jpeg` até `16_acima.jpeg` | Nível acima do limite máximo | Acima |

A imagem `08_limInf.jpeg` será usada para calibrar o menor nível ainda aceitável.

A imagem `13_limSup.jpeg` será usada para calibrar o maior nível ainda aceitável.

A imagem `14_acima(analisar).jpeg`, por aparentar ser um caso de borda, pode ser mantida no teste e discutida separadamente na análise dos resultados.

---

## 3. Estrutura sugerida de pastas

```text
projeto-garrafas/
│
├── dataset/
│   ├── 01_abaixo.jpeg
│   ├── 02_abaixo.jpeg
│   ├── 03_abaixo.jpeg
│   ├── 04_abaixo.jpeg
│   ├── 05_abaixo.jpeg
│   ├── 06_abaixo.jpeg
│   ├── 07_abaixo.jpeg
│   ├── 08_limInf.jpeg
│   ├── 09_noLimite.jpeg
│   ├── 10_noLimite.jpeg
│   ├── 11_noLimite.jpeg
│   ├── 12_noLimite.jpeg
│   ├── 13_limSup.jpeg
│   ├── 14_acima(analisar).jpeg
│   ├── 15_acima.jpeg
│   └── 16_acima.jpeg
│
├── outputs/
│   ├── intermediarios/
│   ├── mascaras/
│   └── finais/
│
├── labels.csv
├── resultados.csv
├── matriz_confusao.png
└── main.py
```

---

## 4. Arquivo de rótulos

Criar um arquivo `labels.csv` com as informações reais das imagens.

Exemplo:

```csv
arquivo,classe_real,uso
01_abaixo.jpeg,abaixo,teste
02_abaixo.jpeg,abaixo,teste
03_abaixo.jpeg,abaixo,teste
04_abaixo.jpeg,abaixo,teste
05_abaixo.jpeg,abaixo,teste
06_abaixo.jpeg,abaixo,teste
07_abaixo.jpeg,abaixo,teste
08_limInf.jpeg,ok,calibracao
09_noLimite.jpeg,ok,teste
10_noLimite.jpeg,ok,teste
11_noLimite.jpeg,ok,teste
12_noLimite.jpeg,ok,teste
13_limSup.jpeg,ok,calibracao
14_acima(analisar).jpeg,acima,teste
15_acima.jpeg,acima,teste
16_acima.jpeg,acima,teste
```

---

## 5. Ideia central do algoritmo

O sistema deve detectar a posição vertical da linha superior do líquido na garrafa.

Em imagens digitais, o eixo `y` cresce de cima para baixo. Portanto:

```text
y menor  → líquido mais alto na garrafa
y maior  → líquido mais baixo na garrafa
```

Isso é essencial para não inverter a classificação.

A lógica principal é:

```text
Detectar y_liquido
Comparar y_liquido com y_limSup e y_limInf
Classificar a garrafa
```

Onde:

- `y_liquido` é a posição vertical detectada da linha do líquido na imagem analisada;
- `y_limInf` é a posição vertical do nível mínimo aceitável;
- `y_limSup` é a posição vertical do nível máximo aceitável.

Como o nível superior fica mais alto na imagem, normalmente:

```text
y_limSup < y_limInf
```

---

## 6. Pipeline geral

O pipeline completo será:

```text
1. Entrada da imagem
2. Recorte da região de interesse da garrafa
3. Conversão para escala de cinza
4. Aplicação de filtro Gaussiano
5. Limiarização de Otsu invertida para segmentar o líquido escuro
6. Operação morfológica de abertura
7. Operação morfológica de fechamento
8. Detecção da linha superior do líquido
9. Cálculo do nível normalizado
10. Comparação com os limites calibrados
11. Classificação da garrafa
12. Geração dos resultados e da matriz de confusão
```

Representação em fluxo:

```text
Imagem original
        ↓
Recorte da ROI
        ↓
Conversão para tons de cinza
        ↓
Filtro Gaussiano
        ↓
Limiarização de Otsu invertida
        ↓
Abertura morfológica
        ↓
Fechamento morfológico
        ↓
Projeção horizontal da máscara
        ↓
Detecção de y_liquido
        ↓
Cálculo do nível
        ↓
Classificação
        ↓
Matriz de confusão
```

---

## 7. Etapa 1 — Entrada da imagem

Cada imagem do dataset será carregada individualmente.

A entrada é uma foto frontal da garrafa.

Condições desejadas:

- garrafa em posição aproximadamente vertical;
- fundo claro e relativamente uniforme;
- iluminação semelhante entre as imagens;
- líquido escuro ou colorido para gerar contraste;
- câmera em posição frontal.

---

## 8. Etapa 2 — Recorte da região de interesse

Como o ambiente simula uma linha de produção, é aceitável usar uma **região de interesse fixa**.

A região de interesse deve conter principalmente o corpo da garrafa, reduzindo a influência do fundo, bordas externas e partes irrelevantes.

Exemplo conceitual:

```text
Imagem inteira
        ↓
Recorte da região central da garrafa
        ↓
Processamento apenas da região útil
```

Justificativa para o relatório:

> Foi utilizada uma região de interesse fixa porque o sistema simula uma linha de produção com câmera posicionada frontalmente e produto aproximadamente alinhado. Essa estratégia reduz interferências do fundo e concentra o processamento na área onde o nível do líquido deve ser detectado.

---

## 9. Etapa 3 — Conversão para escala de cinza

Como o líquido usado nas imagens é escuro, a escala de cinza é suficiente para separar o líquido da região vazia da garrafa.

A imagem colorida é convertida para intensidade:

```text
Imagem RGB/BGR → Imagem em tons de cinza
```

Justificativa:

> A conversão para tons de cinza simplifica o processamento, pois o critério de segmentação depende principalmente da diferença de intensidade entre o líquido escuro e a parte vazia da garrafa.

---

## 10. Etapa 4 — Filtragem Mediana

A filtragem espacial será usada para suavizar pequenas variações locais.

Essas variações podem ser causadas por:

- ruído da câmera;
- textura do fundo;
- reflexos no plástico;
- bolhas ou pontos claros no líquido;
- pequenas irregularidades de iluminação.

Filtro recomendado:

```text
Filtro Mediana 5x5
```

Justificativa:

> O filtro Mediana foi escolhido porque preserva melhor as bordas do líquido em comparação com o filtro Gaussiano, além de ser eficaz na eliminação de ruídos do tipo "sal e pimenta", que são comuns em imagens com reflexos e variações de iluminação.

---

## 11. Etapa 5 — Segmentação do líquido

A segmentação tem como objetivo separar o líquido escuro do restante da imagem.

A técnica principal será:

```text
Limiarização de Otsu invertida
```

Como o líquido é escuro, a binarização invertida faz com que:

```text
Pixels escuros → branco na máscara
Pixels claros  → preto na máscara
```

Assim, a máscara ideal será:

```text
Região do líquido = branca
Fundo, vidro e região vazia = preto
```

Justificativa:

> O método de Otsu foi utilizado por calcular automaticamente um limiar a partir da distribuição de intensidades da imagem. A versão invertida foi adotada porque o líquido possui baixa intensidade em relação ao fundo e à parte vazia da garrafa.

---

## 12. Etapa 6 — Morfologia matemática

Após a segmentação, a máscara pode conter ruídos e falhas.

Dois problemas são esperados:

1. Pequenos pixels brancos fora da região do líquido.
2. Pequenos buracos pretos dentro da região do líquido, causados por reflexos.

Para tratar esses problemas, serão usadas abertura e fechamento.

### 12.1 Abertura

A abertura é uma erosão seguida de uma dilatação.

Função no projeto:

```text
Remover pequenos ruídos isolados fora da região principal do líquido.
```

Kernel sugerido:

```text
Elemento estruturante retangular 3x3 ou 5x5
```

### 12.2 Fechamento

O fechamento é uma dilatação seguida de uma erosão.

Função no projeto:

```text
Preencher pequenas falhas internas na região segmentada do líquido.
```

Kernel sugerido:

```text
Elemento estruturante retangular 7x7, 9x9 ou 15x5
```

### 12.3 Justificativa do elemento estruturante

> O elemento estruturante retangular foi escolhido porque a região do líquido ocupa uma faixa aproximadamente horizontal e compacta no corpo da garrafa. A abertura remove ruídos pequenos e o fechamento ajuda a preencher falhas causadas por reflexos e bolhas.

---

## 13. Etapa 7 — Detecção da linha superior do líquido

Após obter a máscara binária corrigida pela morfologia, o algoritmo deve detectar a primeira linha horizontal com presença significativa de líquido.

A técnica recomendada é a **projeção horizontal da máscara**.

Para cada linha da imagem, calcula-se a quantidade de pixels brancos:

```text
Linha 1   → poucos pixels brancos
Linha 2   → poucos pixels brancos
Linha 3   → poucos pixels brancos
Linha 100 → muitos pixels brancos  ← início do líquido
Linha 101 → muitos pixels brancos
Linha 102 → muitos pixels brancos
```

A primeira linha com quantidade suficiente de pixels brancos será considerada:

```text
y_liquido
```

Critério sugerido:

```text
Uma linha pertence ao líquido se possuir pelo menos X% de pixels brancos dentro da ROI.
```

Exemplo:

```text
Se largura da ROI = 300 pixels
E o limiar horizontal = 25%
Então uma linha deve ter pelo menos 75 pixels brancos para ser considerada líquido.
```

Esse critério evita que pequenos ruídos sejam confundidos com a linha do líquido.

---

## 14. Etapa 8 — Calibração dos limites

A calibração será feita usando duas imagens do próprio dataset.

### 14.1 Limite inferior

Imagem usada:

```text
08_limInf.jpeg
```

O algoritmo detecta a linha do líquido nessa imagem e salva:

```text
y_limInf
```

Esse valor representa o nível mínimo ainda aceitável.

### 14.2 Limite superior

Imagem usada:

```text
13_limSup.jpeg
```

O algoritmo detecta a linha do líquido nessa imagem e salva:

```text
y_limSup
```

Esse valor representa o nível máximo ainda aceitável.

Como o nível superior aparece mais alto na imagem:

```text
y_limSup < y_limInf
```

---

## 15. Etapa 9 — Regra de classificação

A classificação será feita comparando `y_liquido` com os limites calibrados.

Regra sem tolerância:

```text
se y_liquido > y_limInf:
    classe = "abaixo"

se y_limSup <= y_liquido <= y_limInf:
    classe = "ok"

se y_liquido < y_limSup:
    classe = "acima"
```

Regra com tolerância:

```text
se y_liquido > y_limInf + tolerancia:
    classe = "abaixo"

senão se y_liquido < y_limSup - tolerancia:
    classe = "acima"

senão:
    classe = "ok"
```

A tolerância é importante porque pequenas variações de iluminação, ruído ou posicionamento podem deslocar a linha detectada em alguns pixels.

Valor inicial sugerido:

```text
tolerância = 5 a 15 pixels
```

A tolerância deve ser ajustada empiricamente com base nos resultados do dataset.

---

## 16. Etapa 10 — Cálculo do nível normalizado

Além de usar a posição `y`, é recomendável calcular o nível normalizado da garrafa.

Definir:

```text
y_topo_util = topo da região útil da garrafa
y_base_util = base da região útil da garrafa
```

Cálculo:

```text
nivel = (y_base_util - y_liquido) / (y_base_util - y_topo_util)
```

Interpretação:

```text
nível próximo de 0 → garrafa quase vazia
nível próximo de 1 → garrafa quase cheia
```

Exemplo:

```text
y_topo_util = 100
y_base_util = 600
y_liquido = 250

nivel = (600 - 250) / (600 - 100)
nivel = 350 / 500
nivel = 0,70
```

Resultado:

```text
nível detectado = 70%
```

Esse valor facilita a apresentação dos resultados no relatório.

---

## 17. Saídas geradas pelo sistema

Para cada imagem, o sistema deve gerar:

1. Imagem original.
2. Região de interesse recortada.
3. Imagem em tons de cinza.
4. Imagem filtrada.
5. Máscara binária do líquido.
6. Máscara após morfologia.
7. Imagem final com a linha do líquido desenhada.
8. Classe prevista.

Exemplo de tabela de saída:

| Arquivo | Classe real | y detectado | Nível detectado | Classe prevista |
|---|---:|---:|---:|---|
| `01_abaixo.jpeg` | abaixo | 365 | 0,42 | abaixo |
| `09_noLimite.jpeg` | ok | 245 | 0,68 | ok |
| `15_acima.jpeg` | acima | 120 | 0,93 | acima |

---

## 18. Avaliação do sistema

A avaliação será feita comparando a classe prevista pelo algoritmo com a classe real definida no `labels.csv`.

### 18.1 Matriz de confusão multiclasse

Exemplo:

| Real \ Previsto | Abaixo | OK | Acima |
|---|---:|---:|---:|
| Abaixo | 7 | 0 | 0 |
| OK | 0 | 6 | 0 |
| Acima | 0 | 1 | 2 |

### 18.2 Matriz de confusão binária

Para a versão binária:

```text
Abaixo → Defeituosa
Acima  → Defeituosa
OK     → OK
```

Exemplo:

| Real \ Previsto | OK | Defeituosa |
|---|---:|---:|
| OK | 6 | 0 |
| Defeituosa | 1 | 9 |

### 18.3 Acurácia

Cálculo:

```text
acurácia = número de acertos / número total de imagens
```

Exemplo:

```text
acurácia = 15 / 16 = 93,75%
```

---

## 19. Possíveis falhas e limitações

O método pode falhar em algumas situações:

| Problema | Impacto |
|---|---|
| Reflexos fortes na garrafa | Podem criar buracos na máscara ou falsas regiões claras |
| Fundo muito irregular | Pode interferir na limiarização |
| Garrafa muito deslocada | Pode prejudicar a ROI fixa |
| Linha do líquido inclinada | Pode tornar a detecção por projeção horizontal menos precisa |
| Pouca diferença entre líquido e fundo | Pode dificultar a segmentação |
| Bolhas ou espuma no topo | Podem deslocar a linha detectada |

Essas limitações devem ser discutidas no relatório.

---

## 20. Estratégias para reduzir erros

Algumas melhorias possíveis:

| Problema | Estratégia |
|---|---|
| Reflexos | Usar fechamento morfológico maior |
| Ruído fora do líquido | Usar abertura morfológica |
| Fundo interferindo | Ajustar melhor a ROI |
| Variação de iluminação | Testar limiarização adaptativa |
| Garrafa deslocada | Detectar automaticamente o contorno da garrafa |
| Linha irregular | Usar média ou mediana das primeiras linhas detectadas |

---

## 21. Texto sugerido para a metodologia do relatório

> O sistema proposto realiza a inspeção automática do nível de preenchimento de garrafas por meio de técnicas clássicas de processamento digital de imagens. Inicialmente, cada imagem é recortada em uma região de interesse correspondente ao corpo da garrafa. Em seguida, a imagem é convertida para tons de cinza e suavizada com filtro Gaussiano, reduzindo ruídos e pequenas variações de intensidade. A região do líquido é segmentada por limiarização de Otsu invertida, uma vez que o líquido apresenta intensidade inferior ao fundo e à parte vazia da garrafa. A máscara binária resultante passa por operações morfológicas de abertura e fechamento, com o objetivo de remover ruídos e preencher falhas causadas por reflexos. Por fim, calcula-se a projeção horizontal da máscara para detectar a primeira linha com presença significativa de líquido. Essa posição é comparada com limites calibrados a partir de imagens representando os níveis mínimo e máximo aceitáveis, permitindo classificar cada garrafa como abaixo do limite, dentro da faixa aceitável ou acima do limite.

---

## 22. Texto sugerido para a justificativa da morfologia

> As operações morfológicas foram aplicadas para melhorar a qualidade da máscara binária obtida após a segmentação. A abertura foi utilizada para remover pequenos ruídos isolados, enquanto o fechamento foi empregado para preencher falhas internas na região do líquido, principalmente aquelas causadas por reflexos na superfície da garrafa. O elemento estruturante retangular foi escolhido porque o líquido forma uma região predominantemente horizontal e compacta no interior da garrafa, tornando essa geometria adequada para preservar a estrutura principal da região segmentada.

---

## 23. Conclusão esperada

O método deve apresentar bom desempenho quando as imagens forem capturadas em condições controladas, com fundo uniforme, iluminação semelhante e garrafa aproximadamente alinhada.

A principal vantagem do pipeline é sua simplicidade e interpretabilidade: cada etapa pode ser visualizada e explicada no relatório.

A principal limitação é a dependência de condições controladas de captura. Reflexos, deslocamentos da garrafa ou mudanças bruscas de iluminação podem prejudicar a segmentação e alterar a linha detectada do líquido.
