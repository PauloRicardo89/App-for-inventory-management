import tkinter as tk
from tkinter import messagebox, simpledialog

class Produto:
    def __init__(self, nome, quantidade, preco_compra, preco_venda):
        self.nome = nome
        self.quantidade = quantidade
        self.preco_compra = preco_compra
        self.preco_venda = preco_venda

class Estoque:
    def __init__(self):
        self.produtos = []

    def registrar_entrada(self, produto):
        self.produtos.append(produto)

    def consultar_produto(self, query):
        resultados = []
        for produto in self.produtos:
            if query.lower() in produto.nome.lower():
                resultados.append(produto)
        return resultados

class DialogoAdicionarProduto(tk.Toplevel):
    def __init__(self, parent, estoque):
        super().__init__(parent)
        self.title("Adicionar Produto")
        self.estoque = estoque

        self.nome = tk.StringVar()
        self.quantidade = tk.StringVar()
        self.preco_compra = tk.StringVar()
        self.preco_venda = tk.StringVar()

        tk.Label(self, text="Nome do produto:").grid(row=0, column=0)
        tk.Entry(self, textvariable=self.nome).grid(row=0, column=1)

        tk.Label(self, text="Quantidade do produto:").grid(row=1, column=0)
        tk.Entry(self, textvariable=self.quantidade).grid(row=1, column=1)

        tk.Label(self, text="Preço de compra do produto (R$):").grid(row=2, column=0)
        tk.Entry(self, textvariable=self.preco_compra).grid(row=2, column=1)

        tk.Label(self, text="Preço de venda do produto (R$):").grid(row=3, column=0)
        tk.Entry(self, textvariable=self.preco_venda).grid(row=3, column=1)

        tk.Button(self, text="Salvar", command=self.salvar_produto).grid(row=4, column=1)

    def salvar_produto(self):
        try:
            produto = Produto(
                nome=self.nome.get(),
                quantidade=int(self.quantidade.get()),
                preco_compra=float(self.preco_compra.get()),
                preco_venda=float(self.preco_venda.get())
            )
            self.estoque.registrar_entrada(produto)
            messagebox.showinfo("Sucesso", "Produto adicionado com sucesso!")
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao adicionar o produto: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Um erro inesperado ocorreu: {e}")

class Aplicativo:
    def __init__(self, master):
        self.master = master
        self.master.title("Aplicativo de Estoque")
        self.estoque = Estoque()

        # Configura o tamanho da janela
        largura_janela = self.master.winfo_screenwidth()
        altura_janela = self.master.winfo_screenheight()
        self.master.geometry(f"{largura_janela}x{altura_janela}+0+0")

        # Configura o gerenciador de layout grid para a janela principal
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=7, uniform="grupo")  # 70% para o conteúdo principal
        self.master.grid_columnconfigure(1, weight=3, uniform="grupo")  # 30% para a faixa lateral

        # Cria um frame para o conteúdo principal com cor cinza claro
        self.frame_principal = tk.Frame(master, bg='lightgrey')
        self.frame_principal.grid(row=0, column=0, sticky='nsew')

        # Cria um frame para a faixa lateral com cor azul escuro
        self.frame_lateral = tk.Frame(master, bg='darkblue')
        self.frame_lateral.grid(row=0, column=1, sticky='nsew')

        # Adiciona botões ao frame lateral com tamanhos proporcionais à parte azul
        self.botao_adicionar = tk.Button(self.frame_lateral, text="Adicionar Produto", bg='green', fg='white', command=self.abrir_dialogo_adicionar)
        self.botao_adicionar.grid(row=0, column=0, sticky='ew', padx=30, pady=30, ipady=10)

        self.botao_pesquisar = tk.Button(self.frame_lateral, text="Pesquisar Produto", bg='white', fg='black', command=self.pesquisar_produto)
        self.botao_pesquisar.grid(row=1, column=0, sticky='ew', padx=30, pady=0, ipady=10)
        
        # Configura os botões para expandirem e preencherem o espaço disponível
        self.frame_lateral.grid_rowconfigure(0, weight=0)
        self.frame_lateral.grid_rowconfigure(1, weight=0)
        self.frame_lateral.grid_columnconfigure(0, weight=1)

          
    def abrir_dialogo_adicionar(self):
        DialogoAdicionarProduto(self.master, self.estoque)

    def pesquisar_produto(self):
        query = simpledialog.askstring("Pesquisar produto", "Nome do produto:")
        if query is not None and query.strip():
            produtos = self.estoque.consultar_produto(query)
            if produtos:
                resultados = "\n".join(f"Produto: {produto.nome}, Quantidade: {produto.quantidade}" for produto in produtos)
                messagebox.showinfo("Pesquisar produto", f"Produtos encontrados:\n{resultados}")
            else:
                messagebox.showinfo("Pesquisar produto", "Nenhum produto encontrado para a pesquisa.")
        # Não faz nada se a janela de diálogo for fechada ou se nada for digitado

if __name__ == "__main__":
    janela = tk.Tk()
    app = Aplicativo(janela)
    janela.mainloop()    