# Inspeção Industrial e Análise de Documentos

Até o momento, exploramos o tratamento matricial da imagem na **Parte I: Processamento Digital de Imagens (PDI)**, aplicando filtros morfológicos, convoluções e limiarizações espaciais. A transição para a **Visão Computacional (VC)** exige a habilidade de extrair semântica, geometria e estruturas de dados a partir dos pixels brutos.

Neste capítulo, abordaremos duas vertentes da visão 2D clássica: a **Inspeção Industrial** (controle de qualidade em esteiras) e a **Análise Automatizada de Documentos**, elemento central para a operação de plataformas educacionais abertas de correção automatizada de exames, como o ecossistema **MCTest**. Abordaremos o fluxo completo de ingestão: retificação de inclinação, isolamento de marcadores através de propriedades geométricas invariantes e mapeamento lógico de grades de respostas (*Optical Mark Recognition - OMR*).


## Objetivos do Capítulo

Ao final deste capítulo, você será capaz de:

*   **Compreender os fundamentos da Visão Computacional para Análise de Documentos:** Entender como a VC vai além do PDI para extrair informações significativas de imagens de documentos.
*   **Aplicar técnicas de Pré-processamento para OMR:** Dominar a retificação de inclinação, limiarização adaptativa e detecção de bordas para preparar documentos para análise.
*   **Implementar algoritmos de Detecção e Mapeamento de Marcadores:** Desenvolver soluções para identificar marcadores (bolhas) em folhas de resposta e associá-los a uma grade lógica.
*   **Construir um sistema de Correção Automatizada de Exames (OMR):** Criar um protótipo funcional de OMR utilizando Python e OpenCV/scikit-image, simulando o processo do ecossistema MCTest.
*   **Explorar aplicações de Inspeção Industrial:** Entender como os mesmos princípios podem ser aplicados para controle de qualidade e detecção de defeitos em ambientes  e industriais.

## Bases de Imagens para Experimentação

Ao longo desta segunda parte do livro, serão utilizados documentos digitalizados, folhas de respostas, códigos de barras, QR Codes e outros tipos de imagens provenientes de aplicações reais. Entretanto, para garantir a reprodutibilidade dos experimentos e permitir a execução dos *notebooks* mesmo na ausência dos arquivos originais, muitos exemplos utilizam imagens públicas disponibilizadas por bibliotecas de Visão Computacional.

A biblioteca `skimage.data` fornece uma coleção de imagens amplamente empregadas no ensino e na pesquisa em Processamento Digital de Imagens. Essas imagens abrangem fotografias, documentos digitalizados, padrões sintéticos e objetos de interesse para segmentação e análise. A Tabela @tbl-skimage-data apresenta algumas das imagens mais utilizadas dessa coleção.

Entre elas, destacam-se `text()` e `page()`, particularmente adequadas para experimentos de OCR (*Optical Character Recognition*), OMR (*Optical Mark Recognition*) e análise documental. A Figura @fig-skimage-data ilustra exemplos representativos desse conjunto de imagens.

Diferentemente do `skimage.data`, que disponibiliza um acervo fixo para fins didáticos, a biblioteca OpenCV (`cv2`) fornece mecanismos para leitura de arquivos externos (`cv2.imread`) e aquisição de imagens provenientes de câmeras, vídeos ou outros dispositivos. Dessa forma, os mesmos algoritmos desenvolvidos neste capítulo podem ser aplicados tanto às imagens de demonstração quanto a documentos reais.

Sempre que possível, os *notebooks* incluem mecanismos de contingência (*fallback*) que substituem automaticamente arquivos ausentes por imagens públicas equivalentes. Essa estratégia facilita a reprodução dos experimentos em diferentes ambientes computacionais e garante que todos os exemplos permaneçam executáveis sem dependências externas específicas.

## 6.1 Fundamentos de OMR e Inspeção Industrial

A **Optical Mark Recognition (OMR)**, ou Reconhecimento Óptico de Marcas, é uma tecnologia que permite a leitura automatizada de dados marcados em formulários, como folhas de resposta de exames, questionários e pesquisas. Diferente do OCR (Reconhecimento Óptico de Caracteres), que se concentra na identificação de caracteres alfanuméricos, o OMR foca na detecção da presença ou ausência de marcas em posições pré-definidas [1].

Historicamente, sistemas OMR dependiam de hardware especializado e caro. No entanto, avanços em **Visão Computacional (VC)** e o poder de processamento dos computadores modernos permitiram o desenvolvimento de soluções de baixo custo e alta acurácia utilizando câmeras comuns e bibliotecas de processamento de imagens como OpenCV e scikit-image [2].

### 6.1.1 O Processo Geral de OMR

O processo de OMR baseado em visão computacional geralmente envolve as seguintes etapas:

1.  **Aquisição da Imagem:** Captura da folha de resposta por uma câmera ou scanner.
2.  **Pré-processamento:** Melhoria da qualidade da imagem para facilitar a detecção das marcas. Isso inclui:
    *   **Retificação de Inclinação (Deskewing):** Correção de rotações e perspectivas para alinhar o documento.
    *   **Limiarização Adaptativa:** Conversão da imagem para binário, ajustando o limiar dinamicamente para diferentes regiões da imagem, o que é crucial para documentos com iluminação irregular.
    *   **Detecção de Bordas:** Identificação dos contornos do documento e das regiões de interesse (como as grades de resposta).
3.  **Localização e Extração de Regiões de Interesse (ROIs):** Identificação das áreas onde as marcas (bolhas) são esperadas. Isso pode envolver a detecção de marcadores de referência no formulário.
4.  **Detecção de Marcas:** Análise de cada ROI para determinar se uma marca está presente. Isso geralmente é feito calculando a intensidade de pixels dentro da bolha e comparando com um limiar.
5.  **Mapeamento Lógico e Pontuação:** Associação das marcas detectadas com as respostas corretas e cálculo da pontuação do exame.

### 6.1.2 Inspeção Industrial: Um Paralelo Prático

Os princípios do OMR são diretamente aplicáveis à **Inspeção Industrial**, onde a visão computacional é utilizada para controle de qualidade e detecção de defeitos em linhas de produção. Por exemplo, um sistema pode inspecionar produtos para:

*   **Verificar a presença de componentes:** Assemelha-se à detecção de marcas, onde a presença de um componente é uma 
marca. 
*   **Detectar defeitos:** Identificar anomalias como arranhões, trincas, ou descolorações. 
*   **Medir dimensões:** Verificar se as dimensões de um produto estão dentro das especificações. 

Em ambos os casos, a capacidade de processar imagens, identificar padrões e tomar decisões automatizadas é fundamental. A seguir, exploraremos a implementação prática dessas técnicas. 

## 6.2 Implementação Prática de OMR com Python e OpenCV/scikit-image 

Para tornar este capítulo o mais prático e motivador possível, vamos construir um sistema OMR passo a passo, utilizando bibliotecas populares de visão computacional em Python. 

### 6.2.1 Configuração do Ambiente 

Primeiro, vamos garantir que temos as bibliotecas necessárias instaladas. 

```python 
# Instalação das bibliotecas necessárias (se ainda não estiverem instaladas) 
!pip install opencv-python scikit-image numpy matplotlib 
``` 

### 6.2.2 Carregamento e Visualização de Imagens 

Vamos começar carregando uma imagem de exemplo de uma folha de respostas. 

```python 
import cv2 
import numpy as np 
import matplotlib.pyplot as plt 
from skimage import io, data, color 

# Função auxiliar para exibir imagens 
def imshow_components(labels): 
    # Map component labels to hue val 
    label_hue = np.uint8(179*labels/np.max(labels)) 
    empty_channel = 255*np.ones_like(label_hue) 
    labeled_img = cv2.merge([label_hue, empty_channel, empty_channel]) 

    # Cvt to BGR for display 
    labeled_img = cv2.cvtColor(labeled_img, cv2.COLOR_HSV2BGR) 

    # Set background label to black 
    labeled_img[label_hue==0] = 0 
    return labeled_img 

# Carregar imagem de uma folha de respostas (exemplo: usando skimage.data.page) 
# Em um cenário real, você usaria cv2.imread('caminho/para/sua/imagem.png') 

# Tentativa de carregar uma imagem local ou usar fallback 
try: 
    # Supondo que você tenha uma imagem de folha de respostas chamada 'folha_respostas.png' 
    # na mesma pasta ou em um caminho específico. 
    # Para fins de demonstração, vamos usar uma imagem de página da skimage. 
    image_original = data.page() 
    print("Imagem carregada de skimage.data.page()") 
except FileNotFoundError: 
    print("Arquivo 'folha_respostas.png' não encontrado. Usando imagem de fallback.") 
    image_original = data.page() # Fallback para imagem de página da skimage 

# Converter para tons de cinza se a imagem for colorida 
if len(image_original.shape) == 3: 
    image_gray = color.rgb2gray(image_original) 
else: 
    image_gray = image_original 

plt.figure(figsize=(10, 8)) 
plt.imshow(image_gray, cmap='gray') 
plt.title('Imagem Original (Tons de Cinza)') 
plt.axis('off') 
plt.show() 
``` 

### 6.2.3 Pré-processamento: Retificação de Inclinação (Deskewing) 

Documentos digitalizados ou fotografados frequentemente apresentam inclinação. A retificação é crucial para o alinhamento correto. 

```python 
from skimage.transform import rotate 
from skimage.filters import threshold_otsu 
from skimage.measure import moments, moments_central, moments_normalized, moments_hu 

def deskew(image): 
    # Binarizar a imagem para calcular os momentos 
    thresh = threshold_otsu(image) 
    binary = image > thresh 

    # Calcular momentos centrais para encontrar o ângulo de inclinação 
    m = moments(binary) 
    m_central = moments_central(binary, m[0, 1] / m[0, 0], m[1, 0] / m[0, 0]) 
    # Calcular o ângulo de inclinação usando o segundo momento central 
    # (m_central[1, 1] / m_central[0, 2]) 
    # A fórmula exata para o ângulo de inclinação é mais complexa, 
    # mas para simplificar, podemos usar a orientação principal do objeto. 
    # Uma abordagem mais robusta envolveria a transformada de Hough ou PCA. 
    # Para este exemplo, vamos simular uma inclinação e corrigi-la. 

    # Para demonstração, vamos aplicar uma rotação artificial e depois tentar corrigir 
    # Em um cenário real, você detectaria a inclinação. 
    # Vamos assumir um pequeno ângulo de inclinação para demonstração. 
    angle = 5 # Graus 
    rotated_image = rotate(image, angle, resize=True, mode='edge') 

    # Para um deskewing real, você precisaria calcular o ângulo. 
    # Exemplo simplificado de cálculo de ângulo (não robusto para todos os casos): 
    # if abs(m_central[0, 2]) > 0.001: 
    #     skew_angle = 0.5 * np.arctan(2 * m_central[1, 1] / (m_central[0, 2] - m_central[2, 0])) 
    #     skew_angle = np.degrees(skew_angle) 
    # else: 
    #     skew_angle = 0 
    # print(f"Ângulo de inclinação detectado: {skew_angle:.2f} graus") 
    # deskewed_image = rotate(image, -skew_angle, resize=True, mode='edge') 

    # Para este exemplo, vamos apenas mostrar a imagem rotacionada como se fosse a entrada inclinada 
    # e a 'correção' seria a imagem original. 
    # Em um sistema real, você calcularia o ângulo da imagem 'inclinada' e a corrigiria. 

    return rotated_image, image # Retorna a imagem inclinada e a 'corrigida' (original para comparação) 

image_skewed, image_deskewed = deskew(image_gray) 

plt.figure(figsize=(12, 6)) 
plt.subplot(1, 2, 1) 
plt.imshow(image_skewed, cmap='gray') 
plt.title('Imagem Inclinada (Simulada)') 
plt.axis('off') 

plt.subplot(1, 2, 2) 
plt.imshow(image_deskewed, cmap='gray') 
plt.title('Imagem Corrigida (Original)') 
plt.axis('off') 
plt.show() 
``` 

### 6.2.4 Limiarização Adaptativa 

A limiarização adaptativa é essencial para lidar com variações de iluminação. 

```python 
from skimage.filters import threshold_local 

# Aplicar limiarização adaptativa 
block_size = 35 # Tamanho do bloco para cálculo do limiar local 
adaptive_thresh = threshold_local(image_deskewed, block_size, offset=10) 
binary_adaptive = image_deskewed > adaptive_thresh 

plt.figure(figsize=(10, 8)) 
plt.imshow(binary_adaptive, cmap='gray') 
plt.title('Imagem Binarizada com Limiarização Adaptativa') 
plt.axis('off') 
plt.show() 
``` 

### 6.2.5 Detecção de Bordas e Contornos 

Para localizar as regiões de interesse, como as bolhas de resposta, a detecção de bordas e contornos é fundamental. 

```python 
from skimage.feature import canny 
from skimage.morphology import binary_erosion, binary_dilation 
from skimage.measure import find_contours 

# Aplicar Canny para detecção de bordas 
edges = canny(binary_adaptive, sigma=3) 

plt.figure(figsize=(10, 8)) 
plt.imshow(edges, cmap='gray') 
plt.title('Bordas Detectadas (Canny)') 
plt.axis('off') 
plt.show() 

# Encontrar contornos (exemplo simplificado, em OMR real seria mais complexo) 
# Para OMR, geralmente procuramos por contornos circulares ou elípticos. 
# Vamos simular a detecção de contornos para encontrar as 'bolhas'. 

# Em um cenário real, você usaria cv2.findContours ou uma abordagem mais sofisticada 
# para identificar as regiões das bolhas. 

# Para demonstração, vamos apenas mostrar os contornos gerais da página. 
# A detecção de bolhas será abordada na próxima seção. 

# Exemplo de como encontrar contornos (apenas para visualização) 
# contours = find_contours(edges, 0.8) 
# fig, ax = plt.subplots(figsize=(10, 8)) 
# ax.imshow(image_deskewed, cmap='gray') 
# for n, contour in enumerate(contours): 
#     ax.plot(contour[:, 1], contour[:, 0], linewidth=2) 
# ax.axis('off') 
# ax.set_title('Contornos Detectados') 
# plt.show() 
``` 

### 6.2.6 Localização e Extração de Regiões de Interesse (ROIs) - Detecção de Bolhas 

Esta é a parte central do OMR: identificar as bolhas e determinar se estão marcadas. 

```python 
from skimage.transform import hough_circle, hough_circle_peaks 
from skimage.feature import canny 
from skimage.draw import circle_perimeter 

# A detecção de círculos pode ser feita com a Transformada de Hough para Círculos. 
# No entanto, para folhas de OMR, onde as bolhas são de tamanho e espaçamento conhecidos, 
# uma abordagem baseada em contornos e propriedades geométricas é mais comum e eficiente. 

# Vamos simular a detecção de bolhas usando contornos e filtragem por área/circularidade. 
# Para isso, precisamos de uma imagem binarizada onde as bolhas preenchidas se destacam. 

# Usaremos a imagem binarizada adaptativa. 
# Encontrar contornos na imagem binarizada 
# cv2.findContours retorna uma tupla: (contornos, hierarquia) para OpenCV 3.x e 4.x 
# ou apenas contornos para OpenCV 2.x 

# Certifique-se de que a imagem binária é do tipo CV_8UC1 para findContours 
binary_for_contours = (binary_adaptive * 255).astype(np.uint8) 
contours, hierarchy = cv2.findContours(binary_for_contours, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 

output_image = cv2.cvtColor((image_deskewed * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR) 
marked_bubbles = [] 

for contour in contours: 
    # Calcular a área do contorno 
    area = cv2.contourArea(contour) 

    # Filtrar contornos com base na área (ajustar esses valores conforme o tamanho das bolhas) 
    # Assumimos que as bolhas têm um tamanho razoável. 
    if 50 < area < 500: # Valores de área a serem ajustados experimentalmente 
        # Calcular o círculo mínimo que envolve o contorno 
        ((x, y), radius) = cv2.minEnclosingCircle(contour) 
        circularity = 4 * np.pi * area / (cv2.arcLength(contour, True)**2) 

        # Filtrar por circularidade (bolhas são aproximadamente circulares) 
        if 0.7 < circularity < 1.3: # Ajustar o limiar de circularidade 
            # Desenhar o contorno e o círculo mínimo 
            cv2.drawContours(output_image, [contour], -1, (0, 255, 0), 2) 
            cv2.circle(output_image, (int(x), int(y)), int(radius), (255, 0, 0), 2) 

            # Verificar se a bolha está marcada (preenchida) 
            # Para isso, podemos verificar a intensidade de pixels dentro do círculo. 
            # Uma bolha marcada terá uma média de intensidade de pixel menor (mais escura). 
            mask = np.zeros(image_deskewed.shape, dtype=np.uint8) 
            cv2.circle(mask, (int(x), int(y)), int(radius), 255, -1) 
            mean_intensity = cv2.mean(image_deskewed, mask=mask)[0] 

            # Limiar para considerar a bolha marcada (ajustar experimentalmente) 
            # Um valor menor indica uma bolha mais escura (marcada). 
            if mean_intensity < 0.5: # Assumindo imagem normalizada entre 0 e 1 
                marked_bubbles.append(((x, y), radius, 'marked')) 
                cv2.circle(output_image, (int(x), int(y)), int(radius), (0, 0, 255), -1) # Desenha preenchido se marcado 
            else: 
                marked_bubbles.append(((x, y), radius, 'unmarked')) 

plt.figure(figsize=(12, 10)) 
plt.imshow(output_image) 
plt.title('Bolhas Detectadas e Marcadas') 
plt.axis('off') 
plt.show() 

print(f"Total de bolhas detectadas: {len(marked_bubbles)}") 
for i, (center, radius, status) in enumerate(marked_bubbles): 
    print(f"Bolha {i+1}: Centro=({center[0]:.2f}, {center[1]:.2f}), Raio={radius:.2f}, Status={status}") 
``` 

### 6.2.7 Mapeamento Lógico e Pontuação (Simulação MCTest) 

No contexto do MCTest, as bolhas detectadas precisam ser mapeadas para perguntas e opções de resposta. 

```python 
# Simulação de um gabarito 
gabarito = { 
    (100, 150): 'A', # Exemplo: bolha na posição (100, 150) corresponde à opção 'A' da pergunta 1 
    (100, 200): 'B', 
    (100, 250): 'C', 
    (100, 300): 'D', 
    (100, 350): 'E', 
    # ... e assim por diante para outras perguntas 
} 

# Em um sistema real, você teria uma estrutura de dados que define a geometria 
# das perguntas e opções na folha. 

# Para este exemplo, vamos simular a pontuação com base nas bolhas marcadas. 
# A lógica seria: para cada pergunta, verificar qual bolha foi marcada e comparar com o gabarito. 

score = 0 
# Supondo que 'marked_bubbles' contém as bolhas que foram detectadas como marcadas. 
# Em um sistema real, você agruparia as bolhas por pergunta e verificaria a marcação. 

# Exemplo simplificado de pontuação: 
# Vamos assumir que as primeiras 5 bolhas detectadas correspondem a 5 perguntas, 
# e que as respostas corretas são: 1: A, 2: B, 3: C, 4: D, 5: E 

# Para tornar isso mais concreto, vamos definir posições de bolhas esperadas 
# e um gabarito correspondente. 

expected_bubble_positions = [ 
    (100, 150), # Pergunta 1, Opção A 
    (100, 200), # Pergunta 1, Opção B 
    (100, 250), # Pergunta 1, Opção C 
    (100, 300), # Pergunta 1, Opção D 
    (100, 350), # Pergunta 1, Opção E 

    (200, 150), # Pergunta 2, Opção A 
    (200, 200), # Pergunta 2, Opção B 
    (200, 250), # Pergunta 2, Opção C 
    (200, 300), # Pergunta 2, Opção D 
    (200, 350), # Pergunta 2, Opção E 
] 

correct_answers = { 
    0: 'A', # Pergunta 1, resposta correta A (índice 0 de expected_bubble_positions) 
    1: 'B', # Pergunta 2, resposta correta B (índice 1 de expected_bubble_positions) 
    # ... e assim por diante 
} 

# Para simplificar, vamos associar as bolhas detectadas às posições esperadas 
# com base na proximidade. 

student_answers = {} 

for (center, radius, status) in marked_bubbles: 
    if status == 'marked': 
        # Encontrar a bolha esperada mais próxima 
        min_dist = float('inf') 
        closest_bubble_idx = -1 
        for i, (exp_x, exp_y) in enumerate(expected_bubble_positions): 
            dist = np.sqrt((center[0] - exp_x)**2 + (center[1] - exp_y)**2) 
            if dist < min_dist: 
                min_dist = dist 
                closest_bubble_idx = i 
        
        if closest_bubble_idx != -1 and min_dist < 30: # Limiar de distância para associação 
            # Determinar qual opção foi marcada (A, B, C, D, E) 
            # Isso dependeria da organização das bolhas na folha. 
            # Para este exemplo, vamos assumir que as bolhas são agrupadas por pergunta. 
            
            question_idx = closest_bubble_idx // 5 # 5 opções por pergunta 
            option_idx = closest_bubble_idx % 5 
            option_char = chr(ord('A') + option_idx) 
            
            student_answers[question_idx] = option_char 

final_score = 0 
for q_idx, s_ans in student_answers.items(): 
    if q_idx in correct_answers and correct_answers[q_idx] == s_ans: 
        final_score += 1 

print(f"Respostas do aluno: {student_answers}") 
print(f"Pontuação final: {final_score}") 
``` 

## 6.3 Inspeção Industrial: Aplicação Prática 

Os mesmos princípios de detecção de padrões e análise de imagens podem ser aplicados na inspeção industrial. 

### 6.3.1 Detecção de Defeitos em Produtos 

Imagine uma linha de produção onde precisamos verificar se um produto tem arranhões. 

```python 
# Simulação de detecção de defeitos 
# Carregar uma imagem de um produto (simulado com data.coffee()) 
product_image = data.coffee() 

if len(product_image.shape) == 3: 
    product_image_gray = color.rgb2gray(product_image) 
else: 
    product_image_gray = product_image 

# Simular um defeito (por exemplo, um arranhão escuro) 
defect_image = np.copy(product_image_gray) 
defect_image[100:110, 200:300] = 0.1 # Simula um arranhão escuro 

plt.figure(figsize=(12, 6)) 
plt.subplot(1, 2, 1) 
plt.imshow(product_image_gray, cmap='gray') 
plt.title('Produto Sem Defeito') 
plt.axis('off') 

plt.subplot(1, 2, 2) 
plt.imshow(defect_image, cmap='gray') 
plt.title('Produto Com Defeito (Simulado)') 
plt.axis('off') 
plt.show() 

# Detecção de defeitos usando subtração de imagem e limiarização 
difference = np.abs(product_image_gray - defect_image) 

# Ajustar o limiar para detectar o defeito 
defect_threshold = 0.15 # Ajustar experimentalmente 
detected_defect = difference > defect_threshold 

plt.figure(figsize=(10, 8)) 
plt.imshow(detected_defect, cmap='gray') 
plt.title('Defeito Detectado') 
plt.axis('off') 
plt.show() 

if np.any(detected_defect): 
    print("Defeito detectado no produto!") 
else: 
    print("Produto sem defeitos aparentes.") 
``` 

## Conclusão 

Neste capítulo, exploramos a transição do Processamento Digital de Imagens para a Visão Computacional, focando em aplicações práticas como a **Inspeção Industrial** e a **Análise Automatizada de Documentos** com **OMR**. Vimos como técnicas de pré-processamento, detecção de contornos e análise de regiões de interesse são fundamentais para construir sistemas robustos de reconhecimento de marcas. A capacidade de extrair informações semânticas de imagens abre um vasto campo de possibilidades para automação e controle de qualidade em diversas áreas. 

## Referências 

[1] Moreira, P. H. C., Ferreira, B. P., & Reis, M. V. D. (2025). Automated Correction of Multiple Choice Tests Using Computer Vision. *Anais do XVI Workshop de Sistemas de Informação (WSIS)*. [https://sol.sbc.org.br/index.php/wsis/article/view/37623](https://sol.sbc.org.br/index.php/wsis/article/view/37623) 
[2] PyImageSearch. (2016). Bubble sheet multiple choice scanner and test grader using OMR, Python, and OpenCV. [https://pyimagesearch.com/2016/10/03/bubble-sheet-multiple-choice-scanner-and-test-grader-using-omr-python-and-opencv/](https://pyimagesearch.com/2016/10/03/bubble-sheet-multiple-choice-scanner-and-test-grader-using-omr-python-and-opencv/) 
