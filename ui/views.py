# ================= VIEWS =================

import flet as ft
from ui.components import AutocompleteFiled, ContainerRegistro, RankingWidget
from ui.styles import Estilos
from config import SENHA_PAINEL, SENHA_ADMIN
from services.cache_service import CacheService
from services.registro_service import RegistroService
from services.separacao_service import SeparacaoService
from services.ranking_service import RankingService
from firebase_manager import FirebaseManager


class CadastroView:
    """View de Cadastro"""

    def __init__(self, page, cache_service: CacheService):
        self.page = page
        self.cache = cache_service
        self.registro_service = RegistroService(cache_service)
        self.firebase = FirebaseManager()

        self.cad_controle = ft.TextField(label="Controle")
        self.cad_cliente = ft.TextField(label="Cliente")
        self.cad_conferente_field = AutocompleteFiled(
            "Conferente",
            self.cache.conferentes,
            self._select_conferente
        )
        self.cad_box_field = AutocompleteFiled(
            "Box",
            self.cache.boxes,
            self._select_box
        )
        self.cad_volume = ft.TextField(label="Volume")
        self.msg_cadastro = ft.Text()

    def _select_conferente(self, valor):
        """Callback ao selecionar conferente"""
        self.page.update()

    def _select_box(self, valor):
        """Callback ao selecionar box"""
        self.page.update()

    def _salvar(self, e):
        """Salva novo registro"""
        sucesso, msg = self.registro_service.salvar_registro(
            self.cad_controle.value,
            self.cad_cliente.value,
            self.cad_conferente_field.obter_valor(),
            self.cad_box_field.obter_valor(),
            self.cad_volume.value
        )

        self.msg_cadastro.value = msg
        self.msg_cadastro.color = "green" if sucesso else "red"

        if sucesso:
            self.cad_controle.value = ""
            self.cad_cliente.value = ""
            self.cad_volume.value = ""
            self.cad_conferente_field.limpar()
            self.cad_box_field.limpar()
            self.cache.carregar_registros()

        self.page.update()

    def obter_view(self):
        """Retorna a view"""
        return ft.Column([
            ft.Text("Cadastro", size=22, weight="bold"),
            self.cad_controle,
            self.cad_cliente,
            self.cad_conferente_field.obter_container(),
            self.cad_box_field.obter_container(),
            self.cad_volume,
            ft.ElevatedButton("Salvar", on_click=self._salvar),
            self.msg_cadastro
        ])


class SeparacaoView:
    """View de Separação - Contar apenas por NOTAS"""

    def __init__(self, page, cache_service: CacheService):
        self.page = page
        self.cache = cache_service
        self.separacao_service = SeparacaoService(cache_service)

        self.sep_separador_field = AutocompleteFiled(
            "Separador",
            self.cache.separadores,
            self._select_separador
        )
        self.sep_notas = ft.TextField(
            label="Notas",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        self.msg_sep = ft.Text()

    def _select_separador(self, valor):
        """Callback ao selecionar separador"""
        self.page.update()

    def _salvar(self, e):
        """Salva nova separação"""
        sucesso, msg = self.separacao_service.salvar_separacao(
            self.sep_separador_field.obter_valor(),
            self.sep_notas.value
        )

        self.msg_sep.value = msg
        self.msg_sep.color = "green" if sucesso else "red"

        if sucesso:
            self.sep_notas.value = ""
            self.sep_separador_field.limpar()

        self.page.update()

    def obter_view(self):
        """Retorna a view"""
        return ft.Column([
            ft.Text("Separação", size=22, weight="bold"),
            self.sep_separador_field.obter_container(),
            self.sep_notas,
            ft.ElevatedButton("Salvar Separação", on_click=self._salvar),
            self.msg_sep
        ])


class ConsultaView:
    """View de Consulta"""

    def __init__(self, page, cache_service: CacheService):
        self.page = page
        self.cache = cache_service
        self.firebase = FirebaseManager()

        self.busca = ft.TextField(label="Buscar")
        self.lista = ft.Column(scroll="auto")

        self.busca.on_change = self._filtrar
        self._atualizar_lista()

    def _filtrar(self, e=None):
        """Filtra registros"""
        termo = (self.busca.value or "").lower()
        self._atualizar_lista(termo)

    def _atualizar_lista(self, termo=""):
        """Atualiza lista de registros"""
        self.lista.controls.clear()

        registros = self.cache.filtrar_registros(termo)

        for d in registros:
            self.lista.controls.append(
                ContainerRegistro.criar(d, self.firebase)
            )

        self.page.update()

    def obter_view(self):
        """Retorna a view"""
        return ft.Column([
            ft.Text("Consulta", size=22, weight="bold"),
            self.busca,
            self.lista
        ])


class PainelView:
    """View do Painel de Produtividade"""

    def __init__(self, page):
        self.page = page
        self.ranking_service = RankingService()

        self.senha = ft.TextField(label="Senha Painel", password=True)
        self.cadeado = ft.Text(
            "🔒 Painel Trancado",
            color="red",
            size=18,
            weight="bold"
        )
        self.ranking_conf = ft.Column()
        self.ranking_sep = ft.Column()
        self.painel = ft.Container(visible=False)

        self._construir_painel()

    def _construir_painel(self):
        """Constrói o painel de produtividade"""
        self.painel.content = ft.Column([
            ft.Text("📊 Painel de Produtividade", size=24, weight="bold"),
            ft.Divider(),
            self.ranking_conf,
            ft.Divider(),
            self.ranking_sep,
            ft.Divider(),
            ft.ElevatedButton(
                "🔒 Trancar Painel",
                bgcolor="red",
                color="white",
                on_click=self._trancar
            )
        ])

    def _trancar(self, e=None):
        """Tranca o painel"""
        self.painel.visible = False
        self.cadeado.visible = True
        self.senha.value = ""
        self.page.update()

    def _abrir(self, e):
        """Abre o painel com senha"""
        if self.senha.value == SENHA_PAINEL:
            ranking_conf, inicio, fim = self.ranking_service.calcular_ranking_conferentes()
            ranking_sep, _, _ = self.ranking_service.calcular_ranking_separadores()

            self.ranking_conf.controls = [
                RankingWidget.criar_conferentes(
                    ranking_conf,
                    Estilos.CORES_CONFERENTES,
                    inicio,
                    fim
                ).controls[0]
            ]
            self.ranking_conf.controls.append(ft.Container(height=10))
            if ranking_conf:
                for i, (nome, total) in enumerate(ranking_conf, start=1):
                    from ui.styles import criar_card_ranking
                    self.ranking_conf.controls.append(
                        criar_card_ranking(i, nome, f"{total} registros", Estilos.CORES_CONFERENTES[i - 1])
                    )

            self.ranking_sep.controls = [
                RankingWidget.criar_separadores(
                    ranking_sep,
                    Estilos.CORES_SEPARADORES,
                    inicio,
                    fim
                ).controls[0]
            ]
            self.ranking_sep.controls.append(ft.Container(height=10))
            if ranking_sep:
                for i, (nome, total) in enumerate(ranking_sep, start=1):
                    from ui.styles import criar_card_ranking
                    self.ranking_sep.controls.append(
                        criar_card_ranking(i, nome, f"{total} notas", Estilos.CORES_SEPARADORES[i - 1])
                    )

            self.painel.visible = True
            self.cadeado.visible = False
        else:
            self.painel.visible = False
            self.cadeado.visible = True

        self.page.update()

    def obter_view(self):
        """Retorna a view"""
        return ft.Column([
            ft.Text("Painel", size=22, weight="bold"),
            self.senha,
            ft.ElevatedButton("Abrir Painel", on_click=self._abrir),
            self.cadeado,
            self.painel
        ])


class AdminView:
    """View de Administração"""

    def __init__(self, page, cache_service: CacheService):
        self.page = page
        self.cache = cache_service
        self.firebase = FirebaseManager()

        self.admin_senha = ft.TextField(label="Senha Admin", password=True)
        self.admin_msg = ft.Text()

        self.adm_conf = ft.TextField(label="Novo Conferente")
        self.adm_box = ft.TextField(label="Novo Box")
        self.adm_sep = ft.TextField(label="Novo Separador")

        self.admin_area = ft.Container(visible=False)
        self._construir_area_admin()

    def _construir_area_admin(self):
        """Constrói área administrativa"""
        self.admin_area.content = ft.Column([
            ft.Text("🔐 Área Administrativa", size=22, weight="bold"),
            self.adm_conf,
            ft.ElevatedButton("Salvar Conferente", on_click=self._salvar_conf),
            self.adm_box,
            ft.ElevatedButton("Salvar Box", on_click=self._salvar_box),
            self.adm_sep,
            ft.ElevatedButton("Salvar Separador", on_click=self._salvar_sep),
            ft.Divider(),
            ft.ElevatedButton(
                "🔐 Trancar Admin",
                bgcolor="#374151",
                color="white",
                on_click=self._trancar
            ),
            self.admin_msg
        ])

    def _entrar(self, e):
        """Valida senha e abre área admin"""
        if self.admin_senha.value == SENHA_ADMIN:
            self.admin_area.visible = True
            self.admin_msg.value = "Admin liberado!"
            self.admin_msg.color = "green"
        else:
            self.admin_area.visible = False
            self.admin_msg.value = "Senha incorreta!"
            self.admin_msg.color = "red"

        self.page.update()

    def _trancar(self, e):
        """Tranca a área admin"""
        self.admin_area.visible = False
        self.admin_senha.value = ""
        self.admin_msg.value = "Admin trancado!"
        self.admin_msg.color = "red"
        self.page.update()

    def _salvar_conf(self, e):
        """Salva novo conferente"""
        if self.adm_conf.value:
            if self.firebase.salvar_conferente(self.adm_conf.value):
                self.adm_conf.value = ""
                self.cache.carregar_conferentes()
                self.admin_msg.value = "Conferente salvo!"
                self.admin_msg.color = "green"
            else:
                self.admin_msg.value = "Erro ao salvar"
                self.admin_msg.color = "red"

        self.page.update()

    def _salvar_box(self, e):
        """Salva novo box"""
        if self.adm_box.value:
            if self.firebase.salvar_box(self.adm_box.value):
                self.adm_box.value = ""
                self.cache.carregar_boxes()
                self.admin_msg.value = "Box salvo!"
                self.admin_msg.color = "green"
            else:
                self.admin_msg.value = "Erro ao salvar"
                self.admin_msg.color = "red"

        self.page.update()

    def _salvar_sep(self, e):
        """Salva novo separador"""
        if self.adm_sep.value:
            if self.firebase.salvar_separador(self.adm_sep.value):
                self.adm_sep.value = ""
                self.cache.carregar_separadores()
                self.admin_msg.value = "Separador salvo!"
                self.admin_msg.color = "green"
            else:
                self.admin_msg.value = "Erro ao salvar"
                self.admin_msg.color = "red"

        self.page.update()

    def obter_view(self):
        """Retorna a view"""
        return ft.Column([
            ft.Text("Admin", size=22, weight="bold"),
            self.admin_senha,
            ft.ElevatedButton("Entrar", on_click=self._entrar),
            self.admin_area
        ])
