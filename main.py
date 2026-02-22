# gerador_codigos_final.py (Pydroid3 / Android) - SEM KV
# FIX DEFINITIVO: mensagem sempre legível (usa Label + ScrollView)
# GERAR cria mensagem, COPIAR copia, inputs visíveis, layout organizado

import json
import time
import hashlib
from pathlib import Path

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Rectangle

# ---------- LÓGICA ----------
HIST_FILE = Path("clientes.json")
CODE_STEP_SEC = 3 * 60

MONTHLY_SECRET  = "no_princípio_era_o_verbo_e_o_verbo_estava_com_ele_e_o_verbo_erra_Deus"
RECOVERY_SECRET = "Isabel_Tasso_Joaquina_António_Belmiro_Haleny_la_familia"


def load_hist():
    if HIST_FILE.exists():
        try:
            return json.loads(HIST_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_hist(d):
    HIST_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def slot(now=None):
    if now is None:
        now = int(time.time())
    return now // CODE_STEP_SEC

def make_6digits(secret: str, pc_id: str, slot_id: int, kind: str) -> str:
    pc_id = (pc_id or "").strip().upper()
    kind = (kind or "").strip().lower()
    msg = f"{secret}|{pc_id}|{slot_id}|{kind}".encode("utf-8", "ignore")
    h = hashlib.sha256(msg).digest()
    num = int.from_bytes(h[:8], "big") % 1_000_000
    return f"{num:06d}"

def build_client_message(nome: str, pc_id: str, code: str, tipo: str) -> str:
    tipo_txt = "MENSALIDADE (30 dias)" if tipo == "mensalidade" else "RECUPERACAO (reset nome)"
    return (
        f"Ola {nome}!\n\n"
        f"Aqui esta o seu codigo de {tipo_txt}:\n"
        f"CODIGO: {code}\n"
        f"ID: {pc_id}\n\n"
        f"Copie e cole no aplicativo para ativar.\n"
        f"ATENCAO: este codigo muda a cada 3 minutos. Se expirar, peca outro.\n"
    )

# ---------- UI HELPERS ----------
def bg_rect(widget, rgba):
    with widget.canvas.before:
        widget._bgc = Color(*rgba)
        widget._bgr = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(widget._bgr, "pos", widget.pos),
                size=lambda *_: setattr(widget._bgr, "size", widget.size))

def bg_round(widget, rgba, radius=12):
    with widget.canvas.before:
        widget._bgc = Color(*rgba)
        widget._bgr = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=lambda *_: setattr(widget._bgr, "pos", widget.pos),
                size=lambda *_: setattr(widget._bgr, "size", widget.size))

def center_text(lbl: Label):
    lbl.halign = "center"
    lbl.valign = "middle"
    lbl.bind(size=lambda *_: setattr(lbl, "text_size", lbl.size))

# ---------- WIDGETS ----------
class Header(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(2), padding=(dp(10), dp(10)),
                         size_hint_y=None, height=dp(86), **kwargs)
        bg_round(self, (0, 0, 0, 1), radius=14)

        t1 = Label(text="Gerador de Codigos", bold=True, font_size="22sp", color=(1, 1, 1, 1))
        center_text(t1)
        t2 = Label(text="Mensagem pronta + Copiar", font_size="14sp", color=(0.85, 0.85, 0.85, 1))
        center_text(t2)

        self.add_widget(t1)
        self.add_widget(t2)

class SectionBar(Label):
    def __init__(self, text, **kwargs):
        super().__init__(text=text, bold=True, font_size="18sp", color=(1, 1, 1, 1),
                         size_hint_y=None, height=dp(46), **kwargs)
        center_text(self)
        bg_round(self, (0.45, 0.45, 0.45, 1), radius=12)

class SoftInput(TextInput):
    def __init__(self, hint, **kwargs):
        super().__init__(**kwargs)
        self.hint_text = hint
        self.multiline = False
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = (dp(14), dp(14))

        self.background_normal = ""
        self.background_active = ""
        self.background_color = (1, 1, 1, 1)
        self.foreground_color = (0, 0, 0, 1)
        self.hint_text_color = (0.45, 0.45, 0.45, 1)
        self.cursor_color = (0, 0, 0, 1)

class AppButton(Button):
    def __init__(self, text, rgba, **kwargs):
        super().__init__(text=text, bold=True, color=(1, 1, 1, 1),
                         background_normal="", background_down="",
                         size_hint_y=None, height=dp(48), **kwargs)
        self.background_color = (0, 0, 0, 0)
        with self.canvas.before:
            self._c = Color(*rgba)
            self._r = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._r.pos = self.pos
        self._r.size = self.size


# ---------- APP ----------
class Root(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(10), **kwargs)
        bg_rect(self, (0.92, 0.92, 0.92, 1))
        self.hist = load_hist()
        self.current_message = ""  # <- mensagem para copiar

        sv = ScrollView()
        self.add_widget(sv)

        self.wrap = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        self.wrap.bind(minimum_height=self.wrap.setter("height"))
        sv.add_widget(self.wrap)

        self.wrap.add_widget(Header())
        self.wrap.add_widget(SectionBar("Dados do Cliente"))

        card = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(14), size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        bg_round(card, (0.97, 0.97, 0.97, 1), radius=14)

        self.nome_in = SoftInput("Nome do cliente (ex: Carlos)")
        self.pc_in = SoftInput("ID do PC (ex: ATB2C3D4ESF6)")
        self.nome_in.bind(text=self.on_name_change)

        # borda externa sem tapar texto
        box1 = BoxLayout(size_hint_y=None, height=self.nome_in.height, padding=(dp(2), dp(2)))
        bg_round(box1, (0.75, 0.75, 0.75, 1), radius=10)
        inner1 = BoxLayout()
        bg_round(inner1, (1, 1, 1, 1), radius=9)
        inner1.add_widget(self.nome_in)
        box1.add_widget(inner1)

        box2 = BoxLayout(size_hint_y=None, height=self.pc_in.height, padding=(dp(2), dp(2)))
        bg_round(box2, (0.75, 0.75, 0.75, 1), radius=10)
        inner2 = BoxLayout()
        bg_round(inner2, (1, 1, 1, 1), radius=9)
        inner2.add_widget(self.pc_in)
        box2.add_widget(inner2)

        card.add_widget(box1)
        card.add_widget(box2)

        row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(48))
        self.btn_gerar = AppButton("GERAR", (0.12, 0.33, 0.63, 1))
        self.btn_copiar = AppButton("COPIAR", (0.35, 0.35, 0.35, 1))
        self.btn_gerar.bind(on_press=self.on_generate)
        self.btn_copiar.bind(on_press=self.on_copy)
        row.add_widget(self.btn_gerar)
        row.add_widget(self.btn_copiar)
        card.add_widget(row)

        self.tipo_sp = Spinner(
            text="Recuperacao (reset nome)",
            values=("Mensalidade (30 dias)", "Recuperacao (reset nome)"),
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
        )
        with self.tipo_sp.canvas.before:
            self.tipo_sp._c = Color(0.35, 0.35, 0.35, 1)
            self.tipo_sp._r = RoundedRectangle(pos=self.tipo_sp.pos, size=self.tipo_sp.size, radius=[18])
        self.tipo_sp.bind(pos=self._upd_spinner, size=self._upd_spinner)
        card.add_widget(self.tipo_sp)

        self.wrap.add_widget(card)

        self.wrap.add_widget(SectionBar("Mensagem para o cliente"))

        # Caixa escura da mensagem (Label SEMPRE visível)
        msg_box = BoxLayout(size_hint_y=None, height=dp(420), padding=(dp(10), dp(10)))
        bg_round(msg_box, (0.35, 0.35, 0.35, 1), radius=12)

        self.msg_label = Label(
            text="Clique em GERAR para criar a mensagem...",
            color=(1, 1, 1, 1),
            font_size="16sp",
            halign="left",
            valign="top",
        )
        # text_size controla quebra de linha (wrap)
        self.msg_label.bind(size=self._upd_msg_label)

        # Scroll interno para mensagens grandes
        inner_sv = ScrollView()
        inner_sv.add_widget(self.msg_label)
        msg_box.add_widget(inner_sv)

        self.wrap.add_widget(msg_box)

    def _upd_msg_label(self, *_):
        # faz o texto quebrar dentro da caixa
        self.msg_label.text_size = (self.msg_label.width, None)

    def _upd_spinner(self, *_):
        self.tipo_sp._r.pos = self.tipo_sp.pos
        self.tipo_sp._r.size = self.tipo_sp.size

    def set_message(self, msg: str):
        self.current_message = msg
        self.msg_label.text = msg

    def on_name_change(self, *_):
        nome = (self.nome_in.text or "").strip()
        if not nome:
            return
        reg = self.hist.get(nome)
        if isinstance(reg, dict) and reg.get("pc_id"):
            if not (self.pc_in.text or "").strip():
                self.pc_in.text = reg["pc_id"]

    def on_generate(self, *_):
        nome = (self.nome_in.text or "").strip()
        pc_id = (self.pc_in.text or "").strip().upper()

        if not nome:
            self.set_message("Preencha o nome do cliente.")
            return
        if len(pc_id) < 6:
            self.set_message("ID invalido (muito curto).")
            return

        s = slot()
        if self.tipo_sp.text.startswith("Mensalidade"):
            code = make_6digits(MONTHLY_SECRET, pc_id, s, "monthly")
            tipo = "mensalidade"
        else:
            code = make_6digits(RECOVERY_SECRET, pc_id, s, "recovery")
            tipo = "recuperacao"

        msg = build_client_message(nome, pc_id, code, tipo)
        self.set_message(msg)

        self.hist[nome] = {"pc_id": pc_id, "ultimo_tipo": tipo, "gerado_em": int(time.time())}
        save_hist(self.hist)

    def on_copy(self, *_):
        if not self.current_message.strip():
            self.set_message("Clique em GERAR para criar a mensagem, depois COPIAR.")
            return
        Clipboard.copy(self.current_message)
        # feedback curto sem estragar o texto
        self.set_message(self.current_message + "\n\n[Copiado. Agora cole no WhatsApp.]")


class AppOrganizado(App):
    def build(self):
        Window.clearcolor = (0.92, 0.92, 0.92, 1)
        return Root()


if __name__ == "__main__":
    AppOrganizado().run()