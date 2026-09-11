import pandas as pd
import numpy as np
import math
import streamlit as st

st.set_page_config(page_title="IA Betting Screener", page_icon="🎯", layout="wide")

st.title("🎯 IA Betting Screener — Scanner de Oportunidades")
st.caption("Filtro automático de jogos com EV+ (Poisson + Dixon-Coles Matrix)")

# Sidebar - Filtros Globais
st.sidebar.header("🎛️ Filtros de Oportunidades")

mercado_filtro = st.sidebar.selectbox(
    "Mercado Principal", 
    ["Todos", "Vitória Casa (1)", "Ambas Marcam (Sim)", "Over 2.5 Golos", "Vitória Casa ao Intervalo (1 HT)"]
)

min_ev = st.sidebar.slider("Valor Esperado Mínimo (EV+ %)", 0.0, 20.0, 3.0, 0.5)
min_odd = st.sidebar.number_input("Odd Mínima", value=1.50, step=0.05)
max_odd = st.sidebar.number_input("Odd Máxima", value=4.00, step=0.05)

# Simulação de Base de Dados de Jogos do Dia (Substituível por Scraper/API)
@st.cache_data
def carregar_jogos_dia():
    dados = [
        {"Jogo": "Freiburg vs Monchengladbach", "Liga": "Bundesliga", "xG_C": 1.85, "xG_F": 0.90, "Odd_1": 1.75, "Odd_BTTS": 1.80, "Odd_O25": 1.70, "Odd_HT1": 2.30},
        {"Jogo": "Benfica vs Braga", "Liga": "Liga Portugal", "xG_C": 2.10, "xG_F": 1.30, "Odd_1": 1.65, "Odd_BTTS": 1.65, "Odd_O25": 1.55, "Odd_HT1": 2.15},
        {"Jogo": "Sevilla vs Betis", "Liga": "La Liga", "xG_C": 1.10, "xG_F": 1.05, "Odd_1": 2.40, "Odd_BTTS": 1.95, "Odd_O25": 2.20, "Odd_HT1": 3.10},
        {"Jogo": "Arsenal vs Everton", "Liga": "Premier League", "xG_C": 2.40, "xG_F": 0.60, "Odd_1": 1.35, "Odd_BTTS": 2.10, "Odd_O25": 1.50, "Odd_HT1": 1.80},
        {"Jogo": "Lazio vs Fiorentina", "Liga": "Serie A", "xG_C": 1.40, "xG_F": 1.20, "Odd_1": 2.10, "Odd_BTTS": 1.75, "Odd_O25": 1.90, "Odd_HT1": 2.80},
    ]
    return pd.DataFrame(dados)

df_jogos = carregar_jogos_dia()

# Motor do Algoritmo de Poisson
def calcular_metricas(row):
    l_c, l_f = row['xG_C'], row['xG_F']
    
    p_1, p_btts, p_o25, p_ht1 = 0.0, 0.0, 0.0, 0.0
    
    for gc in range(6):
        for gf in range(6):
            prob = ((math.exp(-l_c) * (l_c**gc)) / math.factorial(gc)) * \
                   ((math.exp(-l_f) * (l_f**gf)) / math.factorial(gf))
            
            if gc > gf: p_1 += prob
            if gc > 0 and gf > 0: p_btts += prob
            if (gc + gf) > 2.5: p_o25 += prob
            if gc > gf and (gc >= 1): p_ht1 += prob * 0.65  # Aproximação estocástica HT
            
    return pd.Series([
        (p_1 * row['Odd_1']) - 1,
        (p_btts * row['Odd_BTTS']) - 1,
        (p_o25 * row['Odd_O25']) - 1,
        (p_ht1 * row['Odd_HT1']) - 1
    ])

df_jogos[['EV_1', 'EV_BTTS', 'EV_O25', 'EV_HT1']] = df_jogos.apply(calcular_metricas, axis=1) * 100

# Filtragem Dinâmica
resultados = []

for idx, row in df_jogos.iterrows():
    m_list = [
        ("Vitória Casa (1)", row['Odd_1'], row['EV_1']),
        ("Ambas Marcam (Sim)", row['Odd_BTTS'], row['EV_BTTS']),
        ("Over 2.5 Golos", row['Odd_O25'], row['EV_O25']),
        ("Vitória Casa ao Intervalo (1 HT)", row['Odd_HT1'], row['EV_HT1'])
    ]
    
    for nome_m, odd, ev in m_list:
        if (mercado_filtro == "Todos" or mercado_filtro == nome_m) and (ev >= min_ev) and (min_odd <= odd <= max_odd):
            resultados.append({
                "Jogo": row['Jogo'],
                "Liga": row['Liga'],
                "Mercado Recomen.": nome_m,
                "Odd Mercado": f"{odd:.2f}",
                "Expected Value": f"+{ev:.1f}%"
            })

df_final = pd.DataFrame(resultados)

# Apresentação do Feed Filtrado
st.subheader("📋 Oportunidades Detetadas com Valor (+EV)")

if not df_final.empty:
    st.dataframe(df_final, use_container_width=True)
else:
    st.warning("Nenhum jogo encontrado com os filtros atuais. Reduz o EV% mínimo ou alarga o limite de Odds.")
