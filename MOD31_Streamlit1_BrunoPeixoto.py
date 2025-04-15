import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from PIL import Image
from io import BytesIO
import xlsxwriter


custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks",rc=custom_params)

@st.cache_data(show_spinner = True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data,sep=';')
    except:
        return pd.read_excel(file_data)

@st.cache_resource()
def multiselect_filter(relatorio,col,selecionados):
    if 'all' in selecionados:
        return relatorio
    else:
        return relatorio[relatorio[col].isin(selecionados)].reset_index(drop=True)

@st.cache_resource()
def df_toString(df):
    return df.to_csv(index=False)

@st.cache_resource()
def df_toExcel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output,engine='xlsxwriter')
    df.to_excel(writer,index=False, sheet_name = 'Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def recencia_class(x,r,q_dict):
    if x <= q_dict[r][0.25]:
        return 'A'
    elif x <= q_dict[r][0.5]:
        return 'B'
    elif x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'

def freq_val_class(x,fv,q_dict):
    if x <= q_dict[fv][0.25]:
        return 'D'
    elif x <= q_dict[fv][0.5]:
        return 'C'
    elif x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'

def main():
    st.set_page_config(page_title = 'Análise RFV', \
                       layout = 'wide',
                       initial_sidebar_state = 'expanded'
                       )
    st.write('''# Análise RFV
             
    RFV significa Recência, Frequência e Valor, e é utilizado para segmentação de clientes baseado no comportamento de compras dos clientes e agrupa eles em clusters parecidos. Utilizando esse tipo de agrupamento podemos realizar ações de marketing e CRM melhores direcionadas, ajudando assim na personalização do conteúdo e até a retenção de clientes.
    
    Para cada cliente é preciso calcular cada uma das componentes abaixo:
    - Recência (R): Quantidade de dias desde a última compra.
    - Frequência (F): Quantidade total de compras no período.
    - Valor (V): Total de dinheiro gasto nas compras do período.
    
    E é isso que iremos fazer abaixo.
             
             ''')
    st.markdown('---')

    st.sidebar.write("## Faça o upload do arquivo")

    data_file_1 = st.sidebar.file_uploader("Bank marketing data",type=['csv','xlsx'])

    if (data_file_1 is not None):

        df_compras = pd.read_csv(data_file_1,infer_datetime_format=True,parse_dates=['DiaCompra'])

        st.write(df_compras.head())

        st.write('## Recência (R)')
        
        dia_atual = df_compras['DiaCompra'].max()
        st.write('Dia máximo na base de dados: ',dia_atual)

        st.write('Quantos dias faz que o cliente fez a sua última compra?')

        df_recencia = df_compras.groupby(by='ID_cliente', as_index=False)['DiaCompra'].max()
        df_recencia.columns = ['ID_cliente','DiaUltimaCompra']
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual - x).days)
        st.write(df_recencia.head())

        df_recencia.drop('DiaUltimaCompra',axis=1,inplace=True)

        st.write('## Frequência (F)')
        st.write('Quantas compras o cliente fez no período?')

        df_frequencia = df_compras[['ID_cliente','CodigoCompra']].groupby('ID_cliente').count().reset_index()
        df_frequencia.columns = ['ID_cliente','Frequencia']
        st.write(df_frequencia.head())

        st.write('## Valor (V)')
        st.write('Quanto cada cliente gastou no período?')

        df_valor = df_compras[['ID_cliente','ValorTotal']].groupby('ID_cliente').sum().reset_index()
        df_valor.columns = ['ID_cliente','Valor']
        st.write(df_valor.head())

        st.write('## Tabela RFV Final')

        df_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
        df_RFV = df_RF.merge(df_valor, on='ID_cliente')
        df_RFV.set_index('ID_cliente', inplace=True)
        st.write(df_RFV.head())

        st.markdown('---')

        st.write('## Segmentação Utilizando o RFV')

        st.write('''
        Um jeito de segmentar os clientes é criando quartis para cada componente do RFV, sendo que o melhor quartil é chamado de 'A', o segundo melhor quartil de 'B', o terceiro melhor de 'C' e o pior de 'D'. O melhor e o pior depende da componente. Po exemplo, quanto menor a recência melhor é o cliente (pois ele comprou com a gente tem pouco tempo) logo o menor quartil seria classificado como 'A', já pra componente frêquencia a lógica se inverte, ou seja, quanto maior a frêquencia do cliente comprar com a gente, melhor ele/a é, logo, o maior quartil recebe a letra 'A'.
        Se a gente tiver interessado em mais ou menos classes, basta a gente aumentar ou diminuir o número de quantils pra cada componente.
                 ''')

        st.write('### Quartis para o RFV')
        quartis = df_RFV.quantile(q=[0.25,0.5,0.75])
        st.write(quartis)

        st.write('Tabela após a criação dos grupos')
        df_RFV['R_Quartile'] = df_RFV['Recencia'].apply(recencia_class,
                                            args = ('Recencia',quartis))
        df_RFV['F_Quartile'] = df_RFV['Frequencia'].apply(freq_val_class,
                                            args = ('Frequencia',quartis))
        df_RFV['V_Quartile'] = df_RFV['Valor'].apply(freq_val_class,
                                            args = ('Valor',quartis))    
        
        df_RFV['RFV_Score'] = df_RFV.R_Quartile + df_RFV.F_Quartile + df_RFV.V_Quartile
        st.write(df_RFV.head())

        st.write('### Quantidade de clientes por grupo')
        st.write(df_RFV.groupby('RFV_Score').size().reset_index(name = 'Quantidade de Clientes').sort_values(by='Quantidade de Clientes', ascending=False))

        st.write('### Clientes com menor recência, maior frequência e maior valor gasto')
        st.write(df_RFV[df_RFV['RFV_Score']=='AAA'].sort_values('Valor').head(10))
        
        st.write('### Ações de marketing/CRM')
        
        dict_acoes = {'AAA':'Melhor cliente, ações de marketing personalizadas',
                      'BBB':'Cliente ativo, ações de marketing padronizadas',
                      'CCC':'Cliente inativo, ações de reativação',
                      'DDD':'Cliente inativo, sem ações de reativação',}

        df_RFV['Acoes'] = df_RFV['RFV_Score'].map(dict_acoes)
        st.write(df_RFV.head())

        df_xlsx = df_toExcel(df_RFV)
        st.download_button(label='📥 Download',
                           data=df_xlsx,
                           file_name='RFV.xlsx')
        
        st.write('Quantidade de clientes por tipo de ação')
        st.write(df_RFV['Acoes'].value_counts(dropna=False))

        
if __name__ == '__main__':
    main()

    