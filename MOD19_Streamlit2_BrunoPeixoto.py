import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from PIL import Image
from io import BytesIO

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

def main():
    st.set_page_config(page_title = 'Telemarketing Analisys', \
                       page_icon = './telmarketing_icon.png',
                       layout = 'wide',
                       initial_sidebar_state = 'expanded'
                       )
    st.write('# Telemarketing Analysis')
    st.markdown('---')

    image = Image.open("./Bank-Branding.jpg")
    st.sidebar.image(image)

    st.sidebar.write("## Faça o upload do arquivo")

    data_file_1 = st.sidebar.file_uploader("Bank marketing data",type=['csv','xlsx'])

    if (data_file_1 is not None):

        bank_raw = load_data(data_file_1)
        bank = bank_raw.copy()

        st.write('## Antes dos filtros')
        st.write(bank_raw.head(5))

        with st.sidebar.form(key='my_form'):

            # SELECIONA O TIPO DE GRÁFICO
            graph_type = st.radio('Tipo de gráfico:',('Barras','Pizza'))


            # IDADES

            max_age = int(bank.age.max())
            min_age = int(bank.age.min())
            idades=st.slider(label = 'Idade',
                                min_value = min_age,
                                max_value = max_age,
                                value = (min_age,max_age),
                                step = 1)

            # PROFISSÕES
            jobs_list = bank.job.unique().tolist()
            jobs_list.append('all')
            jobs_selected = st.multiselect("Profissão",jobs_list,['all'])
        
            # ESTADO CIVIL
            marital_list = bank.marital.unique().tolist()
            marital_list.append('all')
            marital_selected = st.multiselect("Estado Civil",marital_list,['all'])
        
            # DEFAULT
            default_list = bank.default.unique().tolist()
            default_list.append('all')
            default_selected = st.multiselect("Default",default_list,['all'])

            # TEM FINANCIAMENTO IMOBILIÁRIO?
            housing_list = bank.housing.unique().tolist()
            housing_list.append('all')
            housing_selected = st.multiselect("Tem financiamento imob?",housing_list,['all'])

            # TEM EMPRESTIMO?
            loan_list = bank.loan.unique().tolist()
            loan_list.append('all')
            loan_selected = st.multiselect("Tem empréstimo?",loan_list,['all'])

            # MEIO DE CONTATO
            contact_list = bank.contact.unique().tolist()
            contact_list.append('all')
            contact_selected = st.multiselect("Meio de contato",contact_list,['all'])

            # MÊS DO CONTATO
            month_list = bank.month.unique().tolist()
            month_list.append('all')
            month_selected = st.multiselect("Mês de contato",month_list,['all'])

            # DIA DA SEMANA
            day_of_week_list = bank.day_of_week.unique().tolist()
            day_of_week_list.append('all')
            day_of_week_selected = st.multiselect("Dia da Semana",day_of_week_list,['all'])
    
            #bank = bank[(bank['age'] >= idades[0]) & (bank['age'] <= idades[1])]
            #bank = bank[bank['job'].isin(jobs_selected)].reset_index(drop=True)

            bank = (bank.query("age >= @idades[0] and age <= @idades[1]")
                    .pipe(multiselect_filter, 'job',jobs_selected)
                    .pipe(multiselect_filter, 'marital',marital_selected)
                    .pipe(multiselect_filter, 'default',default_selected)
                    .pipe(multiselect_filter, 'housing',housing_selected)
                    .pipe(multiselect_filter, 'loan',loan_selected)
                    .pipe(multiselect_filter, 'contact',contact_selected)
                    .pipe(multiselect_filter, 'month',month_selected)
                    .pipe(multiselect_filter, 'day_of_week',day_of_week_selected)
                    )
            
            submit_button = st.form_submit_button(label = 'Aplicar')


        st.write('## Após os filtros')
        st.write(bank.head())


        df_xlsx = df_toExcel(bank)
        st.download_button(label = 'Download da tabela filtrada em EXCEL',
                           data = df_xlsx,
                           file_name = 'bank_filtered.xlsx')
        st.markdown("---")

        bank_raw_target_perc = bank_raw.y.value_counts(normalize=True).reset_index()
        bank_raw_target_perc.columns = ['y', 'proportion']
   
        bank_target_perc = bank.y.value_counts(normalize=True).reset_index()
        bank_target_perc.columns = ['y','proportion']

        # TABELAS DE PROPORÇÃO E DOWNLOAD

        col1,col2 = st.columns(2)

        df_xlsx = df_toExcel(bank_raw_target_perc)
        col1.write('### Proporção original')
        col1.write(bank_raw_target_perc)
        col1.download_button(label='Download',
                            data = df_xlsx,
                            file_name = 'bank_raw_proportion.xlsx')

        df_xlsx = df_toExcel(bank_target_perc)
        col2.write('### Proporção com filtros')
        col2.write(bank_target_perc)
        col2.download_button(label='Download',
                            data = df_xlsx,
                            file_name = 'bank_filtered_proportion.xlsx')

        fig, ax = plt.subplots(1,2, figsize = (6,3))

        # PLOTS
        if graph_type == 'Barras':
            sns.barplot(x='y',
                        y ='proportion',
                        data = bank_raw_target_perc,
                        palette=['blue','darkorange'],
                        ax = ax[0])
            ax[0].bar_label(ax[0].containers[0])
            ax[0].set_title('Dados brutos',
                            fontweight = 'bold')
    
            sns.barplot(x = 'y',
                        y = 'proportion',
                        data = bank_target_perc,
                        palette=['blue','darkorange'],
                        ax = ax[1])
            ax[1].bar_label(ax[1].containers[0])
            ax[1].set_title('Dados filtrados',
                            fontweight = 'bold')
        else:
            bank_raw_target_perc.plot(kind='pie', autopct = '%.2f',y='proportion',labels=bank_raw_target_perc['y'],ax=ax[0])
            ax[0].set_title('Dados brutos',
                            fontweight = 'bold')
            bank_target_perc.plot(kind='pie', autopct = '%.2f',y='proportion',labels=bank_target_perc['y'], ax=ax[1])
            ax[1].set_title('Dados filtrados',
                            fontweight = 'bold')
    
        st.write('## Proporção de aceite')

        st.pyplot(plt)


if __name__ == '__main__':
    main()

    
