import math
import streamlit as st

st.set_page_config(
    page_title="IA Betting Analyst", page_icon="⚽", layout="wide"
)

st.title("⚽ IA Betting Analyst — Painel de Análise On-Demand")
st.caption("Modelo Estatístico Poisson + Ponderação Tática + Cálculo EV+")

st.sidebar.header("⚙️ Gestão de Banca")
banca_total = st.sidebar.number_input(
    "Valor Total da Banca (€)", value=1000.0, step=50.0
)
kelly_fraction = st.sidebar.slider(
    "Fracção de Kelly (Controlo de Risco)", 0.1, 0.5, 0.25, 0.05
)

st.subheader("🔍 Pesquisa e Parâmetros do Jogo")

col1, col2 = st.columns(2)
with col1:
    equipa_casa = st.text_input("Equipa da Casa", "Freiburg")
    xg_casa = st.number_input(
        f"Média xG / Golos {equipa_casa} (Casa)", value=1.85, step=0.05
    )
    ausencias_casa = st.slider(
        f"Impacto Ausências/Desgaste {equipa_casa} (%)", -20, 20, 0
    )

with col2:
    equipa_fora = st.text_input("Equipa Fora", "Monchengladbach")
    xg_fora = st.number_input(
        f"Média xG / Golos {equipa_fora} (Fora)", value=0.90, step=0.05
    )
    ausencias_fora = st.slider(
        f"Impacto Ausências/Desgaste {equipa_fora} (%)", -20, 20, -10
    )

st.divider()

col_odds1, col_odds2, col_odds3 = st.columns(3)
with col_odds1:
    odd_casa = st.number_input(f"Odd Casa ({equipa_casa})", value=1.68, step=0.01)
with col_odds2:
    odd_empate = st.number_input("Odd Empate (X)", value=3.90, step=0.01)
with col_odds3:
    odd_btts = st.number_input("Odd Ambas Marcam (Sim)", value=1.75, step=0.01)


def poisson_prob(k, lambda_param):
    return (math.exp(-lambda_param) * (lambda_param**k)) / math.factorial(k)


lambda_casa = max(0.2, xg_casa * (1 + (ausencias_casa / 100)))
lambda_fora = max(0.2, xg_fora * (1 + (ausencias_fora / 100)))

prob_casa_win = 0.0
prob_empate = 0.0
prob_fora_win = 0.0
prob_btts = 0.0

for g_casa in range(6):
    for g_fora in range(6):
        p = poisson_prob(g_casa, lambda_casa) * poisson_prob(
            g_fora, lambda_fora
        )
        if g_casa > g_fora:
            prob_casa_win += p
        elif g_casa == g_fora:
            prob_empate += p
        else:
            prob_fora_win += p

        if g_casa > 0 and g_fora > 0:
            prob_btts += p

ev_casa = (prob_casa_win * odd_casa) - 1
ev_btts = (prob_btts * odd_btts) - 1


def calc_kelly(prob, odd, banca, fraction):
    b = odd - 1
    q = 1 - prob
    f_star = ((b * prob) - q) / b
    if f_star <= 0:
        return 0.0, 0.0
    stake_percent = f_star * fraction
    stake_euros = banca * stake_percent
    return stake_percent * 100, stake_euros


stake_pct_casa, stake_eur_casa = calc_kelly(
    prob_casa_win, odd_casa, banca_total, kelly_fraction
)
stake_pct_btts, stake_eur_btts = calc_kelly(
    prob_btts, odd_btts, banca_total, kelly_fraction
)

if st.button("🚀 Processar Análise e Calcular Valor", use_container_width=True):
    st.subheader("📊 Relatório de Saída da IA")

    res1, res2 = st.columns(2)

    with res1:
        st.markdown(f"### Vitória Direta: **{equipa_casa}**")
        st.write(f"• **Probabilidade Real Estimada:** `{prob_casa_win*100:.1f}%`")
        st.write(
            f"• **Odd Justa (Fair Odd):** `{1/prob_casa_win:.2f}` vs **Odd Casa:** `{odd_casa:.2f}`"
        )
        st.write(f"• **Expected Value (EV+):** `{ev_casa*100:+.1f}%`")

        if ev_casa > 0:
            st.success(
                f"✅ **VALOR DETETADO!**\n\nRecomendação de Aposta: **{stake_eur_casa:.2f}€** ({stake_pct_casa:.1f}% da banca)"
            )
        else:
            st.error("❌ **SEM VALOR.** A odd da casa está abaixo da odd justa.")

    with res2:
        st.markdown("### Mercado: **Ambas Marcam (BTTS)**")
        st.write(f"• **Probabilidade Real Estimada:** `{prob_btts*100:.1f}%`")
        st.write(
            f"• **Odd Justa (Fair Odd):** `{1/prob_btts:.2f}` vs **Odd Casa:** `{odd_btts:.2f}`"
        )
        st.write(f"• **Expected Value (EV+):** `{ev_btts*100:+.1f}%`")

        if ev_btts > 0:
            st.success(
                f"✅ **VALOR DETETADO!**\n\nRecomendação de Aposta: **{stake_eur_btts:.2f}€** ({stake_pct_btts:.1f}% da banca)"
            )
        else:
            st.error("❌ **SEM VALOR.** A odd da casa está abaixo da odd justa.")
