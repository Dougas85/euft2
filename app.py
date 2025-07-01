import os
import pandas as pd
from itertools import chain
import json
from datetime import datetime
import tempfile
from flask import send_file
from flask import Flask, request, render_template, redirect, flash, url_for, session
from placas import (
    placas_scudo2, placas_scudo7, placas_analisadas2, placas_analisadas7,
    placas_especificas2, placas_especificas7, placas_mobi2, placas_mobi7,
    placas_to_lotacao2, placas_to_lotacao7, placas_scudo1, placas_mobi1,
    placas_especificas1, placas_analisadas1, placas_to_lotacao1, placas_scudo3,
    placas_mobi3, placas_especificas3, placas_analisadas3, placas_to_lotacao3,
    placas_scudo4, placas_mobi4, placas_especificas4, placas_analisadas4,
    placas_to_lotacao4, placas_scudo5, placas_mobi5, placas_especificas5,
    placas_analisadas5, placas_to_lotacao5, placas_scudo6, placas_mobi6,
    placas_especificas6, placas_analisadas6, placas_to_lotacao6, placas_scudo8,
    placas_mobi8, placas_especificas8, placas_analisadas8, placas_to_lotacao8, placas_scudo9,
    placas_mobi9, placas_especificas9, placas_analisadas9, placas_to_lotacao9
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Criar diretório de uploads, se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

regioes = {
    'Região 2': {
        'placas_scudo': placas_scudo2,
        'placas_analisadas': placas_analisadas2,
        'placas_especificas': placas_especificas2,
        'placas_mobi': placas_mobi2,
        'placas_to_lotacao': placas_to_lotacao2
    },
    'Região 7': {
        'placas_scudo': placas_scudo7,
        'placas_analisadas': placas_analisadas7,
        'placas_especificas': placas_especificas7,
        'placas_mobi': placas_mobi7,
        'placas_to_lotacao': placas_to_lotacao7
    },
    'Região 1': {
        'placas_scudo': placas_scudo1,
        'placas_analisadas': placas_analisadas1,
        'placas_especificas': placas_especificas1,
        'placas_mobi': placas_mobi1,
        'placas_to_lotacao': placas_to_lotacao1
    },
    'Região 3': {
        'placas_scudo': placas_scudo3,
        'placas_analisadas': placas_analisadas3,
        'placas_especificas': placas_especificas3,
        'placas_mobi': placas_mobi3,
        'placas_to_lotacao': placas_to_lotacao3
    },
    'Região 4': {
        'placas_scudo': placas_scudo4,
        'placas_analisadas': placas_analisadas4,
        'placas_especificas': placas_especificas4,
        'placas_mobi': placas_mobi4,
        'placas_to_lotacao': placas_to_lotacao4
    },
    'Região 5': {
        'placas_scudo': placas_scudo5,
        'placas_analisadas': placas_analisadas5,
        'placas_especificas': placas_especificas5,
        'placas_mobi': placas_mobi5,
        'placas_to_lotacao': placas_to_lotacao5
    },
    'Região 6': {
        'placas_scudo': placas_scudo6,
        'placas_analisadas': placas_analisadas6,
        'placas_especificas': placas_especificas6,
        'placas_mobi': placas_mobi6,
        'placas_to_lotacao': placas_to_lotacao6
    },
    'Região 8': {
        'placas_scudo': placas_scudo8,
        'placas_analisadas': placas_analisadas8,
        'placas_especificas': placas_especificas8,
        'placas_mobi': placas_mobi8,
        'placas_to_lotacao': placas_to_lotacao8
    },
    'Região 9': {
        'placas_scudo': placas_scudo9,
        'placas_analisadas': placas_analisadas9,
        'placas_especificas': placas_especificas9,
        'placas_mobi': placas_mobi9,
        'placas_to_lotacao': placas_to_lotacao9
    }
}


regioes['SPI'] = {
    'placas_scudo': list(set(chain.from_iterable(r['placas_scudo'] for r in regioes.values()))),
    'placas_analisadas': list(set(chain.from_iterable(r['placas_analisadas'] for r in regioes.values()))),
    'placas_especificas': list(set(chain.from_iterable(r['placas_especificas'] for r in regioes.values()))),
    'placas_mobi': list(set(chain.from_iterable(r['placas_mobi'] for r in regioes.values()))),
    'placas_to_lotacao': list(set(chain.from_iterable(r['placas_to_lotacao'] for r in regioes.values()))),
}





# Função para calcular o tempo de utilização
def calcular_tempo_utilizacao(row):
    try:
        partida = datetime.strptime(f"{row['Data Partida'].date()} {row['Hora Partida']}", "%Y-%m-%d %H:%M")
        if pd.isna(row['Data Retorno']) or pd.isna(row['Hora Retorno']):
            return 'Veículo sem retorno registrado'
        retorno = datetime.strptime(f"{row['Data Retorno'].date()} {row['Hora Retorno']}", "%Y-%m-%d %H:%M")
    except Exception as e:
        return f"Erro ao converter data/hora: {e}"
    
    duracao = (retorno - partida).total_seconds() / 3600
    if row['Almoço?'] == 'S':
        duracao -= 1
    return round(duracao, 2)

# Formatar tempo para exibição
def formatar_tempo_horas_minutos(tempo):
    if isinstance(tempo, (int, float)):
        horas = int(tempo)
        minutos = int((tempo - horas) * 60)
        return f"{horas}h {minutos}m"
    return tempo

# Verificar placas sem saída
def verificar_placas_sem_saida(df_original, placas_analisadas):
    placas_com_saida = set(df_original[df_original['Data Partida'].notna()]['Placa'].unique())
    placas_sem_saida = placas_analisadas - placas_com_saida
    return sorted(placas_sem_saida)

def veiculos_sem_retorno(df, placas_analisadas):
    df = df.copy()
    df['Data Partida'] = pd.to_datetime(df['Data Partida'], format='%d/%m/%Y', errors='coerce')
    df['Data Retorno'] = pd.to_datetime(df['Data Retorno'], format='%d/%m/%Y', errors='coerce')
    df['Placa'] = df['Placa'].str.strip().str.upper()

    # Filtra registros com placa analisada e com saída, mas sem retorno
    df_filtrado = df[
        (df['Placa'].isin(placas_analisadas)) &
        (df['Data Partida'].notna()) &
        (df['Data Retorno'].isna())
    ]

    # Pega as últimas saídas sem retorno por veículo
    df_resultado = df_filtrado.sort_values('Data Partida', ascending=False).drop_duplicates(subset='Placa')

    return df_resultado[['Placa', 'Data Partida', 'Matrícula Condutor', 'Unidade em Operação']]


# Verifica se linha está correta (tempo e distância)
def verificar_corretude_linha(row, placas_scudo, placas_especificas, placas_mobi):
    tempo = row['Tempo Utilizacao']
    dist = row['Distancia Percorrida']
    placa = row['Placa']

    if isinstance(tempo, str):  # erro de cálculo
        return False

    if placa in placas_scudo:
        return 1 <= tempo <= 8 and 10 <= dist <= 120
    elif placa in placas_especificas:
        return 1 <= tempo <= 8 and 8 <= dist <= 100
    elif placa in placas_mobi:
        return 1 <= tempo <= 8 and 6 <= dist <= 80
    else:
        return 2 <= tempo <= 8 and 6 <= dist <= 80

# Gerar motivo de erro
def motivo_erro(row, placas_scudo, placas_especificas, placas_mobi):
    if row['Correto']:
        return ''
    if isinstance(row['Tempo Utilizacao'], str):
        return row['Tempo Utilizacao']
    tempo = row['Tempo Utilizacao']
    dist = row['Distancia Percorrida']
    placa = row['Placa']

    if placa in placas_scudo:
        if not (1 <= tempo <= 8):
            return f"Tempo fora do intervalo (SCUDO): {tempo:.1f}h"
        if not (10 <= dist <= 120):
            return f"Distância fora do intervalo (SCUDO): {dist:.1f}km"
    elif placa in placas_especificas:
        if not (1 <= tempo <= 8):
            return f"Tempo fora do intervalo (FIORINO): {tempo:.1f}h"
        if not (8 <= dist <= 100):
            return f"Distância fora do intervalo (FIORINO): {dist:.1f}km"
    elif placa in placas_mobi:
        if not (1 <= tempo <= 8):
            return f"Tempo fora do intervalo (MOBI): {tempo:.1f}h"
        if not (6 <= dist <= 80):
            return f"Distância fora do intervalo (MOBI): {dist:.1f}km"
    else:
        if not (2 <= tempo <= 8):
            return f"Tempo fora do intervalo: {tempo:.1f}h"
        if not (6 <= dist <= 80):
            return f"Distância fora do intervalo: {dist:.1f}km"
    return 'Erro não identificado'

def calcular_euft(df, dias_uteis_mes, placas_scudo, placas_especificas, placas_mobi, placas_analisadas, placas_to_lotacao):

    # 1) Cópia e pré-processamento geral
    df = df.copy()
    df['Data Partida'] = pd.to_datetime(df['Data Partida'], format='%d/%m/%Y', errors='coerce')
    df['Data Retorno'] = pd.to_datetime(df['Data Retorno'], format='%d/%m/%Y', errors='coerce')
    df['Placa'] = df['Placa'].str.strip().str.upper()

    df['Tempo Utilizacao'] = df.apply(calcular_tempo_utilizacao, axis=1)
    df['Distancia Percorrida'] = df['Hod. Retorno'] - df['Hod. Partida']

    # 2) Calcular DIAS REGISTRADOS (inclusive com erros ou campos faltantes)
    df_registros = df[df['Placa'].isin(placas_analisadas)]
    registros_distintos = df_registros.groupby(['Placa', 'Data Partida', 'Matrícula Condutor']).size().reset_index(name='count')
    dias_registrados_por_placa = registros_distintos.groupby('Placa')['count'].count().reset_index()
    dias_registrados_por_placa.rename(columns={'count': 'Dias_Totais'}, inplace=True)

    def is_preenchido(col):
        return col.astype(str).str.strip().str.lower().replace('nan', '') != ''

    df_validos = df[
        df['Placa'].isin(placas_analisadas) & (
            is_preenchido(df['Nº Distrito']) |
            is_preenchido(df['Nº LCE']) |
            is_preenchido(df['Nº LTU'])
        )
    ]

    df_agrupado = df_validos.groupby(['Placa', 'Data Partida', 'Matrícula Condutor']).agg({
        'Tempo Utilizacao': 'sum',
        'Distancia Percorrida': 'sum',
        'Lotacao Patrimonial': 'first',
        'Unidade em Operação': 'first'
    }).reset_index()

    # 4) Verificar corretude
    df_agrupado['Correto'] = df_agrupado.apply(lambda row: verificar_corretude_linha(row, placas_scudo, placas_especificas, placas_mobi), axis=1)

    # 5) Motivo do erro e formatação
    df_agrupado['Motivo Erro'] = df_agrupado.apply(lambda row: motivo_erro(row, placas_scudo, placas_especificas, placas_mobi), axis=1)
    df_agrupado['Tempo Utilizacao Formatado'] = df_agrupado['Tempo Utilizacao'].map(formatar_tempo_horas_minutos)

    # 6) Calcular Dias Corretos
    resultados_por_veiculo = df_agrupado.groupby('Placa').agg(
        Dias_Corretos=('Correto', 'sum')
    ).reset_index()

    # 7) Mesclar com Dias Totais
    resultados_por_veiculo = resultados_por_veiculo.merge(dias_registrados_por_placa, on='Placa', how='outer')
    resultados_por_veiculo['Dias_Corretos'] = resultados_por_veiculo['Dias_Corretos'].fillna(0).astype(int)
    resultados_por_veiculo['Dias_Totais'] = resultados_por_veiculo['Dias_Totais'].fillna(0).astype(int)

    # 8) Calcular adicional e EUFT
    resultados_por_veiculo['Adicional'] = resultados_por_veiculo['Dias_Totais'].apply(
        lambda x: max(0, 18 - x) if x < 18 else 0
    )

    resultados_por_veiculo['EUFT'] = (
        resultados_por_veiculo['Dias_Corretos'] / 
        (resultados_por_veiculo['Dias_Totais'] + resultados_por_veiculo['Adicional'])
    ).fillna(0)

    resultados_por_veiculo['EUFT (%)'] = (
        resultados_por_veiculo['EUFT'] * 100
    ).map(lambda x: f"{x:.2f}".replace('.', ',') + '%')

    # 9) Adicionar linha TOTAL
    total_veiculos = resultados_por_veiculo.shape[0]
    total_dias_corretos = resultados_por_veiculo['Dias_Corretos'].sum()
    total_dias_totais = resultados_por_veiculo['Dias_Totais'].sum()
    total_adicional = resultados_por_veiculo['Adicional'].sum()
    media_geral_euft = (total_dias_corretos / (total_dias_totais + total_adicional)) if (total_dias_totais + total_adicional) > 0 else 0
    media_geral_euft_percentual = f"{media_geral_euft * 100:.2f}".replace('.', ',') + '%'

    linha_total = pd.DataFrame([{
        'Placa': 'TOTAL',
        'Dias_Totais': total_dias_totais,
        'Dias_Corretos': total_dias_corretos,
        'Adicional': total_adicional,
        'EUFT': media_geral_euft,
        'EUFT (%)': media_geral_euft_percentual
    }])

    resultados_por_veiculo = pd.concat([resultados_por_veiculo, linha_total], ignore_index=True)

    # 10) Retornar também os erros
    df_erros = df_agrupado[~df_agrupado['Correto']].copy()

    return resultados_por_veiculo, df_erros

def veiculos_sem_retorno(df1, placas_analisadas):
    df1['Placa'] = df1['Placa'].astype(str).str.strip().str.upper()
    df1['Data Retorno'] = df1['Data Retorno'].astype(str).str.strip().replace(['', 'nan', 'Nat'],pd.NA)
    df1['Data Retorno'] = df1['Data Retorno'].astype(str).str.strip().replace(['', 'nan', 'Nat'],pd.NA)
placas_sem_retorno - df1[
    (df1['Placa'].isin(placas_analisadas)) &
    (df1['Data Retorno'].isna()) &
    (df1['Hora Retorno'].isna())
].copy()
return placas_sem_retorno


@app.route('/', methods=['GET', 'POST'])
def index():
    placas_scudo = []
    placas_analisadas = []
    placas_especificas = []
    placas_mobi = []
    placas_to_lotacao = []
    region = None

    if request.method == 'POST':
        region = request.form.get('region')

        # Seleciona as listas de placas com base na região
        if region == 'Região 7':
            placas_scudo = placas_scudo7
            placas_analisadas = placas_analisadas7
            placas_especificas = placas_especificas7
            placas_mobi = placas_mobi7
            placas_to_lotacao = placas_to_lotacao7
        elif region == 'Região 2':
            placas_scudo = placas_scudo2
            placas_analisadas = placas_analisadas2
            placas_especificas = placas_especificas2
            placas_mobi = placas_mobi2
            placas_to_lotacao = placas_to_lotacao2
        elif region == 'Região 1':
            placas_scudo = placas_scudo1
            placas_analisadas = placas_analisadas1
            placas_especificas = placas_especificas1
            placas_mobi = placas_mobi1
            placas_to_lotacao = placas_to_lotacao1
        elif region == 'Região 3':
            placas_scudo = placas_scudo3
            placas_analisadas = placas_analisadas3
            placas_especificas = placas_especificas3
            placas_mobi = placas_mobi3
            placas_to_lotacao = placas_to_lotacao3
        elif region == 'Região 4':
            placas_scudo = placas_scudo4
            placas_analisadas = placas_analisadas4
            placas_especificas = placas_especificas4
            placas_mobi = placas_mobi4
            placas_to_lotacao = placas_to_lotacao4
        elif region == 'Região 5':
            placas_scudo = placas_scudo5
            placas_analisadas = placas_analisadas5
            placas_especificas = placas_especificas5
            placas_mobi = placas_mobi5
            placas_to_lotacao = placas_to_lotacao5
        elif region == 'Região 6':
            placas_scudo = placas_scudo6
            placas_analisadas = placas_analisadas6
            placas_especificas = placas_especificas6
            placas_mobi = placas_mobi6
            placas_to_lotacao = placas_to_lotacao6
        elif region == 'Região 8':
            placas_scudo = placas_scudo8
            placas_analisadas = placas_analisadas8
            placas_especificas = placas_especificas8
            placas_mobi = placas_mobi8
            placas_to_lotacao = placas_to_lotacao8
        elif region == 'Região 9':
            placas_scudo = placas_scudo9
            placas_analisadas = placas_analisadas9
            placas_especificas = placas_especificas9
            placas_mobi = placas_mobi9
            placas_to_lotacao = placas_to_lotacao9
        # Adicione mais regiões conforme necessário

        # Validação dos arquivos
        file1 = request.files.get('file1')
        file2 = request.files.get('file2')

        if not file1 or not file2:
            flash('Ambos os arquivos devem ser enviados.', 'danger')
            return redirect(request.url)

        if file1.filename == '' or file2.filename == '':
            flash('Ambos os arquivos devem ser selecionados.', 'danger')
            return redirect(request.url)

        try:
            # Salva arquivos temporariamente
            path1 = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
            path2 = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
            file1.save(path1)
            file2.save(path2)

            # Lê arquivos CSV
            df1 = pd.read_csv(path1, delimiter=';', encoding='utf-8')

            # Lê a planilha df2, pulando 4 linhas e definindo colunas manualmente
            colunas_df2 = ['Data Emissão', 'Placa', 'N° OS', 'STATUS OS', 'SE', 'SE SIGLA', 'Extra']
            df2 = pd.read_csv(path2, delimiter=';', skiprows=3, names=colunas_df2, encoding='utf-8')
            placas_sem_retorno = veiculos_sem_retorno(df1, placas_analisadas)
            """print(placas_sem_retorno)  # Mostra o DataFrame retornado"""

            # Remova ou comente a linha abaixo para evitar erro, pois 'df' ainda não foi criada
            # placas_sem_retorno = veiculos_sem_retorno(df, placas_analisadas)

            
            # Limpeza e normalização da df2
            df2['Placa'] = df2['Placa'].str.replace(r'\s+', '', regex=True).str.upper()
            df2['STATUS OS'] = df2['STATUS OS'].astype(str).str.strip().str.upper()

            # Concatena os dois DataFrames
            df_original = pd.concat([df1, df2], ignore_index=True)

            # Normalização e pré-processamento
            df_original.columns = df_original.columns.str.strip()
            if 'Placa' in df_original.columns:
                df_original['Placa'] = df_original['Placa'].astype(str).str.strip().str.upper()

            if 'Data Partida' not in df_original.columns:
                raise ValueError("Coluna 'Data Partida' não encontrada no arquivo.")

            df = df_original.dropna(subset=['Data Retorno', 'Hora Retorno', 'Hod. Retorno'])

            resultados_veiculo, erros = calcular_euft(df, 20, placas_scudo, placas_especificas, placas_mobi, placas_analisadas, placas_to_lotacao)
            placas_faltantes = verificar_placas_sem_saida(df_original, placas_analisadas)

            # Filtra placas com Status OS "APROVADA" ou "ABERTA" (em manutenção) — usando df_original!
            placas_em_manutencao = df2[df2['STATUS OS'].isin(['APROVADA', 'ABERTA'])]['Placa'].unique()
            
            # Remove dinamicamente essas placas da lista de veículos sem saída

            placas_faltantes = [placa for placa in placas_faltantes if placa not in placas_em_manutencao]
        
            veiculos_sem_retorno_df = veiculos_sem_retorno(df1, placas_analisadas)
            
            """placas_sem_retorno = veiculos_sem_retorno(df1, placas_analisadas)"""


        except Exception as e:
            return f"Ocorreu um erro ao processar os arquivos: {e}"

        # Limpeza de colunas indesejadas
        if 'Tempo Utilizacao' in erros.columns:
            erros = erros.drop(columns=['Tempo Utilizacao'])
        if 'Correto' in erros.columns:
            erros = erros.drop(columns=['Correto'])

        resultados_html = ""
        def extrair_lotacao(val):
            if isinstance(val, str):
                return val
            elif isinstance(val, (list, tuple)):
                return val[0] if len(val) > 0 else ''
            return ''

        resultados_veiculo['lotacao_patrimonial'] = resultados_veiculo['Placa'].map(lambda p: extrair_lotacao(placas_to_lotacao.get(p)))


        for i, row in resultados_veiculo.iterrows():
            euft_percent = f"{row['EUFT'] * 100:.2f}".replace('.', ',') + '%'
            resultados_html += f"<tr><td>{i + 1}</td><td>{row['Placa']}</td><td>{row['lotacao_patrimonial']}</td><td>{row['Dias_Corretos']}</td><td>{row['Dias_Totais']}</td><td>{row['Adicional']}</td><td>{euft_percent}</td></tr>"

        resultados_por_unidade = resultados_veiculo.groupby('lotacao_patrimonial').agg({
            'Dias_Corretos': 'sum',
            'Dias_Totais': 'sum',
            'Adicional': 'sum',
            'EUFT': 'mean'
        }).reset_index().sort_values(by='EUFT', ascending=False)

        resultados_html += "<h3 class='mt-4'>Resultados</h3>"
        resultados_html += "<table id='unidadeTable' class='table table-bordered table-striped mt-2'>"
        resultados_html += "<thead><tr><th>Id</th><th>Lotação Patrimonial</th><th>Lançamentos Corretos</th><th>Lançamentos Totais</th><th>Adicional</th><th>EUFT Médio</th></tr></thead><tbody>"

        for i, row in resultados_por_unidade.iterrows():
            euft_unidade_percent = f"{row['EUFT'] * 100:.2f}".replace('.', ',') + '%'
            resultados_html += f"<tr><td>{i + 1}</td><td>{row['lotacao_patrimonial']}</td><td>{row['Dias_Corretos']}</td><td>{row['Dias_Totais']}</td><td>{row['Adicional']}</td><td>{euft_unidade_percent}</td></tr>"

        resultados_html += "</tbody></table>"
        
        erros_html = ""
        for i, row in erros.iterrows():
            erros_html += f"<tr><td>{i + 1}</td><td>{row['Placa']}</td><td>{row['Data Partida']}</td><td>{row['Distancia Percorrida']}</td><td>{row['Lotacao Patrimonial']}</td><td>{row['Unidade em Operação']}</td><td>{row['Motivo Erro']}</td><td>{row['Tempo Utilizacao Formatado']}</td></tr>"

        veiculos_sem_saida_html = ""
        for i, placa in enumerate(placas_faltantes, start=1):
            valores = placas_to_lotacao.get(placa)

            if isinstance(valores, str):
                partes = valores.split(" - ")
                if len(partes) == 2:
                    lotacao_patrimonial, CAE = partes
                else:
                    lotacao_patrimonial = partes[0]
                    CAE = " "
            elif isinstance(valores, (list, tuple)):
                lotacao_patrimonial = valores[0] if len(valores) > 0 else " "
                CAE = valores[1] if len(valores) > 1 else " "
            else:
                lotacao_patrimonial = " "
                CAE = " "

            veiculos_sem_saida_html += f"""
            <tr>
                <td>{i}</td>
                <td>{placa}</td>
                <td>{lotacao_patrimonial}</td>
                <td>{CAE}</td>
                <td><span class='badge bg-warning text-dark'>Sem saída</span></td>
            </tr>
            """
        veiculos_sem_retorno_data = []  # Garante que sempre exista
        try:
            for i, row in enumerate(placas_sem_retorno.iterrows(), start=1):
                _, data = row
                placa = data['Placa']
                unidade = data.get('Unidade em Operação', '')

                data_partida_str = str(data.get('Data Partida', '')).strip()
                hora_partida_str = str(data.get('Hora Partida', '')).strip()

                try:
                    datahora_partida = datetime.strptime(f"{data_partida_str} {hora_partida_str}", "%d/%m/%Y %H:%M)
                except ValueError:
                    datahora_partida = None

                mais_de_sete_horas = False
                if pd.notna(datahora_partida):
                    tempo_decorrido = datetime.now() - datahora_partida
                    mais_de_sete_horas = tempo_decorrido > timedelta(hours=7)
                print(f"{placa} - + 7h: {mais_de_sete_horas} - Partida: {datahora_partida}")
           

        # Continuação do seu processamento
        impacto_unidade = erros.groupby('Unidade em Operação').size().reset_index(name='Qtd_Erros')
        impacto_unidade.columns = ['Unidade', 'Qtd_Erros']
        # Ordena pela quantidade de erros em ordem decrescente e seleciona os 15 maiores
        impacto_unidade = impacto_unidade.sort_values(by='Qtd_Erros', ascending=False).head(15)
        labels = impacto_unidade['Unidade'].tolist()
        valores = impacto_unidade['Qtd_Erros'].tolist()

        temp_csv_path = os.path.join(tempfile.gettempdir(), "erros_euft.csv")
        temp_excel_path = os.path.join(tempfile.gettempdir(), "erros_euft.xlsx")
        erros.to_csv(temp_csv_path, index=False, sep=';', encoding='utf-8-sig')
        erros.to_excel(temp_excel_path, index=False)

        """# Salvasr veículos sem saída
        temp_csv_path_sem_saida = os.path.join(tempfile.gettempdir(), "sem_saida_euft.csv")
        temp_excel_path_sem_saida = os.path.join(tempfile.gettempdir(), "sem_saida_euft.xlsx")
        sem_saida.to_csv(temp_csv_path, index=False, sep=';', encoding='utf-8-sig')
        sem_saida.to_excel(temp_excel_path, index=False)"""


        return render_template('index.html',
                            resultados=resultados_html,
                            erros=erros_html,
                            grafico_labels=json.dumps(labels),
                            grafico_dados=json.dumps(valores),
                            veiculos_sem_saida=veiculos_sem_saida_html,
                            veiculos_sem_retorno_data=veiculos_sem_retorno_data,
                            link_csv='/download/erros_csv',
                            link_excel='/download/erros_excel',
                            regioes=regioes,
                            region_selecionada=region)


    return render_template('index.html', regioes=regioes)


@app.route('/download/erros_csv')
def download_erros_csv():
    temp_csv_path = os.path.join(tempfile.gettempdir(), "erros_euft.csv")
    return send_file(temp_csv_path, as_attachment=True, download_name="Erros_EUFT.csv")

@app.route('/download/erros_excel')
def download_erros_excel():
    temp_excel_path = os.path.join(tempfile.gettempdir(), "erros_euft.xlsx")
    return send_file(temp_excel_path, as_attachment=True, download_name="Erros_EUFT.xlsx")

"""@app.route('/download/sem_saida_csv')
def download_sem_saida_csv():
    temp_csv_path = os.path.join(tempfile.gettempdir(), "sem_saida_euft.csv")
    return send_file(temp_csv_path, as_attachment=True, download_name="Sem_Saida_EUFT.csv")

@app.route('/download/sem_saida_excel')
def download_sem_saida_excel():
    temp_excel_path = os.path.join(tempfile.gettempdir(), "sem_saida_euft.xlsx")
    return send_file(temp_excel_path, as_attachment=True, download_name="Sem_Saida_EUFT.xlsx")"""

if __name__ == '__main__':
    app.run(debug=True, port=5002)
