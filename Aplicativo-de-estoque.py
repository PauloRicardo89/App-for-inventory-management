import os
import sqlite3
import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, scrolledtext, font

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
# Criação da tabela de configurações, se ela não existir
cursor.execute('''
CREATE TABLE IF NOT EXISTS configuracoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave TEXT NOT NULL,
    valor INTEGER NOT NULL
)
''')
conexao.commit()
# Função para centralizar a janela
def centralizar_janela(janela):
    janela.update_idletasks() 
    largura = janela.winfo_width()
    altura = janela.winfo_height()
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f'+{x}+{y}')

def formatar_preco_para_float(valor):
        # Remove pontos dos milhares
        valor_sem_pontos = valor.replace('.', '')
        # Substitui vírgula por ponto para a conversão em float
        valor_formatado = valor_sem_pontos.replace(',', '.')
        return float(valor_formatado)

def formatar_valor_para_exibicao(valor):
    # Formata o valor para incluir dois decimais, vírgula para decimais e ponto para milhares
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')    

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
    
    def buscar_todos_os_produtos(self):
        self.cursor.execute('''
            SELECT id, nome, quantidade FROM produtos
        ''')
        return self.cursor.fetchall()
    
    def buscar_nome_produto_por_id(self, produto_id):
        self.cursor.execute("SELECT nome FROM produtos WHERE id = ?", (produto_id,))
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado else "Nome não encontrado"
    
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

    def definir_limite_alerta(self, limite):
        # Verifica se já existe um limite de alerta configurado
        self.cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'limite_alerta'")
        resultado = self.cursor.fetchone()
        
        if resultado:
            # Se já existe, atualiza o valor
            self.cursor.execute("UPDATE configuracoes SET valor = ? WHERE chave = 'limite_alerta'", (limite,))
        else:
            # Se não existe, insere um novo registro
            self.cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES ('limite_alerta', ?)", (limite,))
        
        self.conexao.commit() 

    def buscar_limite_alerta(self):
        # Implementa a lógica para buscar o limite de alerta no banco de dados
        cursor = self.conexao.cursor()
        cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'limite_alerta'")
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None 

    def buscar_quantidade_atual_por_id(self, produto_id):
        # Implementa a lógica para buscar a quantidade atual do produto no banco de dados
        cursor = self.conexao.cursor()
        cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto_id,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0      

    def apagar_produto(self, produto_id):
        # Primeiro, apaga as movimentações relacionadas ao produto
        self.cursor.execute("DELETE FROM movimentacoes WHERE produto_id = ?", (produto_id,))
        # Depois, apaga o produto
        self.cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
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
            preco_venda = formatar_preco_para_float(self.preco_venda.get())
            caminho_imagem=self.caminho_imagem.get()

            # Adicionar ou atualizar o produto no estoque
            self.estoque.adicionar_ou_atualizar_produto(nome, quantidade, preco_venda, caminho_imagem)
            messagebox.showinfo("Sucesso", "Produto adicionado com sucesso!")
            
            # Limpa os campos para nova entrada
            self.limpar_campos()
            self.parent.atualizar_area_atualizacoes()
        except ValueError as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao adicionar o produto: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Um erro inesperado ocorreu: {e}")

    def limpar_campos(self):
        # Limpa os campos de entrada
        self.nome.set('')
        self.quantidade.set('')
        self.preco_venda.set('')
        self.caminho_imagem.set('')
        self.entrada_nome_produto.focus_set()
    
class Aplicativo:
    def __init__(self, master):
        self.master = master
        self.master.title("Aplicativo de Estoque")
        self.estoque = Estoque()

        # Maximiza a janela ao abrir
        self.master.state('zoomed')
        # Obtém a largura e altura da tela do usuário
        largura_tela = self.master.winfo_screenwidth()
        altura_tela = self.master.winfo_screenheight()
       
        # Define o tamanho mínimo da janela com base na resolução da tela
        largura_minima = min(800, largura_tela)
        altura_minima = min(600, altura_tela)
        self.master.minsize(largura_minima, altura_minima)
        
        # Configura o gerenciador de layout grid para a janela principal
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=7, uniform="grupo")  # 70% para o conteúdo principal
        self.master.grid_columnconfigure(1, weight=3, uniform="grupo")  # 30% para a faixa lateral

        # Cria um frame para o conteúdo principal com cor cinza claro
        self.frame_principal = tk.Frame(master, bg='lightgrey')
        self.frame_principal.grid(row=0, column=0, sticky='nsew')
        
        # fonte para os botões
        fonte_botao = font.Font(family='Helvetica', size=12, weight='bold')

        # Botão para exibir/fechar atualizações do estoque
        self.botao_atualizacoes = tk.Button(self.frame_principal, text="Exibir Atualizações do Estoque", bg='blue', fg='white', font=fonte_botao, command=self.toggle_atualizacoes_estoque, highlightthickness=4, bd=4)
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
        
        # Configura os botões para expandirem e preencherem o espaço disponível
        self.frame_lateral.grid_rowconfigure(0, weight=0)
        self.frame_lateral.grid_rowconfigure(1, weight=0)
        self.frame_lateral.grid_rowconfigure(2, weight=0)
        self.frame_lateral.grid_rowconfigure(3, weight=0)
        self.frame_lateral.grid_rowconfigure(4, weight=0) 
        self.frame_lateral.grid_columnconfigure(0, weight=1)

        # botão para adicionar Produto
        self.botao_adicionar = tk.Button(self.frame_lateral, text="Adicionar Produto", bg='green', fg='white',font=fonte_botao, command=self.abrir_dialogo_adicionar)
        self.botao_adicionar.grid(row=0, column=0, sticky='ew', padx=30, pady=20, ipady=10)
        self.botao_adicionar.bind('<Return>', lambda event: self.abrir_dialogo_adicionar())

        # botão para Pesquisar produto
        self.botao_pesquisar = tk.Button(self.frame_lateral, text="Pesquisar Produto", bg='#f0f0f0', fg='black', font=fonte_botao, command=self.pesquisar_produto)
        self.botao_pesquisar.grid(row=1, column=0, sticky='ew', padx=30, pady=10, ipady=10)
        self.botao_pesquisar.bind('<Return>', lambda event: self.pesquisar_produto())
        
        # Botão para configurar alerta de estoque baixo
        self.botao_configurar_alerta = tk.Button(self.frame_lateral, text="Alerta de Estoque Baixo", bg='yellow', fg='black', font=fonte_botao, command=self.configurar_alerta_estoque)
        self.botao_configurar_alerta.grid(row=2, column=0, sticky='ew', padx=30, pady= (120,30), ipady=10)
        self.botao_configurar_alerta.bind('<Return>', lambda event: self.configurar_alerta_estoque())

        # Botão Apagar Produto
        self.botao_apagar = tk.Button(self.frame_lateral, text="Apagar Produto", bg='#5b5b58', fg='white', font=fonte_botao, command=self.abrir_dialogo_apagar)
        self.botao_apagar.grid(row=3, column=0, sticky='ew', padx=30, pady=0, ipady=10, ipadx=10)
        self.botao_apagar.bind('<Return>', lambda event: self.abrir_dialogo_apagar())

       # Adiciona o botão 'Registrar Saída' ao frame lateral
        self.botao_registrar_saida = tk.Button(self.frame_lateral, text="Registrar Saída", bg='red', fg='white', font=fonte_botao, command=self.abrir_dialogo_registrar_saida,highlightthickness=5, bd=5)
        self.botao_registrar_saida.grid(row=4, column=0, sticky='ew', padx=30, pady=(120,30), ipady=12)
        self.botao_registrar_saida.bind('<Return>', lambda event: self.abrir_dialogo_registrar_saida())
     
    def abrir_dialogo_adicionar(self):
        dialogo = DialogoAdicionarProduto(self.master, self.estoque, self)
        centralizar_janela(dialogo)  # Chama a função para centralizar e ajustar o tamanho
        
    def salvar_limite_alerta(self, valor, janela_alerta):
        try:
            valor_int = int(valor) 
            # Implementa a lógica para salvar o valor no banco de dados
            self.estoque.definir_limite_alerta(valor_int)
            messagebox.showinfo("Sucesso", "Alerta de estoque baixo configurado para: " + str(valor_int), parent=janela_alerta)
            janela_alerta.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um número válido.", parent=janela_alerta)    

    def configurar_alerta_estoque(self):
    # Cria uma janela de diálogo para inserir a quantidade mínima de estoque
        janela_alerta = tk.Toplevel(self.master)
        janela_alerta.title("Configurar Alerta de Estoque Baixo")
        janela_alerta.geometry('220x140')
        centralizar_janela(janela_alerta)
        janela_alerta.grab_set()  # Torna a janela modal em relação à janela pai
        janela_alerta.bind('<Escape>', lambda event: janela_alerta.destroy())
        janela_alerta.focus_set()

        tk.Label(janela_alerta, text="Defina a quantidade mínima de estoque:").grid(row=0, column=0, columnspan=2, pady=10)

    # Cria um Spinbox para selecionar a quantidade
        spinbox_valor = tk.Spinbox(janela_alerta, from_=0, to=1000, increment=1, wrap=True)
        spinbox_valor.grid(row=1, column=0, columnspan=2, pady=10)

    # Botão para salvar a configuração
        botao_salvar = tk.Button(janela_alerta, text="Salvar", command=lambda: self.salvar_limite_alerta(spinbox_valor.get(), janela_alerta))
        botao_salvar.grid(row=2, column=0, columnspan=2, pady=10)
        botao_salvar.bind('<Return>', lambda event: self.salvar_limite_alerta(spinbox_valor.get(), janela_alerta))

    def pesquisar_produto(self):
        query = simpledialog.askstring("Pesquisar produto", "Digite o nome ou ID do produto:")
        if query is not None and query.strip():
        # Verifica se a consulta é um número (ID)
            if query.isdigit():
                produto_id = int(query)
                produto = self.estoque.buscar_nome_produto_por_id(produto_id)
                if produto != "Nome não encontrado":
                    produtos = self.estoque.consultar_produto(produto)
                    self.mostrar_resultados(produtos)
                else:
                    messagebox.showinfo("Pesquisar produto", "Nenhum produto encontrado para a pesquisa.")
            else:
                 # Assume que a consulta é um nome
                produtos = self.estoque.consultar_produto(query)
                if produtos:
                    self.mostrar_resultados(produtos)
                else:
                    messagebox.showinfo("Pesquisar produto", "Nenhum produto encontrado para a pesquisa.")
        elif query is None:
            pass  # Não faz nada se a caixa de diálogo for fechada sem entrada
    
    def mostrar_resultados(self, produtos):
        janela_resultados = tk.Toplevel(self.master)
        janela_resultados.title("Resultados da Pesquisa")
        janela_resultados.bind('<Escape>', lambda event: janela_resultados.destroy())     
        janela_resultados.focus_set()
        
        texto_resultados = scrolledtext.ScrolledText(janela_resultados, wrap=tk.WORD, font=('Arial', 16))
        texto_resultados.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        for id, nome, quantidade, preco_venda, caminho_imagem in produtos:
            preco_formatado = formatar_valor_para_exibicao(preco_venda)
            texto_resultados.insert(tk.END, f"ID: {id}\nNome: {nome}\nQuantidade: {quantidade}\nPreço de Venda: {preco_formatado}\nImagem: {caminho_imagem}\n\n")
        
        texto_resultados.config(state=tk.DISABLED)  # Desativa a edição do texto

    def abrir_dialogo_registrar_saida(self):
      DialogoRegistrarSaida(self.master, self.estoque, self)

    def exibir_atualizacoes_estoque(self):
        self.texto_atualizacoes.config(state='normal')
        self.texto_atualizacoes.delete('1.0', tk.END)
        
        # Define as tags para as cores
        self.texto_atualizacoes.tag_config('saida', foreground='red')
        self.texto_atualizacoes.tag_config('entrada', foreground='green')
        self.texto_atualizacoes.tag_config('alerta', foreground='red', background='yellow') 
        
        # Busca o limite de alerta de estoque baixo do banco de dados
        limite_alerta = self.estoque.buscar_limite_alerta()
        todos_os_produtos = self.estoque.buscar_todos_os_produtos()
        alertas_estoque_baixo = []

        # Verifica todos os produtos para identificar alertas de estoque baixo
        for produto in todos_os_produtos:
            produto_id, nome_produto, quantidade_atual = produto
            if quantidade_atual <= limite_alerta:
                alertas_estoque_baixo.append(f"Alerta de Estoque Baixo: {nome_produto}, Quantidade Atual: {quantidade_atual}\n")

        # Insere os alertas de estoque baixo no topo da área de texto
        for alerta in alertas_estoque_baixo:
            self.texto_atualizacoes.insert('1.0', alerta, 'alerta')

        movimentacoes = self.estoque.buscar_movimentacoes_recentes()
        for mov in movimentacoes:
            nome_produto = self.estoque.buscar_nome_produto_por_id(mov[1])
            tipo_movimentacao = "Saída" if mov[2].lower() == "saida" else "Entrada"
            data_hora_formatada = datetime.datetime.strptime(mov[4], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y : %H:%M')
            quantidade_atual = self.estoque.buscar_quantidade_atual_por_id(mov[1])
            self.texto_atualizacoes.insert(tk.END, f"{tipo_movimentacao}, ", 'saida' if tipo_movimentacao == "Saída" else 'entrada')
            self.texto_atualizacoes.insert(tk.END, f"ID: {mov[1]},Nome: {nome_produto}, Quantidade: {mov[3]}, Data e Hora: {data_hora_formatada}\n")
        
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
            # atualiza o texto com as últimas atualizações do estoque
            self.exibir_atualizacoes_estoque()
    
    def mostrar_janela_selecao_para_apagar(self, produtos, nome_produto):
        janela_selecao = tk.Toplevel(self.master)
        janela_selecao.title("Selecionar Produto para Apagar")
        janela_selecao.geometry('800x600')
        minha_fonte = font.Font(family='Helvetica', size=16, weight='bold')

        janela_selecao.grid_rowconfigure(0, weight=1)
        janela_selecao.grid_columnconfigure(0, weight=1)

        self.lista_produtos = tk.Listbox(janela_selecao, font=minha_fonte)
        self.lista_produtos.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        for produto in produtos:
            self.lista_produtos.insert(tk.END, f"ID: {produto[0]} - Nome: {produto[1]} - Quantidade: {produto[2]}")
           
        # Botão Selecionar
        botao_selecionar = tk.Button(janela_selecao, text="Selecionar", command=lambda: self.confirmar_e_apagar_produto(self.lista_produtos, janela_selecao, nome_produto))
        botao_selecionar.grid(row=1, column=0, pady=5)
        
        self.lista_produtos.bind('<Return>', lambda event: self.confirmar_e_apagar_produto(self.lista_produtos, janela_selecao, nome_produto))
        janela_selecao.bind('<Escape>', lambda event: janela_selecao.destroy())
        self.lista_produtos.focus_set()

    def abrir_dialogo_apagar(self):
        nome_produto = simpledialog.askstring("Apagar Produto", "Digite o nome do produto a ser apagado:")
        if nome_produto is None:
            return
        produtos_encontrados = []
        if nome_produto:
            produtos_encontrados = self.estoque.buscar_produtos_por_nome(nome_produto)
        if produtos_encontrados:
            self.mostrar_janela_selecao_para_apagar(produtos_encontrados, nome_produto)
        else:
            messagebox.showinfo("Informação", "Nenhum produto encontrado com esse nome.")
    
    def exibir_lista_produtos(self, nome_produto):
        produtos_encontrados = self.estoque.buscar_produtos_por_nome(nome_produto)
        if produtos_encontrados:
            self.lista_produtos.delete(0, tk.END)
            # Insere os produtos atualizados na lista
            for produto in produtos_encontrados:
                self.lista_produtos.insert(tk.END, f"ID: {produto[0]} - Nome: {produto[1]} - Quantidade: {produto[2]}")
        else:
            messagebox.showinfo("Informação", "Nenhum produto encontrado com esse nome.")

    def mostrar_janela_selecao(self, produtos, nome_produto):
        janela_selecao = tk.Toplevel(self.master)
        janela_selecao.title("Selecionar Produto para Apagar")
        janela_selecao.geometry('800x600')

    # Configura o gerenciador de layout grid para a nova janela
        janela_selecao.grid_rowconfigure(0, weight=1)
        janela_selecao.grid_columnconfigure(0, weight=1)

        lista_produtos = tk.Listbox(janela_selecao)
        lista_produtos.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        for produto in produtos:
            lista_produtos.insert(tk.END, f"ID: {produto[0]} - Nome: {produto[1]} - Quantidade: {produto[2]}")
        
        # Vincula a tecla Enter à função de confirmação de apagar produto
        lista_produtos.bind('<Return>', lambda event: self.confirmar_e_apagar_produto(lista_produtos, janela_selecao, nome_produto))

    # Permite a navegação pela lista usando as setas do teclado
        lista_produtos.bind('<Up>', lambda event: "break")  
        lista_produtos.bind('<Down>', lambda event: "break") 

    # Adiciona uma barra de rolagem
        scrollbar = tk.Scrollbar(janela_selecao, orient='vertical', command=lista_produtos.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        lista_produtos['yscrollcommand'] = scrollbar.set
        lista_produtos.focus_set()

    def confirmar_e_apagar_produto(self, lista_produtos, janela_selecao, nome_produto, event=None):
        selecionado = lista_produtos.curselection()
        if selecionado:
            produto_id = lista_produtos.get(selecionado).split(" - ")[0].replace("ID: ", "")
            confirmacao = messagebox.askyesno("Confirmar", "Tem certeza que deseja apagar o produto selecionado?", parent=janela_selecao)
            if confirmacao:
                self.estoque.apagar_produto(produto_id)
                messagebox.showinfo("Sucesso", "Produto apagado com sucesso!", parent=janela_selecao)
                self.exibir_lista_produtos(nome_produto)
                self.exibir_atualizacoes_estoque()  
        else:
            messagebox.showinfo("Informação", "Por favor, selecione um produto para apagar.", parent=janela_selecao)
            janela_selecao.update_idletasks()
            janela_selecao.destroy()   

class DialogoRegistrarSaida(tk.Toplevel):
    def __init__(self, parent, estoque, app_parent):
        super().__init__(parent)
        self.estoque = estoque
        self.parent = app_parent
        self.title("Registrar Saída de Produto")
        self.bind('<Escape>', lambda event: self.destroy())
        self.geometry('300x100') 
        centralizar_janela(self)

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
        minha_fonte = font.Font(family='Helvetica', size=16, weight='bold')
        janela_selecao.bind('<Escape>', lambda event: janela_selecao.destroy())

        lista_produtos = tk.Listbox(janela_selecao, font=minha_fonte)
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