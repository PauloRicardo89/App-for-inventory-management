import os
import sqlite3
import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, scrolledtext

# Conectar ao banco de dados SQLite
diretorio_atual = os.path.dirname(os.path.realpath(__file__))
caminho_banco_de_dados = os.path.join(diretorio_atual, 'estoque_local.db')
conexao = sqlite3.connect(caminho_banco_de_dados)
cursor = conexao.cursor()

# Criar a tabela de produtos, se ela não existir
cursor.execute('''
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_venda REAL NOT NULL,
    caminho_imagem TEXT
)
''')
conexao.commit()
# Criar a tabela de movimentações, se ela não existir
cursor.execute('''
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,  -- 'entrada' ou 'saida'
    quantidade INTEGER NOT NULL,
    data_hora TEXT NOT NULL,
    FOREIGN KEY (produto_id) REFERENCES produtos (id)
)
''')
conexao.commit()

class Produto:
    def __init__(self, nome, quantidade, preco_venda, caminho_imagem):
        self.nome = nome
        self.quantidade = quantidade
        self.preco_venda = preco_venda
        self.caminho_imagem = caminho_imagem

class Estoque:
    def __init__(self):
        self.conexao = conexao
        self.cursor = cursor

    def registrar_entrada(self, produto, quantidade):
        self.cursor.execute('''
            INSERT INTO produtos (nome, quantidade, preco_venda, caminho_imagem)
            VALUES (?, ?, ?, ?)
        ''', (produto.nome, produto.quantidade, produto.preco_venda, produto.caminho_imagem))
        self.conexao.commit()
        produto_id = self.cursor.lastrowid 
        data_hora_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, data_hora)
            VALUES (?, 'entrada', ?, ?)
        ''', (produto.id, quantidade, data_hora_atual))
        self.conexao.commit()

    def consultar_produto(self, query):
        self.cursor.execute('''
            SELECT * FROM produtos WHERE nome LIKE ?
        ''', ('%' + query + '%',))
        return self.cursor.fetchall()
    
    def registrar_saida(self, produto_id, quantidade_saida, event=None):
        self.cursor.execute('''
            UPDATE produtos SET quantidade = quantidade - ? WHERE id = ? AND quantidade - ? >= 0
        ''', (quantidade_saida, produto_id, quantidade_saida))
        if self.cursor.rowcount == 0:
            raise ValueError("Não há quantidade suficiente no estoque para essa saída.")
        self.conexao.commit()
        data_hora_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, data_hora)
            VALUES (?, 'saida', ?, ?)
        ''', (produto_id, quantidade_saida, data_hora_atual))
        self.conexao.commit()

    def adicionar_ou_atualizar_produto(self, nome_produto, quantidade_nova, preco_venda, caminho_imagem):
    # Verifica se o produto já existe no banco de dados
        self.cursor.execute("SELECT id, quantidade FROM produtos WHERE nome = ?", (nome_produto,))
        resultado = self.cursor.fetchone()
    
        if resultado:
        # Se o produto já existe, atualiza a quantidade e registra a movimentação
            produto_id, quantidade_atual = resultado
            nova_quantidade = quantidade_atual + quantidade_nova
            self.cursor.execute("UPDATE produtos SET quantidade = ?, preco_venda = ?, caminho_imagem = ? WHERE nome = ?", (nova_quantidade, preco_venda, caminho_imagem, nome_produto))
            self.registrar_movimentacao(produto_id, 'entrada', quantidade_nova)
        else:
        # Se o produto não existe, insere um novo registro e registra a movimentação
            self.cursor.execute("INSERT INTO produtos (nome, quantidade, preco_venda, caminho_imagem) VALUES (?, ?, ?, ?)", (nome_produto, quantidade_nova, preco_venda, caminho_imagem))
            produto_id = self.cursor.lastrowid
            self.registrar_movimentacao(produto_id, 'entrada', quantidade_nova)
        self.conexao.commit()

    def buscar_produtos_por_nome(self, nome_produto):
        self.cursor.execute("SELECT id, nome, quantidade FROM produtos WHERE nome LIKE ?", ('%' + nome_produto + '%',))
        return self.cursor.fetchall()
    
    def buscar_movimentacoes_recentes(self):
        self.cursor.execute("SELECT * FROM movimentacoes ORDER BY data_hora DESC")
        return self.cursor.fetchall()
    
    def registrar_movimentacao(self, produto_id, tipo, quantidade):
        data_hora_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, data_hora)
            VALUES (?, ?, ?, ?)
        ''', (produto_id, tipo, quantidade, data_hora_atual))
        self.conexao.commit()

class DialogoAdicionarProduto(tk.Toplevel):
    def __init__(self, parent, estoque, app_parent):
        super().__init__(parent)
        self.title("Adicionar Produto")
        self.estoque = estoque
        self.parent = app_parent

        self.nome = tk.StringVar()
        self.quantidade = tk.StringVar()
        self.preco_venda = tk.StringVar()
        self.caminho_imagem = tk.StringVar()
        self.entrada_nome_produto = tk.Entry(self, textvariable=self.nome)
        self.entrada_nome_produto.grid(row=0, column=1)
        self.bind('<Escape>', lambda event: self.destroy())

        tk.Label(self, text="Nome do produto:").grid(row=0, column=0)
        self.entrada_nome_produto = tk.Entry(self, textvariable=self.nome)
        self.entrada_nome_produto.grid(row=0, column=1)

        tk.Label(self, text="Quantidade do produto:").grid(row=1, column=0)
        tk.Entry(self, textvariable=self.quantidade).grid(row=1, column=1)

        tk.Label(self, text="Preço de venda do produto (R$):").grid(row=2, column=0)
        tk.Entry(self, textvariable=self.preco_venda).grid(row=2, column=1)

        tk.Label(self, text="Caminho da imagem do produto:").grid(row=3, column=0)
        tk.Entry(self, textvariable=self.caminho_imagem).grid(row=3, column=1)
        tk.Button(self, text="Selecionar Imagem", command=self.selecionar_imagem).grid(row=3, column=2)
        # Botão Salvar
        botao_salvar = tk.Button(self, text="Salvar", command=self.salvar_produto)
        botao_salvar.grid(row=4, column=1)
        botao_salvar.bind('<Return>', self.salvar_produto)
        botao_salvar.focus_set()


       
    def selecionar_imagem(self):
        caminho_arquivo = filedialog.askopenfilename()
        if caminho_arquivo:
            self.caminho_imagem.set(caminho_arquivo)

    def salvar_produto(self, event=None):
        try:
            nome=self.nome.get()
            quantidade=int(self.quantidade.get())
            preco_venda=float(self.preco_venda.get())
            caminho_imagem=self.caminho_imagem.get()

            # Adicionar ou atualizar o produto no estoque
            self.estoque.adicionar_ou_atualizar_produto(nome, quantidade, preco_venda, caminho_imagem)
            messagebox.showinfo("Sucesso", "Produto adicionado com sucesso!")
            self.destroy()
            self.parent.atualizar_area_atualizacoes()
            #self.parent.exibir_atualizacoes_estoque()
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

        # Botão para exibir/fechar atualizações do estoque
        self.botao_atualizacoes = tk.Button(self.frame_principal, text="Exibir Atualizações do Estoque", bg='blue', fg='white', command=self.toggle_atualizacoes_estoque, highlightthickness=4, bd=4)
        self.botao_atualizacoes.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        self.botao_atualizacoes.bind('<Return>', lambda event: self.toggle_atualizacoes_estoque())
        self.frame_principal.grid_rowconfigure(1, weight=1)
        self.frame_principal.grid_columnconfigure(0, weight=1)
        self.texto_atualizacoes = scrolledtext.ScrolledText(self.frame_principal, wrap=tk.WORD, font=('Arial', 16), state='disabled')
        self.texto_atualizacoes.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.texto_atualizacoes.grid_remove()
        
        # Cria um frame para a faixa lateral com cor azul escuro
        self.frame_lateral = tk.Frame(master, bg='darkblue')
        self.frame_lateral.grid(row=0, column=1, sticky='nsew')

        # Adiciona botões ao frame lateral com tamanhos proporcionais à parte azul
        self.botao_adicionar = tk.Button(self.frame_lateral, text="Adicionar Produto", bg='green', fg='white', command=self.abrir_dialogo_adicionar)
        self.botao_adicionar.grid(row=0, column=0, sticky='ew', padx=30, pady=30, ipady=10)
        self.botao_adicionar.bind('<Return>', lambda event: self.abrir_dialogo_adicionar())

        self.botao_pesquisar = tk.Button(self.frame_lateral, text="Pesquisar Produto", bg='white', fg='black', command=self.pesquisar_produto)
        self.botao_pesquisar.grid(row=1, column=0, sticky='ew', padx=30, pady=0, ipady=10)
        self.botao_pesquisar.bind('<Return>', lambda event: self.pesquisar_produto())
        
        # Adiciona o botão 'Registrar Saída' ao frame lateral
        self.botao_registrar_saida = tk.Button(self.frame_lateral, text="Registrar Saída", bg='red', fg='white', command=self.abrir_dialogo_registrar_saida)
        self.botao_registrar_saida.grid(row=2, column=0, sticky='ew', padx=30, pady=600, ipady=10)
        self.botao_registrar_saida.bind('<Return>', lambda event: self.abrir_dialogo_registrar_saida())
                   
        # Configura os botões para expandirem e preencherem o espaço disponível
        self.frame_lateral.grid_rowconfigure(0, weight=0)
        self.frame_lateral.grid_rowconfigure(1, weight=0)
        self.frame_lateral.grid_columnconfigure(0, weight=1)

    def abrir_dialogo_adicionar(self):
        DialogoAdicionarProduto(self.master, self.estoque, self)

    def pesquisar_produto(self):
        query = simpledialog.askstring("Pesquisar produto", "Nome do produto:")
        if query is not None and query.strip():
            produtos = self.estoque.consultar_produto(query)
            if produtos:
                self.mostrar_resultados(produtos)
            else:
                messagebox.showinfo("Pesquisar produto", "Nenhum produto encontrado para a pesquisa.")

    def mostrar_resultados(self, produtos):
        janela_resultados = tk.Toplevel(self.master)
        janela_resultados.title("Resultados da Pesquisa")
        janela_resultados.bind('<Escape>', lambda event: janela_resultados.destroy())     
        janela_resultados.focus_set()
        
        texto_resultados = scrolledtext.ScrolledText(janela_resultados, wrap=tk.WORD, font=('Arial', 12))
        texto_resultados.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        for id, nome, quantidade, preco_venda, caminho_imagem in produtos:
            texto_resultados.insert(tk.END, f"ID: {id}\nNome: {nome}\nQuantidade: {quantidade}\nPreço de Venda: {preco_venda}\nImagem: {caminho_imagem}\n\n")
        
        texto_resultados.config(state=tk.DISABLED)  # Desativa a edição do texto

    def abrir_dialogo_registrar_saida(self):
      DialogoRegistrarSaida(self.master, self.estoque, self)

    def exibir_atualizacoes_estoque(self):
        self.texto_atualizacoes.config(state='normal')
        self.texto_atualizacoes.delete('1.0', tk.END) 
        movimentacoes = self.estoque.buscar_movimentacoes_recentes()
        for mov in movimentacoes:
            self.texto_atualizacoes.insert(tk.END, f"Produto ID: {mov[1]}, Tipo: {mov[2]}, Quantidade: {mov[3]}, Data e Hora: {mov[4]}\n")
            
              # Desabilita a edição da área de texto após a atualização
        self.texto_atualizacoes.config(state='disabled')
        self.botao_atualizacoes.config(text="Fechar Atualizações do Estoque")  
    
    def atualizar_area_atualizacoes(self):
        # Verifica se a área de atualizações está visível antes de atualizar
        if self.texto_atualizacoes.winfo_ismapped():
            self.exibir_atualizacoes_estoque()

    def toggle_atualizacoes_estoque(self):
        if self.texto_atualizacoes.winfo_ismapped():
            self.texto_atualizacoes.grid_remove()
            self.botao_atualizacoes.config(text="Exibir Atualizações do Estoque")
        else:
            self.texto_atualizacoes.grid()
            self.botao_atualizacoes.config(text="Fechar Atualizações do Estoque")
            # Aqui você pode adicionar o código para atualizar o texto com as últimas atualizações do estoque
            self.exibir_atualizacoes_estoque()

class DialogoRegistrarSaida(tk.Toplevel):
    def __init__(self, parent, estoque, app_parent):
        super().__init__(parent)
        self.estoque = estoque
        self.parent = app_parent
        self.title("Registrar Saída de Produto")
        self.bind('<Escape>', lambda event: self.destroy())
        self.geometry('600x400') # Define o tamanho da janela

        tk.Label(self, text="Nome do produto:").grid(row=0, column=0)
        self.entrada_nome_produto = tk.Entry(self)
        self.entrada_nome_produto.grid(row=0, column=1)
        self.entrada_nome_produto.focus_set()
        self.entrada_nome_produto.bind('<Return>', lambda event: self.buscar_produto())
        tk.Button(self, text="Buscar", command=self.buscar_produto).grid(row=0, column=2)
    
    def buscar_produto(self):
        nome_produto = self.entrada_nome_produto.get()
        produtos_encontrados = self.estoque.buscar_produtos_por_nome(nome_produto)
        if produtos_encontrados:
            self.mostrar_produtos_encontrados(produtos_encontrados)
        else:
            messagebox.showinfo("Informação", "Nenhum produto encontrado.")


    def mostrar_produtos_encontrados(self, produtos):
        # Cria uma nova janela para mostrar os produtos encontrados
        janela_selecao = tk.Toplevel(self)
        janela_selecao.title("Selecionar Produto")
        janela_selecao.geometry('800x600')
        janela_selecao.bind('<Escape>', lambda event: janela_selecao.destroy())

        lista_produtos = tk.Listbox(janela_selecao)
        lista_produtos.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        lista_produtos.bind('<Return>', lambda event: self.selecionar_produto(lista_produtos, janela_selecao))

        lista_produtos.focus_set()

        for produto in produtos:
            lista_produtos.insert(tk.END, f"ID: {produto[0]} - Nome: {produto[1]} - Quantidade: {produto[2]}")

        tk.Button(janela_selecao, text="Selecionar", command=lambda: self.selecionar_produto(lista_produtos, janela_selecao)).pack()

    def selecionar_produto(self, lista_produtos, janela_selecao):
        selecionado = lista_produtos.curselection()
        if selecionado:
            produto_id = lista_produtos.get(selecionado).split(" - ")[0].replace("ID: ", "")
            self.abrir_dialogo_quantidade_saida(produto_id, janela_selecao)
        else:
            messagebox.showinfo("Informação", "Por favor, selecione um produto.")

    def abrir_dialogo_quantidade_saida(self, produto_id, janela_selecao):
        # Cria uma janela de diálogo para inserir a quantidade de saída
        janela_quantidade = tk.Toplevel(janela_selecao)
        janela_quantidade.title("Quantidade de Saída")
        janela_quantidade.geometry('300x200')
        janela_quantidade.bind('<Return>', lambda event: self.confirmar_saida(produto_id, quantidade_saida_var.get(), janela_quantidade))
        self.bind('<Escape>', lambda event: self.destroy())

        tk.Label(janela_quantidade, text="Quantidade de saída:").grid(row=0, column=0)
        quantidade_saida_var = tk.StringVar()
        entrada_quantidade_saida = tk.Entry(janela_quantidade, textvariable=quantidade_saida_var)
        entrada_quantidade_saida.grid(row=0, column=1)
        entrada_quantidade_saida.focus_set() 

        # Vincula a tecla Enter ao método confirmar_saida
        entrada_quantidade_saida.bind('<Return>', lambda event: self.confirmar_saida(produto_id, quantidade_saida_var.get(), janela_quantidade))
        tk.Button(janela_quantidade, text="Confirmar", command=lambda: self.confirmar_saida(produto_id, quantidade_saida_var.get(), janela_quantidade)).grid(row=1, column=0, columnspan=2)
    
    def confirmar_saida(self, produto_id, quantidade_saida_str, janela_saida, event=None):
      try:
        # Converte a string de quantidade para um inteiro
        quantidade_saida = int(quantidade_saida_str)
      except ValueError:
        # Se a conversão falhar, mostra uma mensagem de erro e retorna
        messagebox.showerror("Erro", "Por favor, insira um número válido.", parent=janela_saida)
        return

      print(f"Confirmando saída: Produto ID {produto_id}, Quantidade {quantidade_saida}")  # Para depuração

      if quantidade_saida > 0:
          try:
            self.estoque.registrar_saida(produto_id, quantidade_saida)
            messagebox.showinfo("Sucesso", "Saída de produto registrada com sucesso!", parent=janela_saida)
            janela_saida.destroy()
            self.parent.atualizar_area_atualizacoes()
          except ValueError as e:
            messagebox.showerror("Erro", str(e), parent=janela_saida)
          except Exception as e:
            messagebox.showerror("Erro", f"Um erro inesperado ocorreu: {e}", parent=janela_saida)
      else:
        messagebox.showerror("Erro", "A quantidade de saída deve ser maior que zero.", parent=janela_saida)

if __name__ == "__main__":
    janela = tk.Tk()
    app = Aplicativo(janela)
    janela.mainloop()