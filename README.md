# Aplicativo de Estoque

## Descrição
Aplicativo de Estoque é uma aplicação desenvolvida em Python utilizando a biblioteca Tkinter para gerenciamento de inventário. Permite adicionar, remover e visualizar produtos, além de gerar relatórios.

## Funcionalidades
- Adicionar novos produtos ao estoque
- Remover produtos existentes
- Visualizar lista de produtos
- Gerar relatórios de estoque

## Instalação

1. Clone o repositório:
    ```bash
    git clone https://github.com/seu-usuario/Aplicativo-de-Estoque.git
    ```
2. Navegue até o diretório do projeto:
    ```bash
    cd Aplicativo-de-Estoque
    ```
3. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

## Gerar Executável

Para gerar um executável deste projeto, siga os passos abaixo:

1. **Instale o PyInstaller:**
    ```bash
    pip install pyinstaller
    ```
2. **Gere o Executável sem a Tela de Console:**
    ```bash
    pyinstaller --onefile --windowed Aplicativo-de-estoque.py
    ```
3. **Encontre o Executável:**
    O arquivo executável estará na pasta `dist`.

## Uso
Execute o aplicativo:
```bash
python Aplicativo-de-estoque.py

Contribuição
Sinta-se à vontade para contribuir realizando pull requests.

Licença
Este projeto está licenciado sob a licença MIT.