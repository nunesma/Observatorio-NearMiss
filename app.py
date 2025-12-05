import streamlit as st
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
import plotly.express as px
import folium
import geopandas
import requests


# --- Configuração da Página ---
# Define o título da página, o ícone e o layout para ocupar a largura inteira.
# A taxa de morbidade neonatal near miss


st.set_page_config(
    page_title="Observatório do NearMiss Neonatal",
    page_icon="📊",
    layout="wide",
)

# --- Carregamento dos dados dos municípios ---
mun = pd.read_csv("https://drive.google.com/uc?id=1sf_GMMj4r2Ed-nF_d_ry2kG-B6_dQWlM", sep = ',')
munSE = mun[['IBGE', 'IBGE7']]

# --- Carregamento dos dados ---
df = pd.read_csv("https://drive.google.com/uc?id=18NDljR5ZVrBg5TxyMGaStheGUFnoy5pW", sep = ',')
df['NEARMISS'] = np.where(df['FATOR_NEARMISS'] == 'Sim', 1, 0)

df = df[df["CODMUNRES"] > 280000]
df = pd.merge(df, munSE, how='left', left_on='CODMUNRES', right_on='IBGE')

df2 = df[['MUN', 'CODMUNRES','IBGE', 'IBGE7', 'ANO', 'POP']]
df2['POP'] = df2['POP'].astype('int64')


# --- Barra Lateral (Filtros) ---
st.sidebar.header("🔍 Filtros")

# Filtro de Ano
anos_disponiveis = sorted(df['ANO'].dropna().unique())
anos_selecionados = st.sidebar.multiselect("Ano", anos_disponiveis, default=anos_disponiveis)

# Filtro de Consultas
senioridades_disponiveis = sorted(df['CONSULTAS'].dropna().unique())
senioridades_selecionadas = st.sidebar.multiselect("Consultas", senioridades_disponiveis, default=senioridades_disponiveis)

# Filtro por Local de Nascimento
contratos_disponiveis = sorted(df['LOCNASC'].dropna().unique())
contratos_selecionados = st.sidebar.multiselect("Local de Nascimento", contratos_disponiveis, default=contratos_disponiveis)

# Filtro por Gestação
tamanhos_disponiveis = sorted(df['GESTACAO'].dropna().unique())
tamanhos_selecionados = st.sidebar.multiselect("Gestação", tamanhos_disponiveis, default=tamanhos_disponiveis)

# --- Filtragem do DataFrame ---
# O dataframe principal é filtrado com base nas seleções feitas na barra lateral.
df_filtrado = df[
    (df['ANO'].isin(anos_selecionados)) &
    (df['CONSULTAS'].isin(senioridades_selecionadas)) &
    (df['LOCNASC'].isin(contratos_selecionados)) &
    (df['GESTACAO'].isin(tamanhos_selecionados))
]

# --- Conteúdo Principal ---
st.title("Observatório do NearMiss Neonatal")
st.markdown("Explore os dados referente ao NearMiss Neonatal nos últimos anos. Utilize os filtros à esquerda para refinar sua análise.")

# --- Métricas Principais (KPIs) ---
st.subheader("Métricas gerais")

if not df_filtrado.empty:
    nNear_Miss = (df_filtrado['FATOR_NEARMISS']=='Sim').sum()
    pNear_Miss = round(nNear_Miss/len(df_filtrado['FATOR_NEARMISS']) * 1000, 2)
    total_registros = df_filtrado.shape[0]
    soma_por_mun = df.groupby('MUN')['NEARMISS'].sum()/df.groupby('MUN')['ANO'].sum()
    tNear_Miss = soma_por_mun.idxmax()
else:
    nNear_Miss, pNear_Miss, total_registros, tNear_Miss = 0, 0, 0, " "


col1, col2, col3, col4 = st.columns(4)
col1.metric("Número de Near Miss", nNear_Miss, "Registros no Sinasc")
col2.metric("Taxa de Near Miss", pNear_Miss, " por 1.000 (Nascidos vivos)")
col3.metric("Total de Nascidos Vivos no Período", total_registros, " Registros no Sinasc")
col4.metric("Maior taxa de Near Miss", tNear_Miss, "Município de Sergipe")

st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 25px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.metric(label="Metric", value=1000, delta=100)

st.markdown("---")


NM_ano = pd.crosstab(df['MUN'], df['ANO'])
NM_ano = pd.DataFrame(NM_ano)
NM_ano = NM_ano.reset_index()

NM_ano = pd.melt(
    NM_ano,
    id_vars=['MUN'],  # Colunas que permanecem como estão
    value_vars=[2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],  # Colunas a serem "desempilhadas"
    var_name='ANO',  # Nome da nova coluna de variáveis
    value_name='Nascidos_vivos')  # Nome da nova coluna de valores

NM_total = pd.crosstab(df_filtrado['IBGE7'], df_filtrado['NEARMISS'], margins=True, margins_name="Total")
NM_total = pd.DataFrame(NM_total)
NM_total = NM_total.reset_index()
NM_total = NM_total.drop(NM_total.index[-1])

NM_total["NM_taxa"] = round((NM_total[1] / NM_total["Total"]) * 1000,2)
#NM["NM_taxaNV"] = round((NM["NEARMISS"] / NM["Nascidos_vivos"]) * 1000,2)


NM = pd.crosstab(df['MUN'], df['ANO'], values=(df['FATOR_NEARMISS']=='Sim'), aggfunc=np.sum)
NM = pd.DataFrame(NM)
NM = NM.reset_index()

NM = pd.melt(
    NM,
    id_vars=['MUN'],  # Colunas que permanecem como estão
    value_vars=[2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],  # Colunas a serem "desempilhadas"
    var_name='ANO',  # Nome da nova coluna de variáveis
    value_name='NEARMISS')  # Nome da nova coluna de valores

NM = pd.merge(NM, df2, how='left', left_on=['MUN', 'ANO'], right_on=['MUN', 'ANO'])
NM = pd.merge(NM, NM_ano, how='left', left_on=['MUN', 'ANO'], right_on=['MUN', 'ANO'])
NM.drop_duplicates(inplace=True)

NM["NM_taxaPOP"] = round((NM["NEARMISS"] / NM["POP"]) * 1000,2)
NM["NM_taxaNV"] = round((NM["NEARMISS"] / NM["Nascidos_vivos"]) * 1000,2)

# Encontra os índices das linhas com o valor máximo para cada categoria
indices_max_valor = NM.groupby('MUN')['NM_taxaNV'].idxmax()

# Seleciona as linhas correspondentes no dataframe original
NM_max = NM.loc[indices_max_valor]
NM_max['NM_tmax'] = NM_max['NM_taxaNV']

NM_max = pd.merge(NM_max, NM_total[['NM_taxa', 'IBGE7']], on='IBGE7', how='left')


# Exemplo: Selecionar apenas os valores da coluna 'Valor1' onde a 'Categoria' é 'B'
NM_23 = NM[NM['ANO']==2023]
NM_23['NM_t23'] = NM_23['NM_taxaNV']

data = requests.get(
    "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-28-mun.json"
).json()

states = geopandas.GeoDataFrame.from_features(data, crs="EPSG:4326")
states['IBGE7'] = states['id'].astype('int64')

merged_states = pd.merge(states, NM_23[['POP', 'NM_t23', 'IBGE7']], on='IBGE7', how='left')
merged_states = pd.merge(merged_states, NM_max[['NM_tmax', 'ANO', 'NM_taxa', 'IBGE7']], on='IBGE7', how='left')


#Mapa inicial
mapa_idhm_se = folium.Map([-10.9095, -37.0748],
                         tiles = "cartodbpositron",
                         zoom_start = 8)

# Criando o mapa coropletico
folium.Choropleth(geo_data = merged_states,
                  data = NM_max,
                  columns = ["IBGE7", "NM_taxa"],
                  key_on = "feature.properties.id",
                  fill_color = "YlGnBu", # (exemplos: 'YlGnBu', 'RdPu', 'GnBu')
                  fill_opacity = 0.9,
                  line_opacity = 0.5,
                  legend_name = "Taxa de Near Miss por 10.000 habitantes",
                  nan_fill_color = "white",
                  name = "Dados").add_to(mapa_idhm_se)

#
#Adicionando a função de destaque
estilo = lambda x: {"fillColor": "white",
                   "color": "black",
                   "fillOpacity": 0.001,
                   "weight": 0.001}

estilo_destaque = lambda x: {"fillColor": "darkblue",
                            "color": "black",
                            "fillOpacity": 0.5,
                            "weight": 1}

highlight = folium.features.GeoJson(data = merged_states,
                                   style_function = estilo,
                                   highlight_function = estilo_destaque,
                                   name = "Destaque")


#Adicionando caixa de texto
folium.features.GeoJsonTooltip(fields = ['name', 'POP', 'NM_taxa', 'NM_t23', 'NM_tmax', 'ANO'],
                               aliases = ["Municipio: ", "População: (2023): ", "Taxa de Near Miss no período: ", "Taxa de Near Miss em 2023: ", "Maior Taxa de Near Miss: ", "Aconteceu no ano: "],
                               #labels = False,
                               localize=True,
                               sticky=False,
                               labels=True,
                               style = ("background-color: white; color: black; font-family: arial; font-size: 16px; padding: 10px;")).add_to(highlight)


#Adicionando o destaque ao mapa
mapa_idhm_se.add_child(highlight)

#Adicionando o controle de camadas
folium.LayerControl().add_to(mapa_idhm_se)

st_folium(mapa_idhm_se, width=800, height=600)

# --- Análises Visuais com Plotly ---
st.subheader("Gráficos")

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    if not df_filtrado.empty:
        top_NM = (df_filtrado.groupby('MUN')['NEARMISS'].sum()/df_filtrado.groupby('MUN')['NEARMISS'].count()*1000).nlargest(10).sort_values(ascending=True).reset_index()
        grafico_NM = px.bar(
            top_NM,
            x='NEARMISS',
            y='MUN',
            orientation='h',
            title="Os 10 (dez) Municípios com maiores taxas de Near Miss",
            labels={'NEAR MISS': 'Taxa de Near Miss (por 1.000 nascidos vivo)', 'MUN': ' '}
        )
        grafico_NM.update_layout(title_x=0.1, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(grafico_NM, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de cargos.")

with col_graf2:
    if not df_filtrado.empty:
        down_NM = (df_filtrado.groupby('MUN')['NEARMISS'].sum()/df_filtrado.groupby('MUN')['NEARMISS'].count()*1000).nsmallest(10).sort_values(ascending=True).reset_index()
        grafico_NM = px.bar(
            down_NM,
            x='NEARMISS',
            y='MUN',
            orientation='h',
            title="Os 10 (dez) Municípios com menores taxas de Near Miss",
            labels={'NEAR MISS': 'Taxa de Near Miss (por 1.000 nascidos vivo)', 'MUN': ' '}
        )
        grafico_NM.update_layout(title_x=0.1, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(grafico_NM, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de cargos.")




#col_graf3, col_graf4 = st.columns(2)

    


# --- Tabela de Dados Detalhados ---
st.subheader("Dados Detalhados")
st.dataframe(df_filtrado)




