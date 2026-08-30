# -*- coding: utf-8 -*-
"""
Mega Podcast - Formação em Data Science e Machine Learning

Este script foi gerado especificamente a partir da estrutura cronológica
fornecida pelo usuário. A lista ORDEM_AULAS contém exatamente 200 vídeos,
na ordem em que aparecem no arquivo de estrutura.

Fluxo:
1) verifica os 200 caminhos esperados;
2) extrai/converte o áudio de cada vídeo para AAC, na ordem fixa;
3) anexa os fluxos AAC em um único arquivo ADTS temporário;
4) remuxa para M4A sem recomprimir novamente.

Dependências externas são instaladas automaticamente:
- customtkinter
- imageio-ffmpeg
"""

import os
import sys
import subprocess
import threading
import tempfile
import shutil
from pathlib import Path


# ============================================================
# AUTO-INSTALAÇÃO
# ============================================================

def garantir_pacote(pacote: str, modulo: str | None = None):
    modulo = modulo or pacote
    try:
        __import__(modulo)
    except ImportError:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", pacote
        ])


garantir_pacote("customtkinter")
garantir_pacote("imageio-ffmpeg", "imageio_ffmpeg")

import customtkinter as ctk
from tkinter import filedialog, messagebox
import imageio_ffmpeg


# ============================================================
# CONFIGURAÇÃO ESPECÍFICA DESTE CURSO
# ============================================================

DEFAULT_ROOT = Path(
    r"G:\Meu Drive\CURSOS\Programação e tecnologia\Formacao.em.Data.Science.e.Machine.Learning"
)

DEFAULT_OUTPUT_NAME = "Mega Podcast - Formacao Data Science e Machine Learning.m4a"

ORDEM_AULAS = [
    '1. PYTHON STARTER/0. Apresentação do Curso/1. Bem vindos ao curso.mp4',
    '1. PYTHON STARTER/0. Apresentação do Curso/2. Asimov Academy e Princípios.mp4',
    '1. PYTHON STARTER/0. Apresentação do Curso/3. O que é uma linguagem de programação.mp4',
    '1. PYTHON STARTER/0. Apresentação do Curso/4. Tutorial plataforma.mp4',
    '1. PYTHON STARTER/0. Apresentação do Curso/5. O que podemos e não podemos fazer com Python.mp4',
    '1. PYTHON STARTER/0. Apresentação do Curso/6. Conclusão.mp4',
    '1. PYTHON STARTER/1. Lógica de Programação/1. Apresentação do módulo.mp4',
    '1. PYTHON STARTER/1. Lógica de Programação/2. Algoritmos 1.mp4',
    '1. PYTHON STARTER/1. Lógica de Programação/3. Algoritmos 2.mp4',
    '1. PYTHON STARTER/1. Lógica de Programação/4. Algoritmos 3.mp4',
    '1. PYTHON STARTER/1. Lógica de Programação/5. Algoritmos 4.mp4',
    '1. PYTHON STARTER/1. Lógica de Programação/6. Variáveis.mp4',
    '1. PYTHON STARTER/1. Lógica de Programação/7. Operadores.mp4',
    '1. PYTHON STARTER/1. Lógica de Programação/8. Estruturas de controle de fluxo.mp4',
    '1. PYTHON STARTER/1. Lógica de Programação/9. Estruturas de repetição.mp4',
    '1. PYTHON STARTER/2. Introdução ao Python/1- Oque é Python.mp4',
    '1. PYTHON STARTER/2. Introdução ao Python/2- Instalando o Python através do Anaconda.mp4',
    '1. PYTHON STARTER/2. Introdução ao Python/3 - Executando o primeiro programa.mp4',
    '1. PYTHON STARTER/2. Introdução ao Python/4 - O Segundo Código E Terminais De Programação.mp4',
    '1. PYTHON STARTER/2. Introdução ao Python/5 - Ides E Jupyterlab.mp4',
    '1. PYTHON STARTER/2. Introdução ao Python/6 - Visual Studio Code.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/1. Primeiros passos com JupyterLab.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/2. Números.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/3. Variaveis.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/4. Strings e Indexação.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/5. Mais sobre Strings e métodos embutidos.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/6.Listas.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/7. Dicionários.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/8. Tuplas .mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/9. Input, sets e booleanos.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/10. Operadores de comparação.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/11. Exercícios - Parte 1.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/12. Solução dos exercícios - Parte 1.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/13. Operadores de comparação em cadeia.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/14. If, elif e else.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/15. Range.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/16. For.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/17. While.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/18. Compreensão em listas.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/19. Funções.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/20. Lambda.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/21. Exercícios - Parte 2.mp4',
    '1. PYTHON STARTER/3. Fundamentos da Linguagem/22. Solução dos exercícios - Parte 2.mp4',
    '1. PYTHON STARTER/4. Projetos - Calculadora e software de gestão/1. Introdução - Calculadora.mp4',
    '1. PYTHON STARTER/4. Projetos - Calculadora e software de gestão/2. Resolução - Calculadora.mp4',
    '1. PYTHON STARTER/4. Projetos - Calculadora e software de gestão/3. Introdução - Software de gestão para locadora de carros.mp4',
    '1. PYTHON STARTER/4. Projetos - Calculadora e software de gestão/4. Resolução - Software de gestão para locadora de carros - Pt1.mp4',
    '1. PYTHON STARTER/4. Projetos - Calculadora e software de gestão/5. Resolução - Software de gestão para locadora de carros - Pt2.mp4',
    '1. PYTHON STARTER/5. Gerenciamento de erros e Depuração de código/1. Apresentação do módulo.mp4',
    '1. PYTHON STARTER/5. Gerenciamento de erros e Depuração de código/2. Importação de módulos e pdb.mp4',
    '1. PYTHON STARTER/5. Gerenciamento de erros e Depuração de código/3. Try, Except e Finally-.mp4',
    '1. PYTHON STARTER/5. Gerenciamento de erros e Depuração de código/4. Logging.mp4',
    '1. PYTHON STARTER/5. Gerenciamento de erros e Depuração de código/5. Apresentação do projeto papel pedra e tesoura.mp4',
    '1. PYTHON STARTER/5. Gerenciamento de erros e Depuração de código/6. Projeto Papel pedra e Tesoura.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/1. Introdução a programação orientada a objetos.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/2. Objetos e Classes no Python.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/3. Criando classes e métodos.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/4. Herança e método especiais.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/5. Projeto - Simulador de caos.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/6. Simulador de caos.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/7. Simulador de caos pt2.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/8. Apresentação projeto Jogo da velha.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/9. Projeto Final - Jogo da velha.MP4.mp4',
    '1. PYTHON STARTER/6. Programação orientada a objetos/10. Projeto Final - Jogo da velha - pt2.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/1. O que é o Pandas e do ele é capaz.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/2. Como estudar Pandas.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/3. Como vão se dar as aulas.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/4. Series.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/5. DataFrames e manipulação de colunas.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/6. Iloc e Filtros.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/7. Operações com índices.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/8. Índices multiníveis.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/9. Tratamento de dados ausentes.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/10. Groupby.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/11. Merge, concat e Join.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/12. Operações com DataFrames.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/13. Séries temporais no pandas.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/14. Entrada e Saída de dados.mp4',
    '2. Analisando Dados com Pandas/1. Conceitos básicos de Pandas/15. Encerramento.mp4',
    '2. Analisando Dados com Pandas/2. Projeto 1 - Análise dos preços da gasolina no Brasil/2.1. Apresentação dos exercícios.mp4',
    '2. Analisando Dados com Pandas/2. Projeto 1 - Análise dos preços da gasolina no Brasil/2.2. Resolução dos exercícios pt1.mp4',
    '2. Analisando Dados com Pandas/2. Projeto 1 - Análise dos preços da gasolina no Brasil/2.3 e 2.4 Resolução dos exercícios pt2.mp4',
    '2. Analisando Dados com Pandas/2. Projeto 1 - Análise dos preços da gasolina no Brasil/2.5. Resolução dos exercícios pt3.mp4',
    '2. Analisando Dados com Pandas/3. Projeto 2 – Análise de dados de obesidade mundial/3.1. Apresentação do Projeto.mp4',
    '2. Analisando Dados com Pandas/3. Projeto 2 – Análise de dados de obesidade mundial/3.2. Funções adicionais.mp4',
    '2. Analisando Dados com Pandas/3. Projeto 2 – Análise de dados de obesidade mundial/3.3. Obesity pt 1.mp4',
    '2. Analisando Dados com Pandas/3. Projeto 2 – Análise de dados de obesidade mundial/3.4. Obesity pt2.mp4',
    '2. Analisando Dados com Pandas/4. Projeto 3 – Análise de dados de PIB per capita/4.1. GDP pt1.mp4',
    '2. Analisando Dados com Pandas/4. Projeto 3 – Análise de dados de PIB per capita/4.2. GDP pt2.mp4',
    '2. Analisando Dados com Pandas/4. Projeto 3 – Análise de dados de PIB per capita/4.3. GDP pt3.mp4',
    '2. Analisando Dados com Pandas/5. Resolução do desafio/5.1. Desafio final.mp4',
    '3. Visualizando dados com Matplotlib/1. Criando plots com Matplotlib/1.1. Introdução ao Matplotlib.mp4',
    '3. Visualizando dados com Matplotlib/1. Criando plots com Matplotlib/1.2. Funções básicas de plot.mp4',
    '3. Visualizando dados com Matplotlib/1. Criando plots com Matplotlib/1.3. Orientação à objetos no Matplotlib.mp4',
    '3. Visualizando dados com Matplotlib/1. Criando plots com Matplotlib/1.4. Subplots().mp4',
    '3. Visualizando dados com Matplotlib/1. Criando plots com Matplotlib/1.5. Customização.mp4',
    '3. Visualizando dados com Matplotlib/1. Criando plots com Matplotlib/1.6. Plots Especiais.mp4',
    '3. Visualizando dados com Matplotlib/2. Criando gráficos estatísticos com Seaborn/2.1. Introdução ao Seaborn.mp4',
    '3. Visualizando dados com Matplotlib/2. Criando gráficos estatísticos com Seaborn/2.2 Plots de distribuição.mp4',
    '3. Visualizando dados com Matplotlib/2. Criando gráficos estatísticos com Seaborn/2.3 Plots categóricos.mp4',
    '3. Visualizando dados com Matplotlib/2. Criando gráficos estatísticos com Seaborn/2.4. Plots de regressão.mp4',
    '3. Visualizando dados com Matplotlib/2. Criando gráficos estatísticos com Seaborn/2.5. Plots Matriciais.mp4',
    '3. Visualizando dados com Matplotlib/2. Criando gráficos estatísticos com Seaborn/2.6. Estilização.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/1. Uma visão geral sobre Machine Learning e AI/1 - Conceitos Fundamentais de Machine Learning e Inteligência Artificial.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/1. Uma visão geral sobre Machine Learning e AI/2 - Conceitos Fundamentais de Machine Learning e Inteligência Artificial.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/1. Uma visão geral sobre Machine Learning e AI/3 - Conceitos Fundamentais de Machine Learning e Inteligência Artificial.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/1. Uma visão geral sobre Machine Learning e AI/4 - Conceitos Fundamentais de Machine Learning e Inteligência Artificial.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/1. Uma visão geral sobre Machine Learning e AI/5 - Conceitos Fundamentais de Machine Learning e Inteligência Artificial.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/1. Uma visão geral sobre Machine Learning e AI/6 - Conceitos Fundamentais de Machine Learning e Inteligência Artificial.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/1. Uma visão geral sobre Machine Learning e AI/7 - Conceitos Fundamentais de Machine Learning e Inteligência Artificial.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/1. Uma visão geral sobre o projeto.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/2. Kaggle.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/3 - O checklist do ML.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/4. Análise exploratória dos dados.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/5. Análise Exploratória de dados 2.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/6. Correlação.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/7. Análise de correlação nos dados.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/8. Como funcionaria o treino_.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/9. Processamento de dados para ML.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/10. Treinando os primeiros modelos.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/11. Cross-Validation.mp4',
    '4. Conceitos fundamentais de Machine Learning e AI/2. Prevendo preços de apartamentos usando Machine Learning/12. Comparando Modelos.mp4',
    '5. Matemática para Data Science e Machine Learning/1. Como abordar a matemática/1. Introdução ao curso.mp4',
    '5. Matemática para Data Science e Machine Learning/1. Como abordar a matemática/2. Como o curso está dividido.mp4',
    '5. Matemática para Data Science e Machine Learning/2. Cálculo/1. O que são funções.mp4',
    '5. Matemática para Data Science e Machine Learning/2. Cálculo/2. Funções clássicas.mp4',
    '5. Matemática para Data Science e Machine Learning/2. Cálculo/3. Limites.MP4.mp4',
    '5. Matemática para Data Science e Machine Learning/2. Cálculo/4. O que são derivadas.mp4',
    '5. Matemática para Data Science e Machine Learning/2. Cálculo/5. A definição de derivadas.mp4',
    '5. Matemática para Data Science e Machine Learning/2. Cálculo/6. Aplicando derivadas.mp4',
    '5. Matemática para Data Science e Machine Learning/2. Cálculo/7. Derivadas para problemas de otimização.mp4',
    '5. Matemática para Data Science e Machine Learning/2. Cálculo/8. Derivadas Parciais.mp4',
    '5. Matemática para Data Science e Machine Learning/3. Álgebra Linear/1. Introdução à algebra linear.mp4',
    '5. Matemática para Data Science e Machine Learning/3. Álgebra Linear/2. O surgimento da algebra linear.mp4',
    '5. Matemática para Data Science e Machine Learning/3. Álgebra Linear/3. Matrizes e Vetores.mp4',
    '5. Matemática para Data Science e Machine Learning/3. Álgebra Linear/4. Operações com matrizes.mp4',
    '5. Matemática para Data Science e Machine Learning/3. Álgebra Linear/5. Transposição e inversão matricial.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/1. Introdução à probabilidade e estatística.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/2. Processos aleatórios e probabilidade.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/3. Lei dos grandes números.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/4. Distribuições de probabilidade.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/5. Independencia de eventos e probabilidade condicional.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/6. Esperança de um processo aleatório.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/7. Variância.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/8. A curva de distribuição Gaussiana - Normal.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/9. Propriedades de uma distribuição gaussiana.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/10. Outros modelos de distribuição.mp4',
    '5. Matemática para Data Science e Machine Learning/4. Probabilidade e estatística/11. Verossimilhança.mp4',
    '6. Fundamentos dos modelos de classificação/1. Modelos de classificação/1 - Apresentação do Curso.mp4',
    '6. Fundamentos dos modelos de classificação/1. Modelos de classificação/2 MNIST .mp4',
    '6. Fundamentos dos modelos de classificação/1. Modelos de classificação/3 Explorando o dataset.mp4',
    '6. Fundamentos dos modelos de classificação/1. Modelos de classificação/4 O classificador binário.mp4',
    '6. Fundamentos dos modelos de classificação/1. Modelos de classificação/5 Medindo a acurácia de um modelo binário.mp4',
    '6. Fundamentos dos modelos de classificação/1. Modelos de classificação/6 Métricas essenciais para modelos de classificação.mp4',
    '6. Fundamentos dos modelos de classificação/1. Modelos de classificação/7 Métricas de Classificação no Python.mp4',
    '6. Fundamentos dos modelos de classificação/1. Modelos de classificação/8 Classificação Multiclasse.mp4',
    '6. Fundamentos dos modelos de classificação/1. Modelos de classificação/9 Classificação Multilabel.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/1 - Apresentação do curso.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/2 - Regressão Linear 1.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/3 - Regressão Linear 2.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/4 - Equação Normal.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/5 - Equação Normal na Prática.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/6 - Gradient Descent.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/7 - Gradient Descent na Prática.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/8 - Regressões Polinomiais 1.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/9 - Regressões Polinomiais 2.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/10 - Balanço Viés-Variança.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/11 - Ridge Regression.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/12 - Ridge Regression na Prática.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/13 - Regressão Logística.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/14 - Custo na Regressão Logística.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/15 - Regressão Logística na Prática.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/16 - Regressão Softmax.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/17 - Treinando Modelo de Softmax.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/18 - Entropia.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/19 - Cross Entropy.mp4',
    '7. Abrindo a caixa preta Como os modelos aprendem/1. Como os modelos de Machine Learning aprendem/20 - Treinando Modelo de Cross Entropy.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/1. Apresentação do curso - editado.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/2. O que é uma árvore de decisão.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/3. Como funciona uma árvore de decisão.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/4. Gini Impurity.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/5. A lógica por trás da função custo.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/6. Overfitting em modelos de árvores.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/7. Decision Trees em problemas de regressão.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/8. Função custo dos modelos de regressão.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/9. Ensemble Learning.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/10. Ensemble Learning na prática.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/11. Bagging.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/12. Random Forests.mp4',
    '8. Modelos inteligentes de árvores/1. Machine Learning com árvores de decisões/13. Feature Importance.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/1. Apresentação do curso.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/2. KMeans na prática.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/3. Como o algoritmo funciona.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/4. Problemas do K-Means.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/5. O método do cotovelo.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/6. Mixture Models.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/7. Definição matemática dos mixture models.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/8. Gaussian Mixture Models.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/9. Gaussian Mixture Models na Prática.mp4',
    '9. Unsupervised Learning/1. Os modelos de aprendizado não supervisionado/10. Detecção de anomalias com GMM.mp4',
]

TOTAL_AULAS = len(ORDEM_AULAS)
SAMPLE_RATE = 48000
CHANNELS = 2


# ============================================================
# AUXILIARES
# ============================================================

def ffmpeg_exe() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def caminho_real(raiz: Path, relativo: str) -> Path:
    """
    Os caminhos embutidos usam '/' para serem seguros no código.
    pathlib converte corretamente para o separador do Windows.
    """
    return raiz / Path(relativo)


def tamanho_legivel(num_bytes: int) -> str:
    valor = float(num_bytes)
    for unidade in ("B", "KB", "MB", "GB", "TB"):
        if valor < 1024 or unidade == "TB":
            return f"{valor:.2f} {unidade}"
        valor /= 1024
    return f"{valor:.2f} TB"


def abrir_no_explorador(caminho: Path):
    alvo = caminho if caminho.is_dir() else caminho.parent
    if os.name == "nt":
        os.startfile(str(alvo))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(alvo)])
    else:
        subprocess.Popen(["xdg-open", str(alvo)])


# ============================================================
# GUI
# ============================================================

class MegaPodcastApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Mega Podcast — Formação Data Science")
        self.geometry("980x760")
        self.minsize(850, 680)

        self.cancelar = False
        self.processando = False
        self.ultimo_arquivo = None

        self._montar_ui()

        if DEFAULT_ROOT.exists():
            self.entry_raiz.insert(0, str(DEFAULT_ROOT))
            self.after(300, self.verificar_arquivos)
        else:
            self.entry_raiz.insert(0, str(DEFAULT_ROOT))

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def _montar_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        titulo = ctk.CTkLabel(
            self,
            text="Mega Podcast — Formação em Data Science e Machine Learning",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        titulo.grid(row=0, column=0, padx=24, pady=(22, 4), sticky="w")

        subtitulo = ctk.CTkLabel(
            self,
            text=(
                f"Ordem fixa embutida: {TOTAL_AULAS} aulas. "
                "O programa não reordena os vídeos."
            ),
            text_color=("gray35", "gray70")
        )
        subtitulo.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        config = ctk.CTkFrame(self)
        config.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="ew")
        config.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            config, text="Pasta raiz do curso:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, columnspan=3, padx=16, pady=(14, 4), sticky="w")

        self.entry_raiz = ctk.CTkEntry(config)
        self.entry_raiz.grid(row=1, column=0, padx=(16, 8), pady=(0, 12), sticky="ew")

        self.btn_pasta = ctk.CTkButton(
            config, text="Selecionar pasta", width=140, command=self.selecionar_pasta
        )
        self.btn_pasta.grid(row=1, column=1, padx=4, pady=(0, 12))

        self.btn_verificar = ctk.CTkButton(
            config, text="Verificar 200 aulas", width=145, command=self.verificar_arquivos
        )
        self.btn_verificar.grid(row=1, column=2, padx=(4, 16), pady=(0, 12))

        ctk.CTkLabel(config, text="Arquivo final:").grid(
            row=2, column=0, padx=16, pady=(0, 4), sticky="w"
        )
        ctk.CTkLabel(config, text="Qualidade AAC:").grid(
            row=2, column=1, padx=4, pady=(0, 4), sticky="w"
        )

        self.entry_saida = ctk.CTkEntry(config)
        self.entry_saida.insert(0, DEFAULT_OUTPUT_NAME)
        self.entry_saida.grid(row=3, column=0, padx=(16, 8), pady=(0, 14), sticky="ew")

        self.combo_bitrate = ctk.CTkComboBox(
            config, values=["128k", "160k", "192k", "256k", "320k"], width=140
        )
        self.combo_bitrate.set("192k")
        self.combo_bitrate.grid(row=3, column=1, padx=4, pady=(0, 14))

        self.label_check = ctk.CTkLabel(
            config,
            text=f"Aguardando verificação dos {TOTAL_AULAS} vídeos.",
            anchor="w"
        )
        self.label_check.grid(
            row=4, column=0, columnspan=3, padx=16, pady=(0, 14), sticky="ew"
        )

        prog = ctk.CTkFrame(self)
        prog.grid(row=3, column=0, padx=24, pady=(0, 12), sticky="ew")
        prog.grid_columnconfigure(0, weight=1)

        self.label_status = ctk.CTkLabel(prog, text="Pronto.", anchor="w")
        self.label_status.grid(row=0, column=0, padx=14, pady=(10, 4), sticky="ew")

        self.progress = ctk.CTkProgressBar(prog)
        self.progress.set(0)
        self.progress.grid(row=1, column=0, padx=14, pady=(0, 4), sticky="ew")

        self.label_percent = ctk.CTkLabel(prog, text="0%")
        self.label_percent.grid(row=2, column=0, padx=14, pady=(0, 8), sticky="e")

        self.log = ctk.CTkTextbox(self, wrap="none")
        self.log.grid(row=4, column=0, padx=24, pady=(0, 12), sticky="nsew")
        self.log.configure(state="disabled")

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.grid(row=5, column=0, padx=24, pady=(0, 22), sticky="ew")
        botoes.grid_columnconfigure(0, weight=1)

        self.btn_iniciar = ctk.CTkButton(
            botoes,
            text="GERAR MEGA PODCAST",
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.iniciar
        )
        self.btn_iniciar.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.btn_cancelar = ctk.CTkButton(
            botoes,
            text="Cancelar",
            width=120,
            height=44,
            state="disabled",
            command=self.solicitar_cancelamento
        )
        self.btn_cancelar.grid(row=0, column=1, padx=6)

        self.btn_abrir = ctk.CTkButton(
            botoes,
            text="Abrir pasta",
            width=120,
            height=44,
            state="disabled",
            command=self.abrir_pasta_saida
        )
        self.btn_abrir.grid(row=0, column=2, padx=(6, 0))

    # --------------------------------------------------------
    # Thread-safe UI
    # --------------------------------------------------------

    def escrever_log(self, texto: str):
        def _do():
            self.log.configure(state="normal")
            self.log.insert("end", texto + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.after(0, _do)

    def status(self, texto: str, fracao: float | None = None):
        def _do():
            self.label_status.configure(text=texto)
            if fracao is not None:
                f = max(0.0, min(1.0, fracao))
                self.progress.set(f)
                self.label_percent.configure(text=f"{f * 100:.1f}%")
        self.after(0, _do)

    # --------------------------------------------------------
    # Pasta e verificação
    # --------------------------------------------------------

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta raiz do curso")
        if not pasta:
            return
        self.entry_raiz.delete(0, "end")
        self.entry_raiz.insert(0, pasta)
        self.verificar_arquivos()

    def obter_raiz(self) -> Path | None:
        txt = self.entry_raiz.get().strip().strip('"')
        if not txt:
            return None
        return Path(txt)

    def verificar_arquivos(self):
        raiz = self.obter_raiz()
        if raiz is None or not raiz.is_dir():
            self.label_check.configure(text="A pasta raiz informada não existe.")
            return False

        encontrados = []
        faltando = []

        for rel in ORDEM_AULAS:
            p = caminho_real(raiz, rel)
            if p.is_file():
                encontrados.append(p)
            else:
                faltando.append(rel)

        self._limpar_log()
        self.escrever_log("=== VERIFICAÇÃO DA CRONOLOGIA ===")
        self.escrever_log(f"Esperados:   {TOTAL_AULAS}")
        self.escrever_log(f"Encontrados: {len(encontrados)}")
        self.escrever_log(f"Faltando:    {len(faltando)}")
        self.escrever_log("")

        if faltando:
            self.label_check.configure(
                text=(
                    f"⚠ {len(encontrados)}/{TOTAL_AULAS} encontrados; "
                    f"{len(faltando)} faltando. O processamento ficará bloqueado."
                )
            )
            self.escrever_log("ARQUIVOS AUSENTES:")
            for rel in faltando:
                self.escrever_log(f"  - {rel}")
            return False

        self.label_check.configure(
            text=f"✓ {TOTAL_AULAS}/{TOTAL_AULAS} vídeos encontrados. Cronologia pronta."
        )
        self.escrever_log("✓ Todos os vídeos da cronologia foram encontrados.")
        self.escrever_log("")
        self.escrever_log("PRIMEIRA AULA:")
        self.escrever_log(f"  001. {ORDEM_AULAS[0]}")
        self.escrever_log("")
        self.escrever_log("ÚLTIMA AULA:")
        self.escrever_log(f"  {TOTAL_AULAS:03d}. {ORDEM_AULAS[-1]}")
        return True

    def _limpar_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    # --------------------------------------------------------
    # Execução
    # --------------------------------------------------------

    def iniciar(self):
        if self.processando:
            return

        raiz = self.obter_raiz()
        if raiz is None or not raiz.is_dir():
            messagebox.showerror("Pasta inválida", "Selecione a pasta raiz correta do curso.")
            return

        # Verificação estrita: não começa com nenhuma aula faltando.
        faltando = [
            rel for rel in ORDEM_AULAS
            if not caminho_real(raiz, rel).is_file()
        ]
        if faltando:
            self.verificar_arquivos()
            messagebox.showerror(
                "Arquivos faltando",
                (
                    f"Há {len(faltando)} aula(s) ausente(s).\n\n"
                    "O programa não vai improvisar a ordem nem pular aulas. "
                    "Veja a lista no log."
                )
            )
            return

        nome = self.entry_saida.get().strip()
        if not nome:
            nome = DEFAULT_OUTPUT_NAME
        if not nome.lower().endswith(".m4a"):
            nome += ".m4a"

        saida = raiz / nome

        if saida.exists():
            ok = messagebox.askyesno(
                "Arquivo já existe",
                f"{saida.name} já existe.\n\nDeseja substituí-lo?"
            )
            if not ok:
                return

        self.cancelar = False
        self.processando = True
        self.ultimo_arquivo = None

        self.btn_iniciar.configure(state="disabled")
        self.btn_cancelar.configure(state="normal")
        self.btn_pasta.configure(state="disabled")
        self.btn_verificar.configure(state="disabled")
        self.btn_abrir.configure(state="disabled")

        self._limpar_log()

        thread = threading.Thread(
            target=self._processar,
            args=(raiz, saida, self.combo_bitrate.get()),
            daemon=True
        )
        thread.start()

    def solicitar_cancelamento(self):
        self.cancelar = True
        self.btn_cancelar.configure(state="disabled")
        self.label_status.configure(text="Cancelamento solicitado…")

    def _processar(self, raiz: Path, saida: Path, bitrate: str):
        temp_dir = None
        combinado_aac = None

        try:
            ffmpeg = ffmpeg_exe()

            self.escrever_log("=== MEGA PODCAST ===")
            self.escrever_log(f"Aulas: {TOTAL_AULAS}")
            self.escrever_log(f"Codec final: AAC {bitrate}")
            self.escrever_log(f"Sample rate: {SAMPLE_RATE} Hz")
            self.escrever_log(f"Canais: {CHANNELS}")
            self.escrever_log("")
            self.escrever_log("A ordem abaixo é a ordem fixa do arquivo de cronologia.")
            self.escrever_log("")

            # Cria o temporário preferencialmente ao lado do arquivo final.
            # Isso evita depender do espaço livre do C: quando a coleção está em outro drive.
            try:
                temp_dir = Path(tempfile.mkdtemp(
                    prefix="_mega_podcast_temp_",
                    dir=str(saida.parent)
                ))
            except Exception:
                temp_dir = Path(tempfile.mkdtemp(prefix="_mega_podcast_temp_"))

            combinado_aac = temp_dir / "audio_completo_temp.aac"

            # Garante arquivo vazio.
            combinado_aac.write_bytes(b"")

            for idx, rel in enumerate(ORDEM_AULAS, start=1):
                if self.cancelar:
                    raise InterruptedError("Processamento cancelado pelo usuário.")

                video = caminho_real(raiz, rel)
                fracao = (idx - 1) / (TOTAL_AULAS + 1)

                self.status(
                    f"Extraindo aula {idx}/{TOTAL_AULAS}: {video.name}",
                    fracao
                )
                self.escrever_log(f"[{idx:03d}/{TOTAL_AULAS}] {rel}")

                # Cada vídeo é codificado uma única vez para AAC/ADTS e anexado
                # ao mesmo arquivo. Não há 200 arquivos intermediários.
                with combinado_aac.open("ab") as destino:
                    cmd = [
                        ffmpeg,
                        "-hide_banner",
                        "-loglevel", "error",
                        "-nostdin",
                        "-i", str(video),
                        "-map", "0:a:0",
                        "-vn",
                        "-sn",
                        "-dn",
                        "-map_metadata", "-1",
                        "-ar", str(SAMPLE_RATE),
                        "-ac", str(CHANNELS),
                        "-c:a", "aac",
                        "-b:a", bitrate,
                        "-f", "adts",
                        "pipe:1",
                    ]

                    creationflags = (
                        subprocess.CREATE_NO_WINDOW
                        if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW")
                        else 0
                    )

                    proc = subprocess.Popen(
                        cmd,
                        stdout=destino,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.DEVNULL,
                        creationflags=creationflags
                    )
                    _, stderr = proc.communicate()

                if proc.returncode != 0:
                    erro = stderr.decode("utf-8", errors="replace").strip()
                    raise RuntimeError(
                        f"Falha na aula {idx}:\n{rel}\n\nFFmpeg:\n{erro}"
                    )

                self.escrever_log("    ✓ áudio anexado")

            if self.cancelar:
                raise InterruptedError("Processamento cancelado pelo usuário.")

            # Remux: AAC já comprimido -> M4A. Sem nova compressão.
            self.status(
                "Finalizando o M4A sem recomprimir o áudio…",
                TOTAL_AULAS / (TOTAL_AULAS + 1)
            )
            self.escrever_log("")
            self.escrever_log("=== FINALIZAÇÃO ===")
            self.escrever_log("Empacotando AAC em M4A (stream copy; sem recompressão)…")

            cmd_final = [
                ffmpeg,
                "-hide_banner",
                "-loglevel", "error",
                "-nostdin",
                "-y",
                "-f", "aac",
                "-i", str(combinado_aac),
                "-map", "0:a:0",
                "-c:a", "copy",
                "-bsf:a", "aac_adtstoasc",
                "-movflags", "+faststart",
                str(saida)
            ]

            creationflags = (
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0
            )

            final = subprocess.run(
                cmd_final,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags
            )

            if final.returncode != 0:
                erro = final.stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"Falha ao criar o M4A final.\n\nFFmpeg:\n{erro}")

            self.ultimo_arquivo = saida
            tamanho = tamanho_legivel(saida.stat().st_size)

            self.status("Concluído.", 1.0)
            self.escrever_log("")
            self.escrever_log("✓ MEGA PODCAST CONCLUÍDO")
            self.escrever_log(f"Arquivo: {saida}")
            self.escrever_log(f"Tamanho: {tamanho}")
            self.escrever_log(f"Aulas incluídas: {TOTAL_AULAS}/{TOTAL_AULAS}")
            self.escrever_log(f"Qualidade: AAC {bitrate}")

            self.after(0, lambda: messagebox.showinfo(
                "Concluído",
                (
                    f"Mega podcast criado com sucesso.\n\n"
                    f"{TOTAL_AULAS} aulas incluídas na cronologia correta.\n"
                    f"Tamanho: {tamanho}\n\n"
                    f"{saida}"
                )
            ))

        except InterruptedError as e:
            self.status("Cancelado.", 0)
            self.escrever_log("")
            self.escrever_log(str(e))
            try:
                if saida.exists():
                    saida.unlink()
            except Exception:
                pass

        except Exception as e:
            self.status("Erro no processamento.")
            self.escrever_log("")
            self.escrever_log("ERRO:")
            self.escrever_log(str(e))

            try:
                if saida.exists():
                    saida.unlink()
            except Exception:
                pass

            self.after(0, lambda msg=str(e): messagebox.showerror("Erro", msg))

        finally:
            if temp_dir is not None:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass

            self.processando = False
            self.after(0, self._restaurar_botoes)

    def _restaurar_botoes(self):
        self.btn_iniciar.configure(state="normal")
        self.btn_cancelar.configure(state="disabled")
        self.btn_pasta.configure(state="normal")
        self.btn_verificar.configure(state="normal")
        self.btn_abrir.configure(
            state="normal" if self.ultimo_arquivo and self.ultimo_arquivo.exists() else "disabled"
        )

    def abrir_pasta_saida(self):
        if self.ultimo_arquivo and self.ultimo_arquivo.exists():
            abrir_no_explorador(self.ultimo_arquivo)


if __name__ == "__main__":
    app = MegaPodcastApp()
    app.mainloop()
