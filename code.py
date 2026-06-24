import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd




# Classe utilitária para redirecionar o 'print' para dentro da caixa de texto do Tkinter
class TextRedirector:


    def __init__(self, widget):
        self.widget = widget


    def write(self, str):
        self.widget.insert(tk.END, str)
        self.widget.see(tk.END)  # Rola o texto automaticamente para o final


    def flush(self):
        pass




class AppTriangulacao:


    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Análise de DNA - Triangulação & Cromossomo X")
        self.janela.geometry("900x650")


        # Criando as Abas (Tabs)
        self.tab_control = ttk.Notebook(janela)


        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)


        self.tab_control.add(self.tab1, text="1. Etapa de Triangulação")
        self.tab_control.add(self.tab2, text="2. Análise do Cromossomo X")
        self.tab_control.pack(expand=1, fill="both")


        # Inicializar os elementos de cada aba
        self.configurar_aba1()
        self.configurar_aba2()


    # --- ABA 1: TRIANGULAÇÃO ---
    def configurar_aba1(self):
        frame_topo = ttk.LabelFrame(self.tab1, text=" Seleção do Arquivo ")
        frame_topo.pack(fill="x", padx=10, pady=10)


        self.lbl_caminho1 = ttk.Label(
            frame_topo, text="Nenhum arquivo selecionado..."
        )
        self.lbl_caminho1.pack(side="left", padx=10, pady=10, expand=True, fill="x")


        btn_procurar = ttk.Button(
            frame_topo, text="Procurar CSV", command=self.selecionar_arquivo1
        )
        btn_procurar.pack(side="right", padx=10, pady=10)


        # Botão para processar
        self.btn_processar1 = ttk.Button(
            self.tab1,
            text="Processar Triangulação",
            command=self.processar_triangulacao,
            state="disabled",
        )
        self.btn_processar1.pack(pady=5)


        # Área de Resultado (Console)
        frame_txt = ttk.Frame(self.tab1)
        frame_txt.pack(fill="both", expand=True, padx=10, pady=10)


        self.txt_output1 = tk.Text(
            frame_txt, wrap="none", font=("Courier", 10), bg="#1e1e1e", fg="#ffffff"
        )
        scroll_y = ttk.Scrollbar(
            frame_txt, orient="vertical", command=self.txt_output1.yview
        )
        scroll_x = ttk.Scrollbar(
            frame_txt, orient="horizontal", command=self.txt_output1.xview
        )


        self.txt_output1.configure(
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set
        )


        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.txt_output1.pack(side="left", fill="both", expand=True)


    def selecionar_arquivo1(self):
        caminho = filedialog.askopenfilename(
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )
        if caminho:
            self.lbl_caminho1.config(text=caminho)
            self.caminho_arquivo1 = caminho
            self.btn_processar1.config(state="normal")


    def processar_triangulacao(self):
        resposta = messagebox.askyesno(
            "Confirmação",
            f"O caminho do arquivo está correto?\n\n{self.caminho_arquivo1}",
        )
        if not resposta:
            messagebox.showinfo("Aviso", "Ação cancelada para corrigir o arquivo.")
            return


        self.txt_output1.delete("1.0", tk.END)
        sys.stdout = TextRedirector(self.txt_output1)


        try:
            arquivo = pd.read_csv(self.caminho_arquivo1, header=None)


            col_chr = 0
            col_kit_a = 1
            col_nome_a = 2
            col_kit_b = 4
            col_nome_b = 5
            col_inicio = 7
            col_fim = 8


            cromossomos_disponiveis = (
                arquivo[col_chr].astype(str).str.strip().unique()
            )


            def sort_key(x):
                try:
                    return int(x)
                except ValueError:
                    return 999


            cromossomos_ordenados = sorted(cromossomos_disponiveis, key=sort_key)


            total_geral_segmentos = 0
            total_geral_triangulacoes = 0
            resumo_por_chr = []


            for chrom in cromossomos_ordenados:
                df_atual = arquivo[
                    arquivo[col_chr].astype(str).str.strip() == chrom
                ].copy()
                if df_atual.empty:
                    continue


                df_atual["Par_Formatado"] = (
                    "Kit: "
                    + df_atual.iloc[:, col_kit_a].astype(str)
                    + " ("
                    + df_atual.iloc[:, col_nome_a].astype(str)
                    + ") <-> "
                    + "Kit: "
                    + df_atual.iloc[:, col_kit_b].astype(str)
                    + " ("
                    + df_atual.iloc[:, col_nome_b].astype(str)
                    + ")"
                )


                def extrair_kits_unicos(group):
                    todos_os_kits = pd.concat(
                        [group.iloc[:, col_kit_a], group.iloc[:, col_kit_b]]
                    )
                    return todos_os_kits.astype(str).str.strip().nunique()


                # LINHA CORRIGIDA AQUI:
                df_contagem = (
                    df_atual.groupby([col_inicio, col_fim])
                    .apply(extrair_kits_unicos)
                    .reset_index()
                )
                df_contagem.columns = [col_inicio, col_fim, "Qtd_Kits"]


                df_nomes = (
                    df_atual.groupby([col_inicio, col_fim])["Par_Formatado"]
                    .unique()
                    .reset_index()
                )
                agrupado = pd.merge(df_nomes, df_contagem, on=[col_inicio, col_fim])


                total_geral_segmentos += len(agrupado)
                total_geral_triangulacoes += len(df_atual)
                resumo_por_chr.append([chrom, len(agrupado), len(df_atual)])


                print("\n" + "=" * 130)
                print(f" CROMOSSOMO: {chrom} ".center(130, "#"))
                print("=" * 130)
                print(
                    f"{'INÍCIO':<15} | {'FIM':<15} | {'KITS':<6} | {'TRIANGULAÇÕES NO SEGMENTO'}"
                )
                print("-" * 130)


                for _, row in agrupado.iterrows():
                    inicio = str(row[col_inicio]).strip()
                    fim = str(row[col_fim]).strip()
                    qtd = str(row["Qtd_Kits"])
                    lista_triangulacoes = row["Par_Formatado"]


                    print(
                        f"{inicio:<15} | {fim:<15} | {qtd:<6} | {lista_triangulacoes[0]}"
                    )
                    for outra in lista_triangulacoes[1:]:
                        print(f"{'':<15} | {'':<15} | {'':<6} | {outra}")
                    print("-" * 130)


            print("\n" + " RELATÓRIO FINAL DE TRIANGULAÇÃO ".center(130, "!"))
            print("-" * 130)
            print(
                f"{'CHR':<10} | {'SEGMENTOS ÚNICOS':<20} | {'TOTAL DE TRIANGULAÇÕES'}"
            )
            print("-" * 60)


            for r in resumo_por_chr:
                print(f"{r[0]:<10} | {r[1]:<20} | {r[2]}")


            print("-" * 60)
            print(
                f"{'TOTAL':<10} | {total_geral_segmentos:<20} | {total_geral_triangulacoes}"
            )
            print("-" * 130)


            messagebox.showinfo("Sucesso", "Processamento concluído!")


        except Exception as e:
            messagebox.showerror(
                "Erro", f"Ocorreu um erro ao processar o arquivo:\n{e}"
            )
        finally:
            sys.stdout = sys.__stdout__


    # --- ABA 2: CROMOSSOMO X ---
    def configurar_aba2(self):
        frame_topo = ttk.LabelFrame(self.tab2, text=" Seleção do Arquivo 'ONE TO MANY' ")
        frame_topo.pack(fill="x", padx=10, pady=10)


        self.lbl_caminho2 = ttk.Label(
            frame_topo, text="Nenhum arquivo selecionado..."
        )
        self.lbl_caminho2.pack(side="left", padx=10, pady=10, expand=True, fill="x")


        btn_procurar = ttk.Button(
            frame_topo, text="Procurar CSV", command=self.selecionar_arquivo2
        )
        btn_procurar.pack(side="right", padx=10, pady=10)


        self.btn_processar2 = ttk.Button(
            self.tab2,
            text="Analisar Cromossomo X",
            command=self.processar_cromossomo_x,
            state="disabled",
        )
        self.btn_processar2.pack(pady=5)


        # Área de Resultado
        frame_txt = ttk.Frame(self.tab2)
        frame_txt.pack(fill="both", expand=True, padx=10, pady=10)


        self.txt_output2 = tk.Text(
            frame_txt, wrap="none", font=("Courier", 10), bg="#1e1e1e", fg="#ffffff"
        )
        scroll_y = ttk.Scrollbar(
            frame_txt, orient="vertical", command=self.txt_output2.yview
        )
        scroll_x = ttk.Scrollbar(
            frame_txt, orient="horizontal", command=self.txt_output2.xview
        )


        self.txt_output2.configure(
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set
        )


        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.txt_output2.pack(side="left", fill="both", expand=True)


    def selecionar_arquivo2(self):
        caminho = filedialog.askopenfilename(
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )
        if caminho:
            self.lbl_caminho2.config(text=caminho)
            self.caminho_arquivo2 = caminho
            self.btn_processar2.config(state="normal")


    def processar_cromossomo_x(self):
        resposta = messagebox.askyesno(
            "Confirmação",
            f"O caminho do arquivo está correto?\n\n{self.caminho_arquivo2}",
        )
        if not resposta:
            messagebox.showinfo("Aviso", "Ação cancelada para corrigir o arquivo.")
            return


        self.txt_output2.delete("1.0", tk.END)
        sys.stdout = TextRedirector(self.txt_output2)


        try:
            arquivo = pd.read_csv(self.caminho_arquivo2, sep=",", skiprows=2)


            filtro = arquivo["Largest - X-DNA"] > 0
            resultado = arquivo.loc[filtro, ["Kit", "Name", "Largest - X-DNA"]]
            resultado = resultado.sort_values(by="Largest - X-DNA", ascending=False)


            print(resultado.to_string(index=False))


            tamanho = len(resultado)
            print("\n" + "-" * 60)
            print(
                f"O número de pessoas que compartilham DNA no cromossomo X são: {tamanho}"
            )
            print("-" * 60)


            messagebox.showinfo("Sucesso", "Análise concluída!")


        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Ocorreu um erro. Verifique se o arquivo possui a coluna 'Largest - X-DNA'.\n\nErro detalhado: {e}",
            )
        finally:
            sys.stdout = sys.__stdout__




# Executar o App usando 'janela_principal' em vez de 'root'
if __name__ == "__main__":
    janela_principal = tk.Tk()
    app = AppTriangulacao(janela_principal)
    janela_principal.mainloop()

