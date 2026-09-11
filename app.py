import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA & TEMA VISUAL (DARK FOOTBALL)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EdgeScanner — EV+ Sports",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado Otimizado para Ecrã OLED de iPhone
st.markdown("""
<style>
    /* Fundo Noturno de Estádio com Overlay Escuro */
    .stApp {
        background: 
            linear-gradient(rgba(11, 15, 25, 0.92), rgba(11, 15, 25, 0.97)),
            url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=1920&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #F3F4F6;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main-header {
        text-align: center;
        padding: 10px 0 15px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .main-header h1 {
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        background: linear-gradient(90deg, #10B981, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .main-header p {
        font-size: 0.8rem;
        color: #9CA3AF;
        margin-top: 2px;
    }

    .match-card {
        background: rgba(17, 24, 39, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    .match-meta {
        font-size: 0.75rem;
        font-weight: 600;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: flex;
        justify-content: space-between;
        margin-bottom: 6px;
    }
    
    .teams-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 10px;
    }
    
    .ev-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid #10B981;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
    }
    
    .no-ev-badge {
        background: rgba(107, 114, 128, 0.15);
        color: #9CA3AF;
        border: 1px solid rgba(107, 114, 128, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .market-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.85rem;
    }
    .market-row:last-child {
        border-bottom: none;
    }
    
    .metric-value {
        font-weight: 700;
        color: #3B82F6;
    }
    .odd-22bet {
        font-weight: 700;
        color: #F59E0B;
        background: rgba(245, 158, 11, 0.1);
        padding: 2px 6px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. MOTOR ESTATÍSTICO (POISSON & 7 MERCADOS)
# -----------------------------------------------------------------------------
def calcular_probabilidades_jogo(lambda_casa, lambda_fora):
    max_golos = 8
    matriz = np.zeros((max_golos, max_golos))
    
    for i in range(max_golos):
        for j in range(max_golos):
            matriz[i, j] = poisson.pmf(i, lambda_casa) * poisson.pmf(j, lambda_fora)
            
    prob_casa = float(np.sum(np.tril(matriz, -1)))
    prob_empate = float(np.sum(np.diag(matriz)))
    prob_fora = float(np.sum(np.triu(matriz, 1)))
    
    lambda_casa_ht = lambda_casa * 0.43
    lambda_fora_ht = lambda_fora * 0.43
    matriz_ht = np.zeros((max_golos, max_golos))
    for i in range(max_golos):
        for j in range(max_golos):
            matriz_ht[i, j] = poisson.pmf(i, lambda_casa_ht) * poisson.pmf(j, lambda_fora_ht)
            
    prob_casa_ht = float(np.sum(np.tril(matriz_ht, -1)))
    prob_fora_ht = float(np.sum(np.triu(matriz_ht, 1)))
    
    prob_over05_ht = float(1.0 - matriz_ht[0, 0])
    
    totais = np.array([[i + j for j in range(max_golos)] for i in range(max_golos)])
    prob_over15 = float(np.sum(matriz[totais > 1.5]))
    prob_over25 = float(np.sum(matriz[totais > 2.5]))
    
    prob_btts = float(np.sum(matriz[1:, 1:]))
    
    denom_casa = prob_casa + prob_fora
    prob_dnb_casa = float(prob_casa / denom_casa) if denom_casa > 0 else 0.5
    prob_dnb_fora = float(prob_fora / denom_casa) if denom_casa > 0 else 0.5
    
    return {
        "Casa (1)": prob_casa,
        "Fora (2)": prob_fora,
        "Empate (X)": prob_empate,
        "Casa HT": prob_casa_ht,
        "Fora HT": prob_fora_ht,
        "Over 0.5 HT": prob_over05_ht,
        "Over 1.5 FT": prob_over15,
        "Over 2.5 FT": prob_over25,
        "BTTS (Sim)": prob_btts,
        "DNB Casa": prob_dnb_casa,
        "DNB Fora": prob_dnb_fora
    }

def calcular_ev(prob_pct, odd_22bet):
    prob_decimal = prob_pct / 100.0
    ev = (prob_decimal * odd_22bet) - 1.0
    return round(ev * 100, 1)

# -----------------------------------------------------------------------------
# 3. MÓDULO DE DADOS & ODDS 22BET
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def carregar_jogos_dia(data_str):
    np.random.seed(int(data_str.replace("-", "")) % 100000)
    
    ligas = ["Liga Portugal", "Premier League", "La Liga", "Serie A", "Bundesliga"]
    equipas = [
        ("Benfica", "Porto"), ("Sporting", "Braga"), ("Arsenal", "Chelsea"),
        ("Real Madrid", "Barcelona"), ("Inter", "Milan"), ("Bayern", "Dortmund"),
        ("Vitoria SC", "Rio Ave"), ("Man City", "Liverpool"), ("Juventus", "Napoli")
    ]
    
    jogos = []
    num_jogos = np.random.randint(5, 9)
    
    for i in range(num_jogos):
        eq = equipas[i % len(equipas)]
        liga = ligas[i % len(ligas)]
        hora = f"{np.random.randint(13, 21)}:{np.random.choice(['00', '15', '30', '45'])}"
        
        l_casa = round(np.random.uniform(1.1, 2.4), 2)
        l_fora = round(np.random.uniform(0.8, 2.1), 2)
        
        probs = calcular_probabilidades_jogo(l_casa, l_fora)
        
        odds_22bet = {}
        for m, p in probs.items():
            odd_firme = round(1.0 / p * np.random.uniform(0.92, 1.15), 2)
            odds_22bet[m] = max(odd_firme, 1.05)
            
        jogos.append({
            "id": i,
            "hora": hora,
            "liga": liga,
            "casa": eq[0],
            "fora": eq[1],
            "probs": probs,
            "odds_22bet": odds_22bet
        })
        
    return jogos

# -----------------------------------------------------------------------------
# 4. INTERFACE E NAVEGAÇÃO DE DOMINGO A DOMINGO
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>EDGESCANNER</h1>
    <p>Screener de Vantagem Estatística & Odds 22Bet</p>
</div>
""", unsafe_allow_html=True)

hoje = datetime.today()
dias_ate_domingo = (hoje.weekday() + 1) % 7
inicio_domingo = hoje - timedelta(days=dias_ate_domingo)

dias_semana = [inicio_domingo + timedelta(days=i) for i in range(8)]

data_selecionada = st.select_slider(
    "📅 Seleciona o Dia do Jogo:",
    options=dias_semana,
    format_func=lambda x: x.strftime("%a, %d %b"),
    value=hoje
)

mercado_filtro = st.selectbox(
    "🎯 Filtrar Mercado Principal:",
    [
        "Todos os Mercados",
        "Vitória Direta (1X2)",
        "Vitória ao Intervalo (HT)",
        "Over 0.5 HT",
        "Over 1.5 FT & Over 2.5 FT",
        "Ambas Marcam (BTTS)",
        "Empate Anula (DNB)"
    ]
)

# -----------------------------------------------------------------------------
# 5. PROCESSAMENTO E EXIBIÇÃO DOS JOGOS
# -----------------------------------------------------------------------------
data_str = data_selecionada.strftime("%Y-%m-%d")
lista_jogos = carregar_jogos_dia(data_str)

st.caption(f"A mostrar **{len(lista_jogos)} jogos** para {data_selecionada.strftime('%A, %d de %B de %Y')}")

for jogo in lista_jogos:
    probs = jogo["probs"]
    odds = jogo["odds_22bet"]
    
    oportunidades_ev = []
    for m in probs:
        p_pct = probs[m] * 100
        odd_22 = odds[m]
        ev_val = calcular_ev(p_pct, odd_22)
        if ev_val >= 3.0:
            oportunidades_ev.append((m, p_pct, odd_22, ev_val))
            
    st.markdown(f"""
    <div class="match-card">
        <div class="match-meta">
            <span>{jogo['hora']} | {jogo['liga']}</span>
            <span>{f'<span class="ev-badge">🔥 {len(oportunidades_ev)} OP. EV+</span>' if oportunidades_ev else '<span class="no-ev-badge">SEM EV+</span>'}</span>
        </div>
        <div class="teams-title">{jogo['casa']} vs {jogo['fora']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔍 Ver Probabilidades & Odds 22Bet"):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        col1.markdown("**Mercado**")
        col2.markdown("**Prob. (%)**")
        col3.markdown("**Odd 22Bet**")
        
        for m in probs:
            if mercado_filtro != "Todos os Mercados":
                if "Vitória Direta" in mercado_filtro and m not in ["Casa (1)", "Fora (2)", "Empate (X)"]:
                    continue
                if "Intervalo" in mercado_filtro and "HT" not in m:
                    continue
                if "Over 0.5 HT" in mercado_filtro and m != "Over 0.5 HT":
                    continue
                if "Over 1.5" in mercado_filtro and "FT" not in m:
                    continue
                if "BTTS" in mercado_filtro and m != "BTTS (Sim)":
                    continue
                if "DNB" in mercado_filtro and "DNB" not in m:
                    continue

            p_pct = round(probs[m] * 100, 1)
            odd_22 = odds[m]
            ev_val = calcular_ev(p_pct, odd_22)
            
            tag_ev = f"<span class='ev-badge'>+{ev_val}% EV</span>" if ev_val >= 3.0 else ""
            
            st.markdown(f"""
            <div class="market-row">
                <div><strong>{m}</strong> {tag_ev}</div>
                <div class="metric-value">{p_pct}%</div>
                <div class="odd-22bet">{odd_22:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
