import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from itertools import chain
import itertools
import pandas as pd
import pytz
from flask import Flask, request, render_template, redirect, flash
from flask import send_file


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


def formatar_tempo_horas_minutos(tempo):
    if isinstance(tempo, (int, float)):
        horas = int(tempo)
        minutos = int((tempo - horas) * 60)
        return f"{horas}h {minutos}m"
    return tempo


def verificar_placas_sem_saida(df_original, placas_analisadas):
    placas_com_saida = set(df_original[df_original['Data Partida'].notna()]['Placa'].unique())
    placas_sem_saida = placas_analisadas - placas_com_saida
    return sorted(placas_sem_saida)


def veiculos_sem_retorno(df1, placas_analisadas):
    df1['Placa'] = df1['Placa'].astype(str).str.strip().str.upper()
    df1['Data Retorno'] = df1['Data Retorno'].astype(str).str.strip().replace(['', 'nan', 'NaT'], pd.NA)
    df1['Hora Retorno'] = df1['Hora Retorno'].astype(str).str.strip().replace(['', 'nan', 'NaT'], pd.NA)

    placas_sem_retorno = df1[
        (df1['Placa'].isin(placas_analisadas)) &
        (df1['Data Retorno'].isna()) &
        (df1['Hora Retorno'].isna())
    ].copy()

    return placas_sem_retorno


def verificar_corretude_linha(row, placas_scudo, placas_especificas, placas_mobi):
    tempo = row['Tempo Utilizacao']
    dist = row['Distancia Percorrida']
    placa = row['Placa']

    if isinstance(tempo, str):
        return False

    if placa in placas_scudo:
        return 1 <= tempo <= 8 and 10 <= dist <= 120
    elif placa in placas_especificas:
        return 1 <= tempo <= 8 and 8 <= dist <= 100
    elif placa in placas_mobi:
        return 1 <= tempo <= 8 and 6 <= dist <= 80
    else:
        return 2 <= tempo <= 8 and 6 <= dist <= 80


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
            return f"Tempo fora do intervalo (MOTO): {tempo:.1f}h"
        if not (6 <= dist <= 80):
            return f"Distância fora do intervalo (MOTO): {dist:.1f}km"
    return 'Erro não identificado'


def calcular_euft(df, dias_uteis_mes, placas_scudo, placas_especificas, placas_mobi, placas_analisadas, placas_to_lotacao):
    df = df.copy()
    df['Data Partida'] = pd.to_datetime(df['Data Partida'], format='%d/%m/%Y', errors='coerce')
    df['Data Retorno'] = pd.to_datetime(df['Data Retorno'], format='%d/%m/%Y', errors='coerce')
    df['Placa'] = df['Placa'].astype(str).str.strip().str.upper()

    df = df[df['Data Partida'].dt.weekday < 5].copy()

    df['Tempo Utilizacao'] = df.apply(calcular_tempo_utilizacao, axis=1)
    df['Distancia Percorrida'] = df['Hod. Retorno'] - df['Hod. Partida']

    df_validos = df[df['Placa'].isin(placas_analisadas)].copy()

    df_agrupado = df_validos.groupby(['Placa', 'Data Partida', 'Matrícula Condutor']).agg({
        'Tempo Utilizacao': 'sum',
        'Distancia Percorrida': 'sum',
        'Lotacao Patrimonial': 'first',
        'Unidade em Operação': 'first'
    }).reset_index()

    df_agrupado['Correto'] = df_agrupado.apply(
        lambda row: verificar_corretude_linha(row, placas_scudo, placas_especificas, placas_mobi), axis=1
    )
    df_agrupado['Motivo Erro'] = df_agrupado.apply(
        lambda row: motivo_erro(row, placas_scudo, placas_especificas, placas_mobi), axis=1
    )
    df_agrupado['Tempo Utilizacao Formatado'] = df_agrupado['Tempo Utilizacao'].map(formatar_tempo_horas_minutos)

    resultados_por_veiculo = (
        df_agrupado.groupby('Placa')
        .agg(Dias_Corretos=('Correto', 'sum'))
        .reset_index()
    )

    registros_distintos = (
        df_validos.groupby(['Placa', 'Data Partida', 'Matrícula Condutor'])
        .size()
        .reset_index(name='count')
    )
    dias_registrados_por_placa = (
        registros_distintos.groupby('Placa')['count']
        .count()
        .reset_index()
        .rename(columns={'count': 'Dias_Totais'})
    )

    resultados_por_veiculo = resultados_por_veiculo.merge(dias_registrados_por_placa, on='Placa', how='outer')
    resultados_por_veiculo['Dias_Corretos'] = resultados_por_veiculo['Dias_Corretos'].fillna(0).astype(int)
    resultados_por_veiculo['Dias_Totais'] = resultados_por_veiculo['Dias_Totais'].fillna(0).astype(int)

    dias_uteis_relatorio = df.loc[
        df['Data Partida'].dt.weekday < 5, 'Data Partida'
    ].dropna().dt.date.nunique()

    def calcular_adicional(row):
        minimo_uso = min(18, dias_uteis_relatorio)
        adicional = max(0, minimo_uso - row['Dias_Totais'])
        return adicional

    resultados_por_veiculo['Adicional'] = resultados_por_veiculo.apply(calcular_adicional, axis=1)

    for placa in placas_analisadas:
        if placa not in resultados_por_veiculo['Placa'].values:
            resultados_por_veiculo = pd.concat([resultados_por_veiculo, pd.DataFrame([{
                'Placa': placa,
                'Dias_Corretos': 0,
                'Dias_Totais': 0,
                'Adicional': min(18, dias_uteis_relatorio),
                'EUFT': 0,
                'EUFT (%)': '0,00%'
            }])], ignore_index=True)

    resultados_por_veiculo['Dias_Corretos'] = resultados_por_veiculo['Dias_Corretos'].astype(int)
    resultados_por_veiculo['Dias_Totais'] = resultados_por_veiculo['Dias_Totais'].astype(int)
    resultados_por_veiculo['Adicional'] = resultados_por_veiculo['Adicional'].astype(int)

    resultados_por_veiculo['EUFT'] = (
        resultados_por_veiculo['Dias_Corretos'] /
        (resultados_por_veiculo['Dias_Totais'] + resultados_por_veiculo['Adicional'])
    ).fillna(0)

    resultados_por_veiculo['EUFT'] = resultados_por_veiculo['EUFT'].round(4)

    resultados_por_veiculo['EUFT (%)'] = (
        (resultados_por_veiculo['EUFT'] * 100)
        .round(2)
        .astype(str)
        .str.replace('.', ',') + '%'
    )

    total_dias_corretos = resultados_por_veiculo['Dias_Corretos'].sum()
    total_dias_totais = resultados_por_veiculo['Dias_Totais'].sum()
    total_adicional = resultados_por_veiculo['Adicional'].sum()

    media_geral_euft = (
        total_dias_corretos / (total_dias_totais + total_adicional)
        if (total_dias_totais + total_adicional) > 0 else 0
    )

    media_geral_euft = round(media_geral_euft, 4)
    media_geral_euft_percentual = f"{round(media_geral_euft * 100, 2):.2f}".replace('.', ',') + '%'

    linha_total = pd.DataFrame([{
        'Placa': 'TOTAL',
        'Dias_Totais': total_dias_totais,
        'Dias_Corretos': total_dias_corretos,
        'Adicional': total_adicional,
        'EUFT': media_geral_euft,
        'EUFT (%)': media_geral_euft_percentual
    }])

    resultados_por_veiculo = pd.concat([resultados_por_veiculo, linha_total], ignore_index=True)

    df_erros = df_agrupado[~df_agrupado['Correto']].copy()

    return resultados_por_veiculo, df_erros, media_geral_euft


@app.route('/', methods=['GET', 'POST'])
def index():
    placas_scudo = []
    placas_analisadas = []
    placas_especificas = []
    placas_mobi = []
    placas_to_lotacao = []
    media_geral_euft = None
    region = None

    if request.method == 'POST':
        region = request.form.get('region')

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

        file1 = request.files.get('file1')
        file2 = request.files.get('file2')

        if not file1 or not file2:
            flash('Ambos os arquivos devem ser enviados.', 'danger')
            return redirect(request.url)

        if file1.filename == '' or file2.filename == '':
            flash('Ambos os arquivos devem ser selecionados.', 'danger')
            return redirect(request.url)

        try:
            path1 = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
            path2 = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
            file1.save(path1)
            file2.save(path2)

            # ── Leitura dos arquivos ──
            df1 = pd.read_csv(path1, delimiter=';', encoding='utf-8')
            df1['Data Retorno'] = df1['Data Retorno'].astype(str).str.strip().replace('', pd.NA)
            df1['Hora Retorno'] = df1['Hora Retorno'].astype(str).str.strip().replace('', pd.NA)

            colunas_df2 = ['Data Emissão', 'Placa', 'N° OS', 'STATUS OS', 'SE', 'SE SIGLA', 'Extra']
            df2 = pd.read_csv(path2, delimiter=';', skiprows=3, names=colunas_df2, encoding='utf-8')

            # ── Normalização df1 ──
            df1['Placa'] = df1['Placa'].astype(str).str.strip().str.upper()
            df1['Data Partida'] = pd.to_datetime(df1['Data Partida'], dayfirst=True, errors='coerce')

            # ── [AJUSTE] Identificar placas com saída HOJE ──
            fuso_brasilia = pytz.timezone("America/Sao_Paulo")
            hoje_data = datetime.now(fuso_brasilia).date()
            placas_com_saida_hoje = df1[df1['Data Partida'].dt.date == hoje_data]['Placa'].unique()

            # ── Normalização df2 ──
            df2['Placa'] = df2['Placa'].str.replace(r'\s+', '', regex=True).str.upper()
            df2['STATUS OS'] = df2['STATUS OS'].astype(str).str.strip().str.upper()

            # ── Veículos sem retorno ──
            placas_sem_retorno = veiculos_sem_retorno(df1, placas_analisadas)

            # ── Normalização do dicionário de lotação ──
            def normalizar_placa(p):
                if p is None:
                    return ""
                return str(p).upper().strip().replace(" ", "")

            placas_to_lotacao_normalizado = {
                normalizar_placa(k): v
                for k, v in placas_to_lotacao.items()
            }

            def obter_lotacao_por_placa(placa):
                chave = normalizar_placa(placa)
                valores = placas_to_lotacao_normalizado.get(chave)
                if not valores:
                    return ""
                if isinstance(valores, str):
                    return valores.split(" - ")[0]
                return valores[0] if len(valores) > 0 else ""

            def obter_cae_por_placa(placa):
                chave = normalizar_placa(placa)
                valores = placas_to_lotacao_normalizado.get(chave)
                if not valores:
                    return ""
                if isinstance(valores, str):
                    partes = valores.split(" - ")
                    return partes[1].replace("CAE ", "") if len(partes) > 1 else ""
                return valores[1].replace("CAE ", "") if len(valores) > 1 else ""

            # ── [AJUSTE] Manutenção com filtro de saída hoje ──
            df_manutencao = df2[df2['STATUS OS'].isin(['APROVADA', 'ABERTA'])].copy()
            # Remove placas que saíram hoje (não estão mais em manutenção efetiva)
            df_manutencao = df_manutencao[~df_manutencao['Placa'].isin(placas_com_saida_hoje)]
            # Filtra apenas da região selecionada
            df_manutencao = df_manutencao[df_manutencao['Placa'].isin(placas_analisadas)]

            df_manutencao['Placa'] = df_manutencao['Placa'].apply(normalizar_placa)
            df_manutencao['Lotacao'] = df_manutencao['Placa'].apply(obter_lotacao_por_placa)
            df_manutencao['CAE'] = df_manutencao['Placa'].apply(obter_cae_por_placa)
            df_manutencao['Data Emissão'] = pd.to_datetime(df_manutencao['Data Emissão'], dayfirst=True, errors='coerce')

            hoje_naive = datetime.now(fuso_brasilia).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            df_manutencao['Dias Parados'] = (hoje_naive - df_manutencao['Data Emissão']).dt.days

            # Lista de placas em manutenção (já filtrada — sem as que saíram hoje)
            placas_em_manutencao = df_manutencao['Placa'].unique()

            # ── Salvar arquivos de manutenção ──
            temp_csv_path_manutencao = os.path.join(tempfile.gettempdir(), "manutencao_euft.csv")
            temp_excel_path_manutencao = os.path.join(tempfile.gettempdir(), "manutencao_euft.xlsx")
            df_manutencao.to_csv(temp_csv_path_manutencao, index=False, sep=';', encoding='utf-8-sig')
            df_manutencao.to_excel(temp_excel_path_manutencao, index=False)

            # ── HTML de manutenção ──
            manutencao_html = "<h3 class='mt-4'>Veículos em Manutenção</h3>"
            manutencao_html += "<table class='table table-bordered table-striped mt-2'>"
            manutencao_html += "<thead><tr><th>Placa</th><th>Lotação</th><th>CAE</th><th>Data Entrada</th><th>Dias Parados</th></tr></thead><tbody>"
            for _, row in df_manutencao.iterrows():
                data_entrada = row['Data Emissão'].strftime('%d/%m/%Y') if not pd.isna(row['Data Emissão']) else ''
                manutencao_html += f"<tr><td>{row['Placa']}</td><td>{row['Lotacao']}</td><td>{row['CAE']}</td><td>{data_entrada}</td><td>{row['Dias Parados']}</td></tr>"
            manutencao_html += "</tbody></table>"

            # ── Déficit diário ──
            df_original = pd.concat([df1, df2], ignore_index=True)
            df_original['Placa'] = df_original['Placa'].astype(str).str.strip().str.upper()

            placas_to_lotacao_corrigido = {
                placa: (lot[0] if isinstance(lot, tuple) else lot)
                for placa, lot in placas_to_lotacao.items()
            }
            df_original['lotacao_patrimonial'] = df_original['Placa'].map(placas_to_lotacao_corrigido)
            df_original['Data Partida'] = pd.to_datetime(df_original['Data Partida'], dayfirst=True, errors='coerce')
            df_original = df_original.dropna(subset=['Data Partida'])

            df_uteis = df_original[df_original['Data Partida'].dt.dayofweek < 5].copy()
            placas_por_lot_dia = df_uteis.groupby(['lotacao_patrimonial', 'Data Partida'])['Placa'].nunique().reset_index()
            placas_por_lot_dia.rename(columns={'Placa': 'placas_saida'}, inplace=True)

            total_placas_lot = Counter()
            for placa, lot in placas_to_lotacao_corrigido.items():
                if lot and placa not in placas_em_manutencao:
                    total_placas_lot[lot] += 1

            pivot = placas_por_lot_dia.pivot(index='lotacao_patrimonial', columns='Data Partida', values='placas_saida').fillna(0)
            for lot in pivot.index:
                placas_disp = total_placas_lot.get(lot, 0)
                for dia in pivot.columns:
                    saidas = pivot.at[lot, dia]
                    deficit = max(0, placas_disp - saidas)
                    pivot.at[lot, dia] = deficit

            pivot['Déficit Total'] = pivot.sum(axis=1)
            colunas_datas = [col for col in pivot.columns if isinstance(col, pd.Timestamp)]
            colunas_finais = sorted(colunas_datas) + ['Déficit Total']
            pivot = pivot[colunas_finais]
            pivot.columns = [col.strftime('%d/%m/%Y') if isinstance(col, pd.Timestamp) else col for col in pivot.columns]

            deficit_df = pivot.reset_index()
            dias_cols = [col for col in deficit_df.columns if '/' in col and col != 'Déficit Total']
            deficit_count = (deficit_df[dias_cols] > 0).sum(axis=1)
            total_dias = len(dias_cols)

            def classificar_linha(dias_com_deficit):
                if dias_com_deficit == total_dias:
                    return 'linha-vermelha'
                elif dias_com_deficit >= total_dias / 2:
                    return 'linha-amarela'
                else:
                    return 'linha-verde'

            deficit_df['classe_linha'] = deficit_count.map(classificar_linha)
            colunas_visiveis = [col for col in deficit_df.columns if col != 'classe_linha']

            legenda_html = '''
            <div class="mb-3">
                <h6><strong>Legenda de Status:</strong></h6>
                <ul class="list-unstyled d-flex gap-4">
                    <li><span class="badge bg-success rounded-pill px-3 py-2">&nbsp;</span> <span class="ms-2">Pouco ou nenhum déficit</span></li>
                    <li><span class="badge bg-warning text-dark rounded-pill px-3 py-2">&nbsp;</span> <span class="ms-2">Déficit em 50% ou mais dos dias</span></li>
                    <li><span class="badge bg-danger rounded-pill px-3 py-2">&nbsp;</span> <span class="ms-2">Déficit todos os dias</span></li>
                </ul>
            </div>
            '''

            deficit_html = legenda_html
            deficit_html += '<table id="usoPorDiaTable" class="table table-bordered table-striped text-center align-middle">'
            deficit_html += '<thead class="table-light"><tr>'
            deficit_html += '<th>Status</th>' + ''.join(f'<th>{col}</th>' for col in colunas_visiveis) + '</tr></thead><tbody>'

            for _, row in deficit_df.iterrows():
                classe = row['classe_linha']
                if classe == 'linha-vermelha':
                    icone = '&#128308;'
                    cor = 'red'
                    titulo = 'Déficit em todos os dias'
                elif classe == 'linha-amarela':
                    icone = '&#128993;'
                    cor = 'orange'
                    titulo = 'Déficit em 50% ou mais dos dias'
                else:
                    icone = '&#128994;'
                    cor = 'green'
                    titulo = 'Pouco ou nenhum déficit'

                deficit_html += f'<tr class="{classe}">'
                deficit_html += f'<td title="{titulo}"><span style="font-size:1.2em; color:{cor};">{icone}</span></td>'
                for col in colunas_visiveis:
                    valor = row[col]
                    if isinstance(valor, (int, float)):
                        valor = int(valor)
                    deficit_html += f'<td>{valor}</td>'
                deficit_html += '</tr>'

            deficit_html += '</tbody></table>'

            # ── Cálculo EUFT ──
            df_original.columns = df_original.columns.str.strip()
            if 'Placa' in df_original.columns:
                df_original['Placa'] = df_original['Placa'].astype(str).str.strip().str.upper()

            if 'Data Partida' not in df_original.columns:
                raise ValueError("Coluna 'Data Partida' não encontrada no arquivo.")

            df = df_original.dropna(subset=['Data Retorno', 'Hora Retorno', 'Hod. Retorno'])

            resultados_veiculo, erros, media_geral_euft = calcular_euft(
                df, 20, placas_scudo, placas_especificas, placas_mobi, placas_analisadas, placas_to_lotacao
            )

            placas_faltantes = verificar_placas_sem_saida(df_original, placas_analisadas)
            # Remove placas em manutenção da lista de sem saída
            placas_faltantes = [placa for placa in placas_faltantes if placa not in placas_em_manutencao]

        except Exception as e:
            return f"Ocorreu um erro ao processar os arquivos: {e}"

        # ── Limpeza de colunas indesejadas ──
        if 'Tempo Utilizacao' in erros.columns:
            erros = erros.drop(columns=['Tempo Utilizacao'])
        if 'Correto' in erros.columns:
            erros = erros.drop(columns=['Correto'])

        # ── Funções de lotação/CAE ──
        def get_lotacao(p):
            val = placas_to_lotacao.get(p, ("", ""))
            if isinstance(val, str):
                return val
            elif isinstance(val, (list, tuple)):
                return val[0] if len(val) > 0 else ''
            return ''

        def get_cae(p):
            val = placas_to_lotacao.get(p, ("", ""))
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return val[1].replace("CAE ", "")
            return ""

        resultados_veiculo['lotacao_patrimonial'] = resultados_veiculo['Placa'].map(get_lotacao)
        resultados_veiculo['CAE'] = resultados_veiculo['Placa'].map(get_cae)

        # ── HTML de resultados por veículo ──
        resultados_html = ""
        for i, row in resultados_veiculo.iterrows():
            euft_percent = f"{row['EUFT'] * 100:.2f}".replace('.', ',') + '%'
            resultados_html += (
                f"<tr><td>{i + 1}</td>"
                f"<td>{row['Placa']}</td>"
                f"<td>{row['lotacao_patrimonial']}</td>"
                f"<td>{row['CAE']}</td>"
                f"<td>{row['Dias_Corretos']}</td>"
                f"<td>{row['Dias_Totais']}</td>"
                f"<td>{row['Adicional']}</td>"
                f"<td>{euft_percent}</td></tr>"
            )

        # ── Resultados por unidade ──
        resultados_por_unidade = resultados_veiculo.groupby('lotacao_patrimonial').agg({
            'Dias_Corretos': 'sum',
            'Dias_Totais': 'sum',
            'Adicional': 'sum'
        }).reset_index()

        def buscar_cae_por_lotacao(lot):
            for _, v in placas_to_lotacao.items():
                if isinstance(v, (list, tuple)) and len(v) >= 2:
                    if v[0] == lot:
                        return v[1].replace("CAE ", "")
            return ""

        resultados_por_unidade['CAE'] = resultados_por_unidade['lotacao_patrimonial'].map(buscar_cae_por_lotacao)

        resultados_por_unidade['EUFT'] = (
            resultados_por_unidade['Dias_Corretos'] /
            (resultados_por_unidade['Dias_Totais'] + resultados_por_unidade['Adicional'])
        ).fillna(0)

        resultados_por_unidade['EUFT (%)'] = (
            resultados_por_unidade['EUFT'] * 100
        ).round(2).astype(str).replace('.', ',') + '%'

        resultados_por_unidade = resultados_por_unidade.sort_values(by='EUFT', ascending=False)
        resultados_por_unidade = resultados_por_unidade.drop(columns=['EUFT'], errors='ignore')
        resultados_veiculo = resultados_veiculo.drop(columns=['EUFT'], errors='ignore')

        # ── Exportação de arquivos ──
        temp_dir = tempfile.gettempdir()

        colunas_unidade_renomeadas = {
            'lotacao_patrimonial': 'Lotação Patrimonial',
            'CAE': 'CAE',
            'Dias_Corretos': 'Lançamentos Corretos',
            'Dias_Totais': 'Lançamentos Totais',
            'Adicional': 'Adicional',
            'EUFT (%)': 'EUFT'
        }
        colunas_veiculo_renomeadas = {
            'Placa': 'Placa',
            'lotacao_patrimonial': 'Lotação Patrimonial',
            'CAE': 'CAE',
            'Dias_Corretos': 'Lançamentos Corretos',
            'Dias_Totais': 'Lançamentos Totais',
            'Adicional': 'Adicional',
            'EUFT (%)': 'EUFT'
        }

        df_unidades_export = resultados_por_unidade.rename(columns=colunas_unidade_renomeadas)
        df_veiculos_export = resultados_veiculo.rename(columns=colunas_veiculo_renomeadas)

        temp_csv_path_unidades = os.path.join(temp_dir, "results_unidades_euft.csv")
        temp_excel_path_unidades = os.path.join(temp_dir, "results_unidades_euft.xlsx")
        temp_csv_path_resultados = os.path.join(temp_dir, "results_euft.csv")
        temp_excel_path_resultados = os.path.join(temp_dir, "results_euft.xlsx")

        df_unidades_export.to_csv(temp_csv_path_unidades, index=False, sep=';', encoding='utf-8-sig')
        df_unidades_export.to_excel(temp_excel_path_unidades, index=False)
        df_veiculos_export.to_csv(temp_csv_path_resultados, index=False, sep=';', encoding='utf-8-sig')
        df_veiculos_export.to_excel(temp_excel_path_resultados, index=False)

        # ── HTML de resultados por unidade ──
        resultados_html += "<h3 class='mt-4'>Resultados</h3>"
        resultados_html += "<table id='unidadeTable' class='table table-bordered table-striped mt-2'>"
        resultados_html += (
            "<thead><tr><th>Id</th><th>CAE</th><th>Lotação Patrimonial</th>"
            "<th>Lançamentos Corretos</th><th>Lançamentos Totais</th>"
            "<th>Adicional</th><th>EUFT</th></tr></thead><tbody>"
        )

        for i, row in resultados_por_unidade.iterrows():
            def parse_euft_percent(valor):
                if valor is None:
                    return 0.0
                valor_str = str(valor).replace('%', '').strip()
                if ',' in valor_str and '.' not in valor_str:
                    valor_str = valor_str.replace(',', '.')
                valor_str = valor_str.replace(' ', '')
                partes = valor_str.split('.')
                if len(partes) > 2:
                    valor_str = ''.join(partes[:-1]) + '.' + partes[-1]
                try:
                    return float(valor_str)
                except:
                    return 0.0

            if 'EUFT' in resultados_por_unidade.columns and pd.notna(row.get('EUFT')):
                euft_val = float(row['EUFT']) * 100.0
            else:
                euft_val = parse_euft_percent(row.get('EUFT (%)', 0))

            if euft_val >= 97:
                cor = "#c6efce"
            elif 90 <= euft_val < 97:
                cor = "#fff3cd"
            else:
                cor = "#f8d7da"

            resultados_html += (
                f"<tr style='background-color: {cor};'>"
                f"<td>{i + 1}</td>"
                f"<td>{row.get('CAE', '')}</td>"
                f"<td>{row.get('lotacao_patrimonial', '')}</td>"
                f"<td>{row.get('Dias_Corretos', '')}</td>"
                f"<td>{row.get('Dias_Totais', '')}</td>"
                f"<td>{row.get('Adicional', '')}</td>"
                f"<td>{row.get('EUFT (%)', '')}</td></tr>"
            )

        resultados_html += "</tbody></table>"

        # ── HTML de erros ──
        erros_html = ""
        for i, row in erros.iterrows():
            erros_html += (
                f"<tr><td>{i + 1}</td><td>{row['Placa']}</td>"
                f"<td>{row['Data Partida']}</td><td>{row['Distancia Percorrida']}</td>"
                f"<td>{row['Lotacao Patrimonial']}</td><td>{row['Unidade em Operação']}</td>"
                f"<td>{row['Motivo Erro']}</td><td>{row['Tempo Utilizacao Formatado']}</td></tr>"
            )

        # ── HTML de veículos sem saída ──
        veiculos_sem_saida_html = ""
        for i, placa in enumerate(placas_faltantes, start=1):
            valores = placas_to_lotacao.get(placa)
            if isinstance(valores, str):
                partes = valores.split(" - ")
                lotacao_patrimonial = partes[0]
                CAE = partes[1] if len(partes) > 1 else " "
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

        # ── Exportação sem saída ──
        sem_saida_data = []
        for placa in placas_faltantes:
            valores = placas_to_lotacao.get(placa)
            if isinstance(valores, str):
                partes = valores.split(" - ")
                lotacao_patrimonial = partes[0]
                CAE = partes[1] if len(partes) > 1 else ""
            elif isinstance(valores, (list, tuple)):
                lotacao_patrimonial = valores[0] if len(valores) > 0 else ""
                CAE = valores[1] if len(valores) > 1 else ""
            else:
                lotacao_patrimonial = ""
                CAE = ""
            sem_saida_data.append({'Placa': placa, 'Lotação Patrimonial': lotacao_patrimonial, 'CAE': CAE, 'Status': 'Sem saída'})

        sem_saida_df = pd.DataFrame(sem_saida_data)
        temp_csv_path_sem_saida = os.path.join(tempfile.gettempdir(), "sem_saida_euft.csv")
        temp_excel_path_sem_saida = os.path.join(tempfile.gettempdir(), "sem_saida_euft.xlsx")
        sem_saida_df.to_csv(temp_csv_path_sem_saida, index=False, sep=';', encoding='utf-8-sig')
        sem_saida_df.to_excel(temp_excel_path_sem_saida, index=False)

        # ── Veículos sem retorno ──
        veiculos_sem_retorno_data = []
        agora_brasilia = datetime.now(fuso_brasilia)

        try:
            for i, row in enumerate(placas_sem_retorno.iterrows(), start=1):
                _, data = row
                placa = data['Placa']
                unidade = data.get('Unidade em Operação', '')

                data_partida_str = str(data.get('Data Partida', '')).strip()
                hora_partida_str = str(data.get('Hora Partida', '')).strip()

                try:
                    datahora_partida = datetime.strptime(f"{data_partida_str} {hora_partida_str}", "%d/%m/%Y %H:%M")
                    datahora_partida = fuso_brasilia.localize(datahora_partida)
                except ValueError:
                    datahora_partida = None

                mais_de_sete_horas = False
                if datahora_partida:
                    tempo_decorrido = agora_brasilia - datahora_partida
                    mais_de_sete_horas = tempo_decorrido > timedelta(hours=8)

                data_partida_formatada = datahora_partida.strftime('%d/%m/%Y %H:%M') if datahora_partida else ''

                valores = placas_to_lotacao.get(placa)
                if isinstance(valores, str):
                    partes = valores.split(" - ")
                    lotacao_patrimonial = partes[0]
                    CAE = partes[1] if len(partes) > 1 else " "
                elif isinstance(valores, (list, tuple)):
                    lotacao_patrimonial = valores[0] if len(valores) > 0 else " "
                    CAE = valores[1] if len(valores) > 1 else " "
                else:
                    lotacao_patrimonial = " "
                    CAE = " "

                veiculos_sem_retorno_data.append({
                    'Placa': placa,
                    'DataPartida': data_partida_formatada,
                    'Unidade': unidade,
                    'Lotacao': lotacao_patrimonial,
                    'CAE': CAE,
                    'MaisDeSeteHoras': mais_de_sete_horas
                })
        except Exception as e:
            print(f"Erro ao processar veículos sem retorno: {e}")

        # ── Gráfico ──
        impacto_unidade = erros.groupby('Unidade em Operação').size().reset_index(name='Qtd_Erros')
        impacto_unidade.columns = ['Unidade', 'Qtd_Erros']
        impacto_unidade = impacto_unidade.sort_values(by='Qtd_Erros', ascending=False).head(15)
        labels = impacto_unidade['Unidade'].tolist()
        valores = impacto_unidade['Qtd_Erros'].tolist()

        temp_csv_path = os.path.join(tempfile.gettempdir(), "erros_euft.csv")
        temp_excel_path = os.path.join(tempfile.gettempdir(), "erros_euft.xlsx")
        erros.to_csv(temp_csv_path, index=False, sep=';', encoding='utf-8-sig')
        erros.to_excel(temp_excel_path, index=False)

        return render_template('index.html',
                               resultados_veiculo_data=resultados_html,
                               erros_data=erros_html,
                               grafico_labels=json.dumps(labels),
                               grafico_dados=json.dumps(valores),
                               sem_saida_data=veiculos_sem_saida_html,
                               manutencao_data=manutencao_html,
                               veiculos_sem_retorno_data=veiculos_sem_retorno_data,
                               link_csv_resultados='/download/results_csv',
                               link_excel_resultados='/download/results_excel',
                               link_csv='/download/erros_csv',
                               link_excel='/download/erros_excel',
                               link_csv_sem_saida='/download/sem_saida_csv',
                               link_excel_sem_saida='/download/sem_saida_excel',
                               link_csv_manutencao='/download/manutencao_csv',
                               link_excel_manutencao='/download/manutencao_excel',
                               regioes=regioes,
                               region_selecionada=region,
                               deficit_html=deficit_html,
                               media_geral_euft=media_geral_euft)

    return render_template('index.html', media_geral_euft=media_geral_euft)


@app.route('/download/erros_csv')
def download_erros_csv():
    temp_csv_path = os.path.join(tempfile.gettempdir(), "erros_euft.csv")
    return send_file(temp_csv_path, as_attachment=True, download_name="Erros_EUFT.csv")


@app.route('/download/erros_excel')
def download_erros_excel():
    temp_excel_path = os.path.join(tempfile.gettempdir(), "erros_euft.xlsx")
    return send_file(temp_excel_path, as_attachment=True, download_name="Erros_EUFT.xlsx")


@app.route('/download/sem_saida_csv')
def download_sem_saida_csv():
    temp_csv_path = os.path.join(tempfile.gettempdir(), "sem_saida_euft.csv")
    return send_file(temp_csv_path, as_attachment=True, download_name="Sem_Saida_EUFT.csv")


@app.route('/download/sem_saida_excel')
def download_sem_saida_excel():
    temp_excel_path = os.path.join(tempfile.gettempdir(), "sem_saida_euft.xlsx")
    return send_file(temp_excel_path, as_attachment=True, download_name="Sem_Saida_EUFT.xlsx")


@app.route('/download/results_csv')
def download_resultados_csv():
    temp_csv_path_resultados = os.path.join(tempfile.gettempdir(), "results_euft.csv")
    return send_file(temp_csv_path_resultados, as_attachment=True, download_name="Results_EUFT.csv")


@app.route('/download/results_excel')
def download_resultados_excel():
    temp_excel_path_resultados = os.path.join(tempfile.gettempdir(), "results_euft.xlsx")
    return send_file(temp_excel_path_resultados, as_attachment=True, download_name="Results_EUFT.xlsx")


@app.route('/download/results_unidades_csv')
def download_results_unidades_csv():
    temp_csv_path = os.path.join(tempfile.gettempdir(), "results_unidades_euft.csv")
    return send_file(temp_csv_path, as_attachment=True, download_name="Resultados_Unidades_EUFT.csv")


@app.route('/download/results_unidades_excel')
def download_results_unidades_excel():
    temp_excel_path = os.path.join(tempfile.gettempdir(), "results_unidades_euft.xlsx")
    return send_file(temp_excel_path, as_attachment=True, download_name="Resultados_Unidades_EUFT.xlsx")


@app.route('/download/manutencao_csv')
def download_manutencao_csv():
    temp_csv_path = os.path.join(tempfile.gettempdir(), "manutencao_euft.csv")
    return send_file(temp_csv_path, as_attachment=True, download_name="Veiculos_Manutencao_EUFT.csv")


@app.route('/download/manutencao_excel')
def download_manutencao_excel():
    temp_excel_path = os.path.join(tempfile.gettempdir(), "manutencao_euft.xlsx")
    return send_file(temp_excel_path, as_attachment=True, download_name="Veiculos_Manutencao_EUFT.xlsx")


if __name__ == '__main__':
    app.run(debug=True, port=5002)
