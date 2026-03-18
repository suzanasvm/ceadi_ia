import streamlit as st
import pandas as pd
import re
import plotly.express as px

st.set_page_config(layout="wide")

st.title("Ceadi - Dashboard de Engajamento de Alunos")

# =========================
# Função de conversão
# =========================
def tempo_para_dias(texto):
    if pd.isna(texto):
        return None
    
    texto = texto.lower()
    
    if "nunca" in texto:
        return 999
    
    dias = 0
    
    match_dias = re.search(r'(\d+)\s*dias?', texto)
    if match_dias:
        dias += int(match_dias.group(1))
    
    match_horas = re.search(r'(\d+)\s*horas?', texto)
    if match_horas:
        dias += int(match_horas.group(1)) / 24
    
    match_min = re.search(r'(\d+)\s*minutos?', texto)
    if match_min:
        dias += int(match_min.group(1)) / (24 * 60)
    
    return dias

# =========================
# Upload
# =========================
arquivo = st.file_uploader("Envie o CSV", type=["csv"])

if arquivo:
    df = pd.read_csv(arquivo)

    df["dias_sem_acesso"] = df["Último acesso ao curso"].apply(tempo_para_dias)
    df_ativos = df[df["Situação"] == "Ativo"]

    # =========================
    # Sidebar
    # =========================
    st.sidebar.title("Configurações")

    opcao = st.sidebar.radio(
        "Navegação",
        ["Visão Geral", "Por Grupo", "Email Externo"]
    )

    dias_risco = st.sidebar.slider(
        "Dias sem acesso (risco)",
        1, 30, 7
    )

    top_n = st.sidebar.slider(
        "Top grupos",
        min_value=3,
        max_value=50,
        value=15
    )

    st.sidebar.subheader("Personalização")

    tamanho_fonte = st.sidebar.slider(
        "Tamanho da fonte",
        min_value=10,
        max_value=24,
        value=14
    )

    altura_grafico = st.sidebar.slider(
        "Altura dos gráficos",
        min_value=300,
        max_value=900,
        value=500
    )

    # =========================
    # VISÃO GERAL
    # =========================
    if opcao == "Visão Geral":

        st.header("Panorama Geral")

        # =========================
        # BASE COMPLETA (SEM FILTRO)
        # =========================
        total_por_grupo = (
            df_ativos.groupby("Grupos")
            .size()
            .reset_index(name="Total")
        )

        risco = df_ativos[df_ativos["dias_sem_acesso"] > dias_risco]

        risco_por_grupo = (
            risco.groupby("Grupos")
            .size()
            .reset_index(name="Em risco")
        )

        merged = pd.merge(total_por_grupo, risco_por_grupo, on="Grupos", how="left")
        merged["Em risco"] = merged["Em risco"].fillna(0)
        merged["Percentual"] = (merged["Em risco"] / merged["Total"]) * 100

        # =========================
        # GRÁFICO 1: TAMANHO DOS GRUPOS
        # =========================
        contagem = (
            total_por_grupo
            .sort_values(by="Total", ascending=False)
        )

        contagem_top = contagem.head(top_n)

        fig = px.bar(
            contagem_top,
            x="Total",
            y="Grupos",
            orientation="h",
            text="Total",
            color="Total",
            color_continuous_scale="viridis"
        )

        fig.update_layout(
            title=f"Top {top_n} grupos por quantidade de alunos",
            yaxis=dict(categoryorder="total ascending"),
            height=altura_grafico,
            font=dict(size=tamanho_fonte)
        )

        st.plotly_chart(fig, use_container_width=True)


        # =========================

        # GRÁFICO 2: RISCO (%)
        # =========================
        st.subheader("Onde está o maior risco de evasão?")

        merged_percentual = merged.sort_values(by="Percentual", ascending=False)
        merged_percentual_top = merged_percentual.head(top_n)

        fig2 = px.bar(
            merged_percentual_top,
            x="Percentual",
            y="Grupos",
            orientation="h",
            text=merged_percentual_top["Percentual"].round(1).astype(str) + "%",
            color="Percentual",
            color_continuous_scale="reds",
            hover_data={
                "Total": True,
                "Em risco": True,
                "Percentual": ':.2f'
            }
        )

        fig2.update_traces(
            hovertemplate="<b>%{y}</b><br>" +
                        "Percentual: %{x:.2f}%<br>" +
                        "Total alunos: %{customdata[0]}<br>" +
                        "Em risco: %{customdata[1]}<extra></extra>"
        )

        fig2.update_layout(
            title=f"Top {top_n} grupos com maior percentual de risco (> {dias_risco} dias)",
            yaxis=dict(categoryorder="total ascending"),
            height=altura_grafico,
            font=dict(size=tamanho_fonte),
            xaxis_title="% de alunos em risco"
        )

        st.plotly_chart(fig2, use_container_width=True)

        # =========================
        # GRÁFICO 3: EVASÃO ABSOLUTA
        # =========================
        st.subheader("Possibilidade de Evasão em valores absolutos?")

        merged_abs = merged.sort_values(by="Em risco", ascending=False)
        merged_abs_top = merged_abs.head(top_n)

        fig3 = px.bar(
            merged_abs_top,
            x="Em risco",
            y="Grupos",
            orientation="h",
            text="Em risco",
            color="Em risco",
            color_continuous_scale="oranges",
            hover_data={
                "Total": True,
                "Percentual": ':.2f'
            }
        )

        fig3.update_traces(
            hovertemplate="<b>%{y}</b><br>" +
                        "Alunos em risco: %{x}<br>" +
                        "Total alunos: %{customdata[0]}<br>" +
                        "Percentual: %{customdata[1]:.2f}%<extra></extra>"
        )

        fig3.update_layout(
             title=f"Top {top_n} grupos com maior número absoluto de alunos em risco (> {dias_risco} dias)",
            yaxis=dict(categoryorder="total ascending"),
            height=altura_grafico,
            font=dict(size=tamanho_fonte),
            xaxis_title="Quantidade de alunos em risco"
        )

        st.plotly_chart(fig3, use_container_width=True)
        # =========================
        # INDICADORES
        # =========================
        st.subheader("Indicadores rápidos")

        # identificar profissionais (sem grupo ou grupo vazio)
        profissionais = df_ativos[
            df_ativos["Grupos"].isna() | (df_ativos["Grupos"].astype(str).str.strip() == "Nenhum grupo")
        ]

        # alunos válidos (com grupo)
        alunos = df_ativos.drop(profissionais.index)

        # alunos que nunca acessaram
        nunca = alunos[alunos["Último acesso ao curso"] == "Nunca"]

        # alunos em risco
        risco = alunos[alunos["dias_sem_acesso"] > dias_risco]

        total_alunos = len(alunos)

        # evitar divisão por zero
        perc_nunca = (len(nunca) / total_alunos * 100) if total_alunos > 0 else 0
        perc_risco = (len(risco) / total_alunos * 100) if total_alunos > 0 else 0

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total de alunos", total_alunos)
        col2.metric("Profissionais", len(profissionais))
        col3.metric("Nunca acessaram", f"{len(nunca)} ({perc_nunca:.1f}%)")
        col4.metric("Alunos em risco", f"{len(risco)} ({perc_risco:.1f}%)")

        # =========================
        # EXPORTAÇÃO PARA EXCEL
        # =========================
        st.subheader("Exportação de dados")

        from io import BytesIO

        output = BytesIO()

        # dados combinados: nunca + risco
        df_export = pd.concat([nunca, risco]).drop_duplicates()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for grupo, dados_grupo in df_export.groupby("Grupos"):
                nome_aba = str(grupo)[:31] if pd.notna(grupo) else "Sem Grupo"
                dados_grupo.to_excel(writer, sheet_name=nome_aba, index=False)

        output.seek(0)

        st.download_button(
            label="Gerar planilha Excel",
            data=output,
            file_name="alunos_risco_nunca.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    # =========================
    # VISÃO POR GRUPO
    # =========================
    elif opcao == "Por Grupo":
        st.header("Análise por Grupo")

        grupos = sorted(df_ativos["Grupos"].unique())

        grupo_selecionado = st.selectbox("Escolha o grupo:", grupos)

        df_grupo = df_ativos[df_ativos["Grupos"] == grupo_selecionado]

        # =========================
        # Alunos ativos (sem "Nunca" e ordenados crescente)
        # =========================
        st.subheader("Alunos ativos")

        df_ativos_validos = df_grupo[df_grupo["Último acesso ao curso"] != "Nunca"].copy()

        df_ativos_validos = df_ativos_validos.sort_values(
            by="dias_sem_acesso",
            ascending=True
        )

        st.dataframe(df_ativos_validos, use_container_width=True)

        # =========================
        # Alunos em risco
        # =========================
        st.subheader("Alunos em risco de desistência")

        risco = df_grupo[df_grupo["dias_sem_acesso"] > dias_risco].copy()

        # criar coluna auxiliar para priorizar "Nunca"
        risco["ordem_nunca"] = risco["Último acesso ao curso"].apply(
            lambda x: 0 if x == "Nunca" else 1
        )

        risco = risco.sort_values(
            by=["ordem_nunca", "dias_sem_acesso"],
            ascending=[True, False]
        )

        risco = risco.drop(columns=["ordem_nunca"])

        st.write(f"Critério: mais de {dias_risco} dias sem acesso")

        st.dataframe(risco, use_container_width=True)
    # =========================
    # =========================
    # MENU: EMAIL EXTERNO
    # =========================
    elif opcao == "Email Externo":

        st.header("Alunos com email externo (fora do padrão ifnmg.edu.br)")

        # garantir tratamento de nulos e padronização
        df_temp = df_ativos.copy()
        df_temp["Endereço de e-mail"] = df_temp["Endereço de e-mail"].fillna("").str.strip().str.lower()

        # filtrar emails que NÃO terminam com ifnmg.edu.br
        df_externo = df_temp[
            ~df_temp["Endereço de e-mail"].str.endswith("ifnmg.edu.br")
        ]

        st.subheader("Lista de alunos")

        st.dataframe(
            df_externo.sort_values(by="Endereço de e-mail"),
            use_container_width=True
        )

        # =========================
        # INDICADORES
        # =========================
        st.subheader("Indicadores")

        total_externo = len(df_externo)

         # identificar profissionais (sem grupo ou grupo vazio)
        profissionais = df_temp[
            df_temp["Grupos"].isna() | (df_temp["Grupos"].astype(str).str.strip() == "Nenhum grupo")
        ]

        # alunos válidos (com grupo)
        alunos = df_temp.drop(profissionais.index)
        total_geral = len(alunos)

        percentual = (total_externo / total_geral * 100) if total_geral > 0 else 0

        col1, col2 = st.columns(2)

        col1.metric("Total de emails externos", total_externo)
        col2.metric("Percentual", f"{percentual:.1f}%")

        # =========================
        # EXPORTAÇÃO
        # =========================
        st.subheader("Exportação")

        from io import BytesIO

        output = BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_externo.to_excel(writer, sheet_name="Email_Externo", index=False)

        output.seek(0)

        st.download_button(
            label="Gerar planilha Excel",
            data=output,
            file_name="emails_externos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )