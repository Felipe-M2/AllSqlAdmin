import sys
import json
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
                            QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget, QHBoxLayout,
                            QListWidget, QDialog, QFormLayout, QDialogButtonBox, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from crypto import SimpleCrypto
from addFavorite import AddFavoriteDialog

class DatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Configuração inicial da janela principal
        self.setWindowTitle("AllSqlAdmin")
        self.setGeometry(100, 100, 800, 600)
        
        # Configuração de arquivos e diretórios
        self.files_dir = Path(os.getcwd()) / "files"
        self.files_dir.mkdir(exist_ok=True)
        self.favorites_file = self.files_dir / "db_gui_favorites.json"
        
        # Inicialização de variáveis
        self.favorites = []
        self.crypto = SimpleCrypto()
        self.bd_list = ["PostgreSQL", "SQL Server", "MySQL"]
        self.engine = None
        self.current_db_type = None
        
        # Carrega favoritos e inicializa UI
        self.load_favorites()
        self.init_ui()
        self.update_favorites_list()

    #######################################################################
    # SEÇÃO: CONFIGURAÇÃO DA INTERFACE PRINCIPAL
    #######################################################################
    
    def init_ui(self):
        """Inicializa toda a interface gráfica"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Cria as abas principais
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Configura cada uma das abas
        self.setup_connection_tab()    # Aba de conexão com o banco
        self.setup_query_tab()        # Aba para execução de queries
        self.setup_explorer_tab()     # Aba para explorar tabelas
        self.setup_favorites_tab()    # Aba de favoritos

    #######################################################################
    # SEÇÃO: ABA DE CONEXÃO
    #######################################################################
    
    def setup_connection_tab(self):
        """Configura a aba de conexão com o banco de dados"""
        connection_tab = QWidget()
        layout = QVBoxLayout(connection_tab)
        
        # Dropdown para seleção do tipo de banco
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(self.bd_list)
        layout.addWidget(QLabel("Tipo de Banco de Dados:"))
        layout.addWidget(self.db_type_combo)
        
        # Campos de entrada para parâmetros de conexão
        self.host_input = QLineEdit(placeholderText="host (ex: localhost)")
        self.port_input = QLineEdit(placeholderText="porta (ex: 5432, 1433, 3306)")
        self.db_name_input = QLineEdit(placeholderText="nome do banco de dados")
        self.username_input = QLineEdit(placeholderText="usuário")
        self.password_input = QLineEdit(placeholderText="senha")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Adiciona os campos ao layout
        connection_fields = [
            ("Host:", self.host_input),
            ("Porta:", self.port_input),
            ("Nome do Banco:", self.db_name_input),
            ("Usuário:", self.username_input),
            ("Senha:", self.password_input)
        ]
        
        for label, field in connection_fields:
            layout.addWidget(QLabel(label))
            layout.addWidget(field)
        
        # Botão de conexão e status
        connect_btn = QPushButton("Conectar")
        connect_btn.clicked.connect(self.connect_to_db)
        layout.addWidget(connect_btn)
        
        self.connection_status = QLabel("Não conectado")
        layout.addWidget(self.connection_status)
        
        self.tabs.addTab(connection_tab, "Conexão")

    def connect_to_db(self):
        """Estabelece conexão com o banco de dados"""
        # Obtém os parâmetros da interface
        db_type = self.db_type_combo.currentText()
        host = self.host_input.text()
        port = self.port_input.text()
        db_name = self.db_name_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        
        try:
            # Cria a string de conexão de acordo com o tipo de banco
            if db_type == "PostgreSQL":
                connection_string = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{db_name}"
            elif db_type == "SQL Server":
                connection_string = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"
            elif db_type == "MySQL":
                connection_string = f'mysql+pymysql://{username}:{password}@{host}:{port}/{db_name}'
            
            # Tenta estabelecer a conexão
            self.engine = create_engine(connection_string)
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))  # Testa a conexão
                
            # Atualiza a interface com o status da conexão
            self.current_db_type = db_type
            self.connection_status.setText(f"Conectado a {db_type} - {db_name}")
            self.connection_status.setStyleSheet("color: green;")
            
            # Habilita as abas que dependem da conexão
            self.tabs.setTabEnabled(1, True)  # Aba de consulta
            self.tabs.setTabEnabled(2, True)  # Aba de exploração
            
            # Carrega a lista de tabelas
            self.load_tables_list()
            
        except SQLAlchemyError as e:
            # Exibe mensagens de erro em caso de falha
            self.connection_status.setText(f"Erro de conexão: {str(e)}")
            self.connection_status.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível conectar ao banco de dados:\n{str(e)}")

    #######################################################################
    # SEÇÃO: ABA DE CONSULTA SQL
    #######################################################################
    
    def setup_query_tab(self):
        """Configura a aba para execução de consultas SQL"""
        query_tab = QWidget()
        layout = QVBoxLayout(query_tab)
        
        # Editor de texto para escrever queries
        self.sql_editor = QTextEdit(placeholderText="Digite sua consulta SQL aqui...")
        layout.addWidget(self.sql_editor)
        
        # Botão para executar a consulta
        execute_btn = QPushButton("Executar Consulta")
        execute_btn.clicked.connect(self.execute_query)
        layout.addWidget(execute_btn)
        
        # Tabela para exibir resultados
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)
        
        # Label para status da consulta
        self.query_status = QLabel("")
        layout.addWidget(self.query_status)
        
        self.tabs.addTab(query_tab, "Consulta SQL")
        self.tabs.setTabEnabled(1, False)  # Inicialmente desabilitada

    def execute_query(self):
        """Executa a consulta SQL e exibe os resultados"""
        # Verifica se há uma conexão ativa
        if not self.engine:
            QMessageBox.warning(self, "Aviso", "Conecte-se a um banco de dados primeiro!")
            return
        
        query = self.sql_editor.toPlainText().strip()
        
        # Verifica se o usuário digitou algo
        if not query:
            QMessageBox.warning(self, "Aviso", "Digite uma consulta SQL!")
            return
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                # Processa resultados para consultas SELECT
                if query.lower().startswith("select"):
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    # Configura a tabela de resultados
                    self.results_table.setRowCount(len(rows))
                    self.results_table.setColumnCount(len(columns))
                    self.results_table.setHorizontalHeaderLabels(columns)
                    
                    # Preenche a tabela com os resultados
                    for row_idx, row in enumerate(rows):
                        for col_idx, col in enumerate(row):
                            self.results_table.setItem(row_idx, col_idx, QTableWidgetItem(str(col)))
                    
                    self.query_status.setText(f"{len(rows)} linhas retornadas")
                else:
                    # Para outros tipos de comando (INSERT, UPDATE, etc)
                    self.query_status.setText("Comando executado com sucesso")
                    
        except SQLAlchemyError as e:
            # Tratamento de erros na consulta
            self.query_status.setText(f"Erro na consulta: {str(e)}")
            QMessageBox.critical(self, "Erro na Consulta", f"Erro ao executar a consulta:\n{str(e)}")

    #######################################################################
    # SEÇÃO: ABA DE EXPLORAÇÃO DE TABELAS
    #######################################################################
    
    def setup_explorer_tab(self):
        """Configura a aba para explorar tabelas do banco"""
        explorer_tab = QWidget()
        layout = QVBoxLayout(explorer_tab)
        
        # Layout superior com combobox e botão de atualização
        top_layout = QHBoxLayout()
        
        self.tables_list = QComboBox()
        self.tables_list.currentTextChanged.connect(self.load_table_data)
        top_layout.addWidget(QLabel("Tabelas:"))
        top_layout.addWidget(self.tables_list, 1)  # Stretch factor 1
        
        refresh_btn = QPushButton("Atualizar")
        refresh_btn.clicked.connect(self.load_tables_list)
        top_layout.addWidget(refresh_btn)
        
        layout.addLayout(top_layout)
        
        # Tabela para exibir os dados
        self.table_data = QTableWidget()
        self.table_data.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table_data, 1)  # Stretch factor 1
        
        self.tabs.addTab(explorer_tab, "Explorar")
        self.tabs.setTabEnabled(2, False)  # Inicialmente desabilitada

    def load_tables_list(self):
        """Carrega a lista de tabelas do banco conectado"""
        if not self.engine:
            QMessageBox.warning(self, "Aviso", "Nenhuma conexão com banco de dados estabelecida")
            return
        
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            # Atualiza o combobox de tabelas
            self.tables_list.blockSignals(True)  # Evita eventos durante atualização
            self.tables_list.clear()
            
            if not tables:
                self.tables_list.addItem("Nenhuma tabela encontrada")
            else:
                self.tables_list.addItems(tables)
                if tables:
                    self.load_table_data(tables[0])  # Carrega dados da primeira tabela
            
            self.tables_list.blockSignals(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar tabelas:\n{str(e)}")
            self.tables_list.clear()
            self.tables_list.addItem("Erro ao carregar tabelas")

    def load_table_data(self, table_name):
        """Carrega os dados de uma tabela específica"""
        # Verifica se há uma tabela válida selecionada
        if (not table_name or not self.engine or 
            table_name in ["Nenhuma tabela encontrada", "Erro ao carregar tabelas"]):
            self.table_data.clear()
            self.table_data.setRowCount(0)
            self.table_data.setColumnCount(0)
            return
        
        try:
            with self.engine.connect() as conn:
                # Limita a 100 registros para demonstração
                query = text(f'SELECT * FROM "{table_name}" LIMIT 100')
                result = conn.execute(query)
                
                rows = result.fetchall()
                columns = result.keys()
                
                # Configura a tabela de visualização
                self.table_data.setRowCount(len(rows))
                self.table_data.setColumnCount(len(columns))
                self.table_data.setHorizontalHeaderLabels(columns)
                
                # Preenche a tabela com os dados
                for row_idx, row in enumerate(rows):
                    for col_idx, col in enumerate(row):
                        item = QTableWidgetItem(str(col) if col is not None else "NULL")
                        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)  # Torna não editável
                        self.table_data.setItem(row_idx, col_idx, item)
                
                # Ajusta o tamanho das colunas
                self.table_data.resizeColumnsToContents()
                
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados da tabela {table_name}:\n{str(e)}")
            self.table_data.clearContents()

    #######################################################################
    # SEÇÃO: ABA DE FAVORITOS
    #######################################################################
    
    def setup_favorites_tab(self):
        """Configura a aba de conexões favoritas"""
        favorites_tab = QWidget()
        layout = QVBoxLayout(favorites_tab)
        
        # Lista de favoritos
        self.favorites_list = QListWidget()
        self.favorites_list.itemDoubleClicked.connect(self.connect_to_favorite)
        layout.addWidget(self.favorites_list)
        
        # Configura o menu de contexto (botão direito)
        self.setup_favorites_context_menu()
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Adicionar Favorito")
        add_btn.clicked.connect(self.show_add_favorite_dialog)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remover Favorito")
        remove_btn.clicked.connect(self.remove_favorite)
        btn_layout.addWidget(remove_btn)
        
        layout.addLayout(btn_layout)
        
        self.tabs.addTab(favorites_tab, "Favoritos")
        self.update_favorites_list()

    def setup_favorites_context_menu(self):
        """Configura o menu de contexto para os favoritos"""
        self.favorites_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.favorites_list.customContextMenuRequested.connect(self.show_favorites_context_menu)

    def show_favorites_context_menu(self, position):
        """Exibe o menu de contexto para editar favoritos"""
        item = self.favorites_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu(self)
        
        # Ações do menu
        edit_action = QAction("Editar Favorito", self)
        edit_action.triggered.connect(lambda: self.edit_favorite(item))
        
        remove_action = QAction("Remover Favorito", self)
        remove_action.triggered.connect(lambda: self.remove_favorite_item(item))
        
        menu.addAction(edit_action)
        menu.addAction(remove_action)
        menu.exec(self.favorites_list.viewport().mapToGlobal(position))

    def update_favorites_list(self):
        """Atualiza a lista de favoritos na interface"""
        self.favorites_list.clear()
        for fav in self.favorites:
            self.favorites_list.addItem(f"{fav['name']} ({fav['db_type']} - {fav['host']}/{fav['db_name']})")

    def show_add_favorite_dialog(self):
        """Exibe diálogo para adicionar novo favorito"""
        dialog = AddFavoriteDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Valida campos obrigatórios
            if not all([dialog.name_input.text(), 
                       dialog.host_input.text(), 
                       dialog.port_input.text(), 
                       dialog.db_name_input.text()]):
                QMessageBox.warning(self, "Aviso", "Preencha todos os campos obrigatórios!")
                return
                
            # Cria novo favorito (com senha criptografada)
            favorite = {
                "name": dialog.name_input.text(),
                "db_type": dialog.db_type_combo.currentText(),
                "host": dialog.host_input.text(),
                "port": dialog.port_input.text(),
                "db_name": dialog.db_name_input.text(),
                "username": dialog.username_input.text(),
                "password": self.crypto.encrypt(dialog.password_input.text()) if dialog.password_input.text() else ""
            }
            self.add_favorite(favorite)

    def add_favorite(self, favorite):
        """Adiciona um novo favorito à lista"""
        self.favorites.append(favorite)
        self.save_favorites()
        self.update_favorites_list()

    def edit_favorite(self, item):
        """Edita um favorito existente"""
        index = self.favorites_list.row(item)
        favorite = self.favorites[index]
        
        dialog = AddFavoriteDialog(self)
        
        # Preenche o diálogo com os valores existentes
        dialog.name_input.setText(favorite.get("name", ""))
        dialog.db_type_combo.setCurrentText(favorite.get("db_type", ""))
        dialog.host_input.setText(favorite.get("host", ""))
        dialog.port_input.setText(favorite.get("port", ""))
        dialog.db_name_input.setText(favorite.get("db_name", ""))
        dialog.username_input.setText(favorite.get("username", ""))
        
        # Decriptografa a senha se existir
        if favorite.get("password"):
            try:
                decrypted = self.crypto.decrypt(favorite["password"])
                dialog.password_input.setText(decrypted)
            except:
                dialog.password_input.clear()
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Valida campos obrigatórios
            if not all([dialog.name_input.text(), 
                       dialog.host_input.text(), 
                       dialog.port_input.text(), 
                       dialog.db_name_input.text()]):
                QMessageBox.warning(self, "Aviso", "Preencha todos os campos obrigatórios!")
                return
                
            # Atualiza o favorito
            self.favorites[index] = {
                "name": dialog.name_input.text(),
                "db_type": dialog.db_type_combo.currentText(),
                "host": dialog.host_input.text(),
                "port": dialog.port_input.text(),
                "db_name": dialog.db_name_input.text(),
                "username": dialog.username_input.text(),
                "password": self.crypto.encrypt(dialog.password_input.text()) if dialog.password_input.text() else ""
            }
            
            self.save_favorites()
            self.update_favorites_list()

    def remove_favorite(self):
        """Remove o favorito selecionado"""
        selected = self.favorites_list.currentRow()
        if selected >= 0:
            self.favorites.pop(selected)
            self.save_favorites()
            self.update_favorites_list()

    def remove_favorite_item(self, item):
        """Remove um favorito específico (para menu de contexto)"""
        index = self.favorites_list.row(item)
        if index >= 0:
            self.favorites.pop(index)
            self.save_favorites()
            self.update_favorites_list()

    def connect_to_favorite(self, item):
        """Conecta usando os parâmetros de um favorito"""
        index = self.favorites_list.row(item)
        favorite = self.favorites[index]
        
        # Muda para a aba de conexão
        self.tabs.setCurrentIndex(0)
        
        # Preenche os campos de conexão
        self.db_type_combo.setCurrentText(favorite["db_type"])
        self.host_input.setText(favorite["host"])
        self.port_input.setText(favorite["port"])
        self.db_name_input.setText(favorite["db_name"])
        self.username_input.setText(favorite["username"])
        
        # Decriptografa a senha se existir
        if favorite.get("password"):
            try:
                decrypted = self.crypto.decrypt(favorite["password"])
                self.password_input.setText(decrypted)
            except:
                self.password_input.clear()
        else:
            self.password_input.clear()
        
        # Foca no campo de senha
        self.password_input.setFocus()

    #######################################################################
    # SEÇÃO: MANIPULAÇÃO DE ARQUIVOS
    #######################################################################
    
    def load_favorites(self):
        """Carrega a lista de favoritos do arquivo JSON"""
        try:
            if self.favorites_file.exists():
                with open(self.favorites_file, 'r') as f:
                    self.favorites = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar favoritos: {e}")

    def save_favorites(self):
        """Salva a lista de favoritos no arquivo JSON"""
        try:
            with open(self.favorites_file, 'w') as f:
                json.dump(self.favorites, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar favoritos: {e}")

#######################################################################
# EXECUÇÃO PRINCIPAL
#######################################################################

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec())