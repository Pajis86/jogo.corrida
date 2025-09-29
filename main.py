import random
import pygame
import os
import json
import math

pygame.init()

largura, altura = 400, 600
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("Nave vs Meteoros")
clock = pygame.time.Clock()

# Caminho das imagens
caminho_imagens = r"C:\Users\aluno\PyCharm\Cotacao-Kivy\corrida"

# == Sistema de Pontuação, tempo e níveis ===
fonte = pygame.font.Font(None, 36)
fonte_pequena = pygame.font.Font(None, 24)
fonte_grande = pygame.font.Font(None, 48)

# Variáveis globais inicializadas corretamente
pontuacao = 0
tempo_inicio = pygame.time.get_ticks()
tempo_atual = 0
nivel = 1
velocidade_base = 3
vida_jogador = 3
max_vida = 5
ultimo_boss_derrotado = 0  # CORREÇÃO 1: Variável definida

# Sistema de salvamento
ARQUIVO_SAVE = "save_game.json"


def salvar_jogo():
    dados = {
        "pontuacao": pontuacao,
        "nivel": nivel,
        "vida_jogador": vida_jogador,
        "naves_compradas": [nave["comprada"] for nave in loja.naves],
        "nave_selecionada": loja.nave_selecionada,
        "melhorias_compradas": [melhoria["comprada"] for melhoria in loja.melhorias],
        "ultimo_boss_derrotado": ultimo_boss_derrotado
    }
    try:
        with open(ARQUIVO_SAVE, 'w') as f:
            json.dump(dados, f)
        print("Jogo salvo com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar jogo: {e}")


def carregar_jogo():
    global pontuacao, nivel, vida_jogador, ultimo_boss_derrotado
    try:
        if os.path.exists(ARQUIVO_SAVE):
            with open(ARQUIVO_SAVE, 'r') as f:
                dados = json.load(f)

            pontuacao = dados.get("pontuacao", 0)
            nivel = dados.get("nivel", 1)
            vida_jogador = dados.get("vida_jogador", 3)
            ultimo_boss_derrotado = dados.get("ultimo_boss_derrotado", 0)  # CORREÇÃO 4: Valor padrão

            # Carregar naves compradas
            naves_compradas = dados.get("naves_compradas", [])
            for i, comprada in enumerate(naves_compradas):
                if i < len(loja.naves):
                    loja.naves[i]["comprada"] = comprada

            # Carregar nave selecionada
            loja.nave_selecionada = dados.get("nave_selecionada", 0)

            # Carregar melhorias compradas
            melhorias_compradas = dados.get("melhorias_compradas", [])
            for i, comprada in enumerate(melhorias_compradas):
                if i < len(loja.melhorias):
                    loja.melhorias[i]["comprada"] = comprada

            print("Jogo carregado com sucesso!")
            return True
    except Exception as e:
        print(f"Erro ao carregar jogo: {e}")
    return False


# Sistema de loja com efeitos reais
class Loja:
    def __init__(self):
        self.ativa = False
        self.nave_selecionada = 0
        self.secao_atual = "naves"
        self.rotacao_angulo = 0

        # Naves com estatísticas reais
        self.naves = [
            {"nome": "Nave Básica", "preco": 0, "comprada": True, "selecionada": True,
             "velocidade": 5, "dano": 1, "defesa": 3, "agilidade": 6, "bonus": 0,
             "tiro_duplo": False, "cor": (200, 200, 200)},

            {"nome": "Nave Azul-Roxa", "preco": 500, "comprada": False, "selecionada": False,
             "velocidade": 7, "dano": 2, "defesa": 3, "agilidade": 8, "bonus": 10,
             "tiro_duplo": True, "cor": (100, 100, 255)},

            {"nome": "Nave Verde", "preco": 700, "comprada": False, "selecionada": False,
             "velocidade": 6, "dano": 3, "defesa": 4, "agilidade": 7, "bonus": 15,
             "tiro_duplo": True, "cor": (100, 255, 100)},

            {"nome": "Nave Vermelha", "preco": 900, "comprada": False, "selecionada": False,
             "velocidade": 8, "dano": 4, "defesa": 5, "agilidade": 6, "bonus": 20,
             "tiro_duplo": True, "cor": (255, 100, 100)},

            {"nome": "Nave Dourada", "preco": 1200, "comprada": False, "selecionada": False,
             "velocidade": 9, "dano": 5, "defesa": 6, "agilidade": 9, "bonus": 25,
             "tiro_duplo": True, "cor": (255, 215, 0)}
        ]

        # Melhorias com efeitos reais
        self.melhorias = [
            {"nome": "+1 Vida", "preco": 300, "comprada": False, "tipo": "vida", "ativa": False},
            {"nome": "Velocidade+", "preco": 400, "comprada": False, "tipo": "velocidade", "ativa": False, "bonus": 2},
            {"nome": "Tiro Triplo", "preco": 600, "comprada": False, "tipo": "tiro", "ativa": False},
            {"nome": "Escudo Temporal", "preco": 450, "comprada": False, "tipo": "escudo", "ativa": False,
             "duracao": 10000},
            {"nome": "Imã de Itens", "preco": 350, "comprada": False, "tipo": "ima", "ativa": False, "raio": 100},
            {"nome": "Explosão Nuclear", "preco": 800, "comprada": False, "tipo": "explosao", "ativa": False,
             "usos": 3},
            {"nome": "Campo de Força", "preco": 550, "comprada": False, "tipo": "campo", "ativa": False,
             "duracao": 15000}
        ]

        # Tempo de ativação das melhorias
        self.tempo_escudo = 0
        self.tempo_campo = 0
        self.explosoes_restantes = 0

    def abrir_loja(self):
        self.ativa = True

    def fechar_loja(self):
        self.ativa = False

    def selecionar_nave(self, indice):
        if 0 <= indice < len(self.naves) and self.naves[indice]["comprada"]:
            # Desselecionar todas
            for nave in self.naves:
                nave["selecionada"] = False
            # Selecionar nova nave
            self.naves[indice]["selecionada"] = True
            self.nave_selecionada = indice
            aplicar_estatisticas_nave()
            salvar_jogo()

    def comprar_nave(self, pontuacao_atual):
        nave = self.naves[self.nave_selecionada]
        if not nave["comprada"] and pontuacao_atual >= nave["preco"]:
            nave["comprada"] = True
            nave["selecionada"] = True
            # Desselecionar outras
            for n in self.naves:
                if n != nave:
                    n["selecionada"] = False
            aplicar_estatisticas_nave()
            salvar_jogo()
            return pontuacao_atual - nave["preco"]
        return pontuacao_atual

    def comprar_melhoria(self, indice, pontuacao_atual):
        if 0 <= indice < len(self.melhorias):
            melhoria = self.melhorias[indice]
            if not melhoria["comprada"] and pontuacao_atual >= melhoria["preco"]:
                melhoria["comprada"] = True
                self.ativar_melhoria(melhoria)
                salvar_jogo()
                return pontuacao_atual - melhoria["preco"]
        return pontuacao_atual

    def ativar_melhoria(self, melhoria):
        melhoria["ativa"] = True
        if melhoria["tipo"] == "vida":
            global vida_jogador, max_vida
            max_vida += 1
            vida_jogador = min(vida_jogador + 1, max_vida)
        elif melhoria["tipo"] == "escudo":
            self.tempo_escudo = pygame.time.get_ticks()
        elif melhoria["tipo"] == "explosao":
            self.explosoes_restantes = melhoria["usos"]
        elif melhoria["tipo"] == "campo":
            self.tempo_campo = pygame.time.get_ticks()

    def usar_explosao_nuclear(self):
        if self.explosoes_restantes > 0:
            self.explosoes_restantes -= 1
            return True
        return False

    def pode_usar_explosao_nuclear(self):  # CORREÇÃO 8: Nova função de verificação
        return (any(m["comprada"] and m["tipo"] == "explosao" for m in self.melhorias)
                and self.explosoes_restantes > 0)

    def alternar_secao(self):
        if self.secao_atual == "naves":
            self.secao_atual = "melhorias"
        else:
            self.secao_atual = "naves"

    def atualizar_rotacao(self):
        self.rotacao_angulo = (self.rotacao_angulo + 2) % 360

    def verificar_escudo_ativo(self):
        if not any(m["comprada"] and m["tipo"] == "escudo" for m in self.melhorias):
            return False
        return pygame.time.get_ticks() - self.tempo_escudo < self.melhorias[3]["duracao"]

    def verificar_campo_ativo(self):
        if not any(m["comprada"] and m["tipo"] == "campo" for m in self.melhorias):
            return False
        return pygame.time.get_ticks() - self.tempo_campo < self.melhorias[6]["duracao"]

    def verificar_ima_ativo(self):
        return any(m["comprada"] and m["tipo"] == "ima" for m in self.melhorias)


# CORREÇÃO 2 e 5: Sistema de pontuação consistente
def atualizar_pontuacao():
    global tempo_atual
    tempo_atual = (pygame.time.get_ticks() - tempo_inicio) // 1000
    # Não sobrescrever pontuação acumulada - apenas calcular nível
    atualizar_nivel()


# CORREÇÃO 6: Aplicar estatísticas de forma consistente
def aplicar_estatisticas_nave():
    global velocidade_jogador, dano_base, bonus_pontuacao, tiro_duplo
    nave = loja.naves[loja.nave_selecionada]

    # CORREÇÃO 6: Velocidade consistente
    velocidade_base = 5
    velocidade_jogador = velocidade_base + (nave["velocidade"] - 5) * 0.3  # 5-9 vira 5-6.2

    # Aplicar bônus de velocidade se a melhoria foi comprada
    if any(m["comprada"] and m["tipo"] == "velocidade" for m in loja.melhorias):
        velocidade_jogador += loja.melhorias[1]["bonus"]

    dano_base = nave["dano"]
    bonus_pontuacao = nave["bonus"] / 100.0
    tiro_duplo = nave["tiro_duplo"]


# CORREÇÃO 7: Lógica do boss simplificada
def verificar_boss():
    global boss, boss_ativo
    if nivel % 5 == 0 and not boss_ativo and nivel > ultimo_boss_derrotado:
        boss = Boss(nivel)
        boss_ativo = True
        return True
    return False


# Classe para sprites animados
class SpriteAnimado:
    def __init__(self, imagens, escala=(40, 40), tempo_quadro=100):
        self.quadros = []
        for img_path in imagens:
            try:
                img = pygame.image.load(os.path.join(caminho_imagens, img_path))
                img = pygame.transform.scale(img, escala)
                self.quadros.append(img)
            except FileNotFoundError:
                print(f"Arquivo não encontrado: {img_path}")
                placeholder = pygame.Surface(escala)
                placeholder.fill((random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)))
                self.quadros.append(placeholder)

        if not self.quadros:
            placeholder = pygame.Surface(escala)
            placeholder.fill((255, 0, 0))
            self.quadros.append(placeholder)

        self.quadro_atual = 0
        self.tempo_quadro = tempo_quadro
        self.ultimo_tempo = pygame.time.get_ticks()

    def atualizar(self):
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_tempo > self.tempo_quadro and len(self.quadros) > 1:
            self.quadro_atual = (self.quadro_atual + 1) % len(self.quadros)
            self.ultimo_tempo = tempo_atual

    def get_imagem(self):
        return self.quadros[self.quadro_atual]


# Classe para o Boss
class Boss:
    def __init__(self, nivel_boss):
        self.nivel_boss = nivel_boss
        self.vida_maxima = 100 + (nivel_boss // 5) * 50
        self.vida = self.vida_maxima
        self.largura = 80
        self.altura = 80
        self.rect = pygame.Rect(largura // 2 - self.largura // 2, 50, self.largura, self.altura)
        self.velocidade = 2 + (nivel_boss // 5) * 0.5
        self.ultimo_tiro = pygame.time.get_ticks()
        self.intervalo_tiros = max(500, 1000 - (nivel_boss // 5) * 100)
        self.tiros_simultaneos = 1 + (nivel_boss // 5)

    def atualizar(self, jogador_rect):
        if self.rect.centerx < jogador_rect.centerx:
            self.rect.x += min(self.velocidade, jogador_rect.centerx - self.rect.centerx)
        elif self.rect.centerx > jogador_rect.centerx:
            self.rect.x -= min(self.velocidade, self.rect.centerx - jogador_rect.centerx)

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > largura:
            self.rect.right = largura

    def pode_atirar(self):
        agora = pygame.time.get_ticks()
        return agora - self.ultimo_tiro > self.intervalo_tiros

    def atirar(self, jogador_rect):
        self.ultimo_tiro = pygame.time.get_ticks()
        projeteis = []

        if self.tiros_simultaneos == 1:
            direcao_x = jogador_rect.centerx - self.rect.centerx
            if abs(direcao_x) > 0:
                fator = min(10, abs(direcao_x) / 10)
                offset_x = direcao_x / abs(direcao_x) * fator
            else:
                offset_x = 0

            x = self.rect.centerx - 5 + offset_x
            y = self.rect.bottom
            projeteis.append(pygame.Rect(x, y, 10, 20))

        else:
            for i in range(self.tiros_simultaneos):
                offset = (i - (self.tiros_simultaneos - 1) / 2) * 15
                x = self.rect.centerx - 5 + offset
                y = self.rect.bottom
                projeteis.append(pygame.Rect(x, y, 10, 20))

        return projeteis

    def levar_dano(self, dano):
        self.vida -= dano
        return self.vida <= 0

    def desenhar_barra_vida(self, surface):
        barra_largura = 100
        barra_altura = 10
        x = self.rect.centerx - barra_largura // 2
        y = self.rect.top - 20

        pygame.draw.rect(surface, (255, 0, 0), (x, y, barra_largura, barra_altura))
        vida_largura = int((self.vida / self.vida_maxima) * barra_largura)
        pygame.draw.rect(surface, (0, 255, 0), (x, y, vida_largura, barra_altura))


# Verificar quais arquivos existem
def verificar_arquivos():
    arquivos_existentes = []
    for arquivo in os.listdir(caminho_imagens):
        if arquivo.lower().endswith(('.gif', '.png', '.jpg', '.jpeg')):
            arquivos_existentes.append(arquivo)
    return arquivos_existentes


# Lista de arquivos disponíveis
arquivos_disponiveis = verificar_arquivos()
print("Arquivos encontrados:", arquivos_disponiveis)


# CORREÇÃO 10: Carregamento de imagens mais robusto
def carregar_sprites():
    naves_animadas = []
    naves_arquivos = [
        "nave_azulroxo3.gif", "nave_laranja3.gif", "nave_rosa2.gif",
        "nave_verde3.gif", "nave_vermelho1.gif", "nave_vermelho3.gif"
    ]

    naves_existentes = [nave for nave in naves_arquivos if nave in arquivos_disponiveis]

    if not naves_existentes and arquivos_disponiveis:
        naves_existentes = [arquivos_disponiveis[0]]
    elif not naves_existentes:
        # Criar placeholder se não encontrar arquivos
        placeholder = pygame.Surface((40, 40))
        placeholder.fill((255, 0, 255))
        sprite_placeholder = SpriteAnimado([], (40, 40), 200)
        sprite_placeholder.quadros = [placeholder]
        return [sprite_placeholder]

    for nave_arquivo in naves_existentes:
        naves_animadas.append(SpriteAnimado([nave_arquivo], (40, 40), 200))

    return naves_animadas


# Carregar sprites
naves_animadas = carregar_sprites()

# Restante do carregamento de sprites...
tamanho_meteoro = 60
if "meteoro.gif" in arquivos_disponiveis:
    meteoro_animado = SpriteAnimado(["meteoro.gif"], (tamanho_meteoro, tamanho_meteoro), 150)
else:
    meteoro_animado = SpriteAnimado([], (tamanho_meteoro, tamanho_meteoro), 150)
    meteoro_animado.quadros = [pygame.Surface((tamanho_meteoro, tamanho_meteoro))]

if "projetil_base.gif" in arquivos_disponiveis:
    projetil_animado = SpriteAnimado(["projetil_base.gif"], (15, 25), 100)
else:
    projetil_animado = SpriteAnimado([], (15, 25), 100)
    projetil_animado.quadros = [pygame.Surface((15, 25))]

if "projetil_boss.gif" in arquivos_disponiveis:
    projetil_boss_animado = SpriteAnimado(["projetil_boss.gif"], (15, 25), 100)
else:
    projetil_boss_animado = SpriteAnimado([], (15, 25), 100)
    projetil_boss_animado.quadros = [pygame.Surface((15, 25))]

if "nave_boss.gif" in arquivos_disponiveis:
    boss_animado = SpriteAnimado(["nave_boss.gif"], (80, 80), 200)
else:
    boss_animado = SpriteAnimado([], (80, 80), 200)
    boss_animado.quadros = [pygame.Surface((80, 80))]

if "coracao.png" in arquivos_disponiveis:
    coracao_img = pygame.transform.scale(pygame.image.load(os.path.join(caminho_imagens, "coracao.png")), (30, 30))
else:
    coracao_img = pygame.Surface((30, 30))
    coracao_img.fill((255, 0, 0))

if "portal.gif" in arquivos_disponiveis:
    portal_animado = SpriteAnimado(["portal.gif"], (60, 60), 150)
else:
    portal_animado = SpriteAnimado([], (60, 60), 150)
    portal_animado.quadros = [pygame.Surface((60, 60))]

# Variáveis globais do jogo
jogador = pygame.Rect(180, 500, 40, 40)
velocidade_jogador = 5  # CORREÇÃO 6: Variável renomeada para evitar conflito
dano_base = 1
bonus_pontuacao = 0
tiro_duplo = False
meteoros = []
projeteis = []
projeteis_boss = []
explosoes = []
boss = None
boss_ativo = False
coracoes = []
portais = []
ultimo_coracao = pygame.time.get_ticks()
intervalo_coracoes = 15000
ultimo_portal = pygame.time.get_ticks()
intervalo_portais = 30000

# Instanciar a loja
loja = Loja()

# Carregar jogo salvo
carregar_jogo()
aplicar_estatisticas_nave()


def criar_meteoro():
    x = random.randint(0, largura - tamanho_meteoro)
    rect = pygame.Rect(x, -tamanho_meteoro, tamanho_meteoro, tamanho_meteoro)
    velocidade_meteoro = velocidade_base + (nivel * 1.2)
    rotacao_speed = random.uniform(-2, 2)
    return {"rect": rect, "velocidade": velocidade_meteoro, "rotacao": 0, "rotacao_speed": rotacao_speed, "vida": 1}


def criar_projetil():
    projetis = []
    nave = loja.naves[loja.nave_selecionada]

    if nave["tiro_duplo"]:
        # Tiro duplo
        projetis.append({"rect": pygame.Rect(jogador.centerx - 15, jogador.top, 10, 20), "dano": dano_base})
        projetis.append({"rect": pygame.Rect(jogador.centerx + 5, jogador.top, 10, 20), "dano": dano_base})
    else:
        # Tiro único
        projetis.append({"rect": pygame.Rect(jogador.centerx - 5, jogador.top, 10, 20), "dano": dano_base})

    # Verificar se tem tiro triplo
    if any(m["comprada"] and m["tipo"] == "tiro" for m in loja.melhorias):
        projetis.append({"rect": pygame.Rect(jogador.centerx - 5, jogador.top - 20, 10, 20), "dano": dano_base})

    return projetis


def criar_coracao():
    x = random.randint(30, largura - 30)
    return pygame.Rect(x, -30, 30, 30)


def criar_portal():
    x = random.randint(60, largura - 60)
    return pygame.Rect(x, -60, 60, 60)


def criar_explosao(x, y, tamanho=50):
    return {"rect": pygame.Rect(x - tamanho // 2, y - tamanho // 2, tamanho, tamanho),
            "tempo_inicio": pygame.time.get_ticks(), "duracao": 500}


def desenhar_explosao(surface, explosao):
    tempo_decorrido = pygame.time.get_ticks() - explosao["tempo_inicio"]
    progresso = min(tempo_decorrido / explosao["duracao"], 1.0)

    raio = int(progresso * explosao["rect"].width // 2)
    for i in range(3):
        cor = (255, 165 - i * 30, 0)
        pygame.draw.circle(surface, cor, explosao["rect"].center, raio - i * 5)

    for i in range(15):
        angulo = random.uniform(0, 6.28)
        distancia = progresso * 40
        x = explosao["rect"].centerx + int(distancia * pygame.math.Vector2(1, 0).rotate(angulo).x)
        y = explosao["rect"].centery + int(distancia * pygame.math.Vector2(1, 0).rotate(angulo).y)
        pygame.draw.circle(surface, (255, 255, 100), (x, y), 3)


def explosao_nuclear():
    global meteoros, pontuacao
    meteoros_atingidos = len(meteoros)
    for meteoro in meteoros[:]:
        explosoes.append(criar_explosao(meteoro["rect"].centerx, meteoro["rect"].centery, 70))
        # CORREÇÃO 5: Sistema de pontuação consistente
        pontos_meteoro = 50 * (1 + bonus_pontuacao)
        pontuacao += int(pontos_meteoro)
    meteoros.clear()
    return meteoros_atingidos


def aplicar_ima_itens():
    if loja.verificar_ima_ativo():
        for coracao in coracoes[:]:
            # Movimento suave em direção ao jogador
            dx = jogador.centerx - coracao.centerx
            dy = jogador.centery - coracao.centery
            distancia = math.sqrt(dx * dx + dy * dy)

            if distancia > 0:
                coracao.x += dx / distancia * 5
                coracao.y += dy / distancia * 5


def avancar_nivel(quantidade):
    global nivel, boss, boss_ativo
    nivel_anterior = nivel
    nivel += quantidade
    # CORREÇÃO 5: Sistema de pontuação consistente
    pontos_nivel = quantidade * 200 * (1 + bonus_pontuacao)
    pontuacao += int(pontos_nivel)

    for i in range(nivel_anterior + 1, nivel + 1):
        verificar_boss()  # CORREÇÃO 7: Usar função simplificada


def atualizar_nivel():
    global nivel, boss_ativo, boss
    # CORREÇÃO 2: Nível baseado na pontuação, mas não sobrescreve pontuação
    novo_nivel = max(1, pontuacao // 500 + 1)

    if novo_nivel > nivel:
        nivel = novo_nivel
        verificar_boss()  # CORREÇÃO 7: Usar função simplificada


def desenhar_vidas():
    for i in range(vida_jogador):
        x = largura - 40 - (i * 35)
        y = 10
        tela.blit(coracao_img, (x, y))


def desenhar_efeitos_ativos():
    y_offset = 50
    if loja.verificar_escudo_ativo():
        tempo_restante = (loja.melhorias[3]["duracao"] - (pygame.time.get_ticks() - loja.tempo_escudo)) // 1000
        texto_escudo = fonte_pequena.render(f"Escudo: {tempo_restante}s", True, (0, 255, 255))
        tela.blit(texto_escudo, (largura - 150, y_offset))
        y_offset += 25

    if loja.verificar_campo_ativo():
        tempo_restante = (loja.melhorias[6]["duracao"] - (pygame.time.get_ticks() - loja.tempo_campo)) // 1000
        texto_campo = fonte_pequena.render(f"Campo: {tempo_restante}s", True, (255, 255, 0))
        tela.blit(texto_campo, (largura - 150, y_offset))
        y_offset += 25

    if loja.explosoes_restantes > 0:
        texto_explosao = fonte_pequena.render(f"Explosões: {loja.explosoes_restantes}", True, (255, 100, 100))
        tela.blit(texto_explosao, (largura - 150, y_offset))


def desenhar_interface():
    texto_pontuacao = fonte.render(f'Pontos: {pontuacao}', True, (255, 255, 255))
    tela.blit(texto_pontuacao, (10, 10))

    minutos = tempo_atual // 60
    segundos = tempo_atual % 60
    texto_tempo = fonte.render(f'Tempo: {minutos:02d}:{segundos:02d}', True, (255, 255, 255))
    tela.blit(texto_tempo, (10, 50))

    texto_nivel = fonte.render(f'Nível: {nivel}', True, (255, 255, 255))
    tela.blit(texto_nivel, (10, 90))

    nave_atual = loja.naves[loja.nave_selecionada]
    texto_nave = fonte.render(f'Nave: {nave_atual["nome"]}', True, nave_atual["cor"])
    tela.blit(texto_nave, (10, 130))

    desenhar_vidas()
    desenhar_efeitos_ativos()

    if boss_ativo:
        texto_boss = fonte.render('BOSS!', True, (255, 0, 0))
        tela.blit(texto_boss, (largura - 100, 10))

        if boss:
            texto_vida_boss = fonte_pequena.render(f'Boss: {boss.vida}/{boss.vida_maxima}', True, (255, 255, 255))
            tela.blit(texto_vida_boss, (largura - 120, 40))

    texto_instrucoes = fonte_pequena.render('L: Loja | R: Reiniciar | X: Explosão', True, (200, 200, 200))
    tela.blit(texto_instrucoes, (10, altura - 30))


def desenhar_loja():
    tela.fill((10, 10, 40))

    # Título
    titulo = fonte_grande.render("SHOWROOM DE NAVES", True, (255, 255, 255))
    tela.blit(titulo, (largura // 2 - titulo.get_width() // 2, 20))

    # Informações do jogador
    info_saldo = fonte.render(f"SALDO: {pontuacao} pts", True, (255, 255, 0))
    naves_compradas = sum(1 for n in loja.naves if n["comprada"])
    info_naves = fonte.render(f"NAVES: {naves_compradas}/{len(loja.naves)}", True, (0, 255, 255))
    info_vidas = fonte.render(f"VIDAS: {vida_jogador}/{max_vida}", True, (255, 100, 100))
    info_nivel = fonte.render(f"NÍVEL: {nivel}", True, (100, 255, 100))

    tela.blit(info_saldo, (20, 80))
    tela.blit(info_naves, (20, 120))
    tela.blit(info_vidas, (largura - 200, 80))
    tela.blit(info_nivel, (largura - 200, 120))

    # Nave selecionada
    nave_atual = loja.naves[loja.nave_selecionada]

    # Container principal
    pygame.draw.rect(tela, (30, 30, 60), (20, 160, largura - 40, altura - 250), 0, 10)
    pygame.draw.rect(tela, (60, 60, 100), (20, 160, largura - 40, altura - 250), 3, 10)

    # Nome e preço da nave
    nome_texto = fonte_grande.render(nave_atual["nome"], True, nave_atual["cor"])
    status_preco = "COMPRADA" if nave_atual["comprada"] else f"{nave_atual['preco']} pontos"
    cor_preco = (0, 255, 0) if nave_atual["comprada"] else (255, 255, 0)
    preco_texto = fonte.render(status_preco, True, cor_preco)

    tela.blit(nome_texto, (largura // 2 - nome_texto.get_width() // 2, 180))
    tela.blit(preco_texto, (largura // 2 - preco_texto.get_width() // 2, 220))

    # Área de visualização da nave
    pygame.draw.rect(tela, (20, 20, 40), (40, 260, 160, 200), 0, 5)

    # Desenhar nave animada
    loja.atualizar_rotacao()
    nave_img = naves_animadas[loja.nave_selecionada % len(naves_animadas)].get_imagem()
    nave_rotacionada = pygame.transform.rotate(nave_img, loja.rotacao_angulo)
    tela.blit(nave_rotacionada, (120 - nave_rotacionada.get_width() // 2, 360 - nave_rotacionada.get_height() // 2))

    # Estatísticas
    stats_x = 220
    stats_y = 260

    stats_titulo = fonte.render("ESTATÍSTICAS:", True, (200, 200, 255))
    tela.blit(stats_titulo, (stats_x, stats_y))

    stats = [
        f"Velocidade: {nave_atual['velocidade']}/10",
        f"Dano: {nave_atual['dano']}/5",
        f"Defesa: {nave_atual['defesa']}/10",
        f"Agilidade: {nave_atual['agilidade']}/10",
        f"Bônus: +{nave_atual['bonus']}% pontos"
    ]

    for i, stat in enumerate(stats):
        cor = (200, 255, 200) if i < 4 else (255, 255, 100)
        texto_stat = fonte_pequena.render(stat, True, cor)
        tela.blit(texto_stat, (stats_x, stats_y + 40 + i * 25))

    # Habilidade especial
    habilidade_y = stats_y + 180
    habilidade_titulo = fonte.render("HABILIDADE ESPECIAL:", True, (200, 200, 255))
    tela.blit(habilidade_titulo, (stats_x, habilidade_y))

    if nave_atual["tiro_duplo"]:
        habilidade_texto = fonte_pequena.render("Tiro Duplo Automático", True, (255, 200, 100))
        descricao1 = fonte_pequena.render("• Dispara dois projéteis", True, (200, 200, 200))
        descricao2 = fonte_pequena.render("• Maior chance de acerto", True, (200, 200, 200))

        tela.blit(habilidade_texto, (stats_x, habilidade_y + 30))
        tela.blit(descricao1, (stats_x, habilidade_y + 55))
        tela.blit(descricao2, (stats_x, habilidade_y + 75))
    else:
        basica_texto = fonte_pequena.render("Nave básica padrão", True, (200, 200, 200))
        tela.blit(basica_texto, (stats_x, habilidade_y + 30))

    # Botões de compra/seleção
    if nave_atual["comprada"]:
        if nave_atual["selecionada"]:
            status_texto = fonte.render("SELECIONADA", True, (0, 255, 0))
        else:
            status_texto = fonte.render("[ENTER] SELECIONAR", True, (255, 255, 0))
    else:
        if pontuacao >= nave_atual["preco"]:
            comprar_texto = fonte.render("[ENTER] COMPRAR", True, (0, 255, 0))
        else:
            comprar_texto = fonte.render("PONTOS INSUFICIENTES", True, (255, 0, 0))
        tela.blit(comprar_texto, (largura // 2 - comprar_texto.get_width() // 2, altura - 80))

    # Controles
    controles = [
        "[←→] Navegar nave",
        "[1-5] Seleção rápida",
        "[ESPACO] Girar nave",
        "[TAB] Loja de melhorias",
        "[ESC] Voltar ao jogo"
    ]

    for i, controle in enumerate(controles):
        texto_controle = fonte_pequena.render(controle, True, (150, 150, 200))
        tela.blit(texto_controle, (20 + i % 2 * 200, altura - 40 + i // 2 * 20))


def rotacionar_imagem(imagem, angulo):
    return pygame.transform.rotate(imagem, angulo)


rodando = True
game_over = False

while rodando:
    if loja.ativa:
        tela.fill((0, 0, 40))
        desenhar_loja()
    else:
        tela.fill((0, 0, 40))

        # Fundo estelar
        for i in range(50):
            x = random.randint(0, largura)
            y = random.randint(0, altura)
            pygame.draw.circle(tela, (255, 255, 255), (x, y), 1)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            salvar_jogo()
            rodando = False

        if evento.type == pygame.KEYDOWN:
            if loja.ativa:
                # Controles da loja
                if evento.key == pygame.K_ESCAPE:
                    loja.fechar_loja()
                elif evento.key == pygame.K_RIGHT:
                    loja.selecionar_nave((loja.nave_selecionada + 1) % len(loja.naves))
                elif evento.key == pygame.K_LEFT:
                    loja.selecionar_nave((loja.nave_selecionada - 1) % len(loja.naves))
                elif evento.key == pygame.K_SPACE:
                    loja.rotacao_angulo = 0
                elif evento.key == pygame.K_RETURN:
                    if loja.naves[loja.nave_selecionada]["comprada"]:
                        loja.selecionar_nave(loja.nave_selecionada)
                    else:
                        pontuacao = loja.comprar_nave(pontuacao)
                elif evento.key == pygame.K_1:
                    loja.selecionar_nave(0)
                elif evento.key == pygame.K_2:
                    loja.selecionar_nave(1)
                elif evento.key == pygame.K_3:
                    loja.selecionar_nave(2)
                elif evento.key == pygame.K_4:
                    loja.selecionar_nave(3)
                elif evento.key == pygame.K_5:
                    loja.selecionar_nave(4)
                elif evento.key == pygame.K_TAB:
                    # Implementar tela de melhorias aqui
                    pass
            else:
                # Controles do jogo
                if evento.key == pygame.K_SPACE and not game_over:
                    novos_projeteis = criar_projetil()
                    projeteis.extend(novos_projeteis)
                elif evento.key == pygame.K_r and game_over:
                    # Reiniciar jogo
                    jogador = pygame.Rect(180, 500, 40, 40)
                    meteoros = []
                    projeteis = []
                    projeteis_boss = []
                    explosoes = []
                    coracoes = []
                    portais = []
                    boss = None
                    boss_ativo = False
                    pontuacao = 0
                    nivel = 1
                    vida_jogador = 3
                    max_vida = 5
                    tempo_inicio = pygame.time.get_ticks()
                    ultimo_boss_derrotado = 0
                    game_over = False
                    # Resetar loja
                    loja = Loja()
                    aplicar_estatisticas_nave()
                elif evento.key == pygame.K_l and not game_over:
                    loja.abrir_loja()
                elif evento.key == pygame.K_x and not game_over:
                    # CORREÇÃO 8: Verificar se pode usar explosão nuclear
                    if loja.pode_usar_explosao_nuclear() and loja.usar_explosao_nuclear():
                        meteoros_destruidos = explosao_nuclear()
                        print(f"Explosão nuclear! {meteoros_destruidos} meteoros destruídos!")

    if not loja.ativa and not game_over:
        # Movimento do jogador - CORREÇÃO 6: Usar velocidade_jogador
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT] and jogador.left > 0:
            jogador.x -= velocidade_jogador
        if teclas[pygame.K_RIGHT] and jogador.right < largura:
            jogador.x += velocidade_jogador
        if teclas[pygame.K_UP] and jogador.top > 0:
            jogador.y -= velocidade_jogador
        if teclas[pygame.K_DOWN] and jogador.bottom < altura:
            jogador.y += velocidade_jogador

        # Criar meteoros
        if not boss_ativo and random.randint(1, max(5, 60 - nivel * 3)) == 1:
            meteoros.append(criar_meteoro())

        # Aplicar imã de itens
        aplicar_ima_itens()

        # Atualizar meteoros
        for meteoro in meteoros[:]:
            meteoro["rect"].y += meteoro["velocidade"]
            meteoro["rotacao"] += meteoro["rotacao_speed"]

            # Verificar colisão com jogador
            if meteoro["rect"].colliderect(jogador):
                # Verificar escudo ativo
                if not loja.verificar_escudo_ativo():
                    explosoes.append(criar_explosao(meteoro["rect"].centerx, meteoro["rect"].centery, 70))
                    vida_jogador -= 1
                    if vida_jogador <= 0:
                        game_over = True
                else:
                    explosoes.append(criar_explosao(meteoro["rect"].centerx, meteoro["rect"].centery, 30))

                if meteoro in meteoros:
                    meteoros.remove(meteoro)

            # Desenhar meteoro
            meteoro_img_rotacionada = rotacionar_imagem(meteoro_animado.get_imagem(), meteoro["rotacao"])
            tela.blit(meteoro_img_rotacionada, meteoro["rect"])

        # Atualizar corações
        for coracao in coracoes[:]:
            coracao.y += 3

            if coracao.colliderect(jogador) and vida_jogador < max_vida:
                vida_jogador += 1
                coracoes.remove(coracao)
                explosoes.append(criar_explosao(coracao.centerx, coracao.centery, 30))

            elif coracao.y < altura:
                tela.blit(coracao_img, coracao)
            else:
                coracoes.remove(coracao)

        # Atualizar portais
        for portal in portais[:]:
            portal.y += 2

            if portal.colliderect(jogador):
                avancar_nivel(3)
                portais.remove(portal)
                explosoes.append(criar_explosao(portal.centerx, portal.centery, 80))

            elif portal.y < altura:
                portal_animado.atualizar()
                tela.blit(portal_animado.get_imagem(), portal)
            else:
                portais.remove(portal)

        # Atualizar projéteis do jogador
        for projetil in projeteis[:]:
            projetil["rect"].y -= 10

            # Colisão com meteoros
            for meteoro in meteoros[:]:
                if projetil["rect"].colliderect(meteoro["rect"]):
                    meteoro["vida"] -= projetil["dano"]
                    if meteoro["vida"] <= 0:
                        explosoes.append(criar_explosao(meteoro["rect"].centerx, meteoro["rect"].centery, 70))
                        if meteoro in meteoros:
                            meteoros.remove(meteoro)
                        # CORREÇÃO 5: Sistema de pontuação consistente
                        pontos_meteoro = 50 * (1 + bonus_pontuacao)
                        pontuacao += int(pontos_meteoro)

                    if projetil in projeteis:
                        projeteis.remove(projetil)
                    break

            # Colisão com boss
            if boss_ativo and boss and projetil["rect"].colliderect(boss.rect):
                explosoes.append(criar_explosao(projetil["rect"].centerx, projetil["rect"].centery, 30))
                if projetil in projeteis:
                    projeteis.remove(projetil)
                if boss.levar_dano(projetil["dano"] * 2):
                    explosoes.append(criar_explosao(boss.rect.centerx, boss.rect.centery, 100))
                    pontos_boss = 500 * (1 + bonus_pontuacao)
                    pontuacao += int(pontos_boss)
                    ultimo_boss_derrotado = boss.nivel_boss
                    boss = None
                    boss_ativo = False
                break

            if projetil["rect"].bottom < 0:
                projeteis.remove(projetil)
            else:
                tela.blit(projetil_animado.get_imagem(), projetil["rect"])

        # Atualizar projéteis do boss
        for projetil in projeteis_boss[:]:
            projetil.y += 7

            if projetil.colliderect(jogador):
                if not loja.verificar_escudo_ativo() and not loja.verificar_campo_ativo():
                    explosoes.append(criar_explosao(projetil.centerx, projetil.centery, 40))
                    vida_jogador -= 1
                    if vida_jogador <= 0:
                        game_over = True
                else:
                    explosoes.append(criar_explosao(projetil.centerx, projetil.centery, 20))

                projeteis_boss.remove(projetil)

            elif projetil.top > altura:
                projeteis_boss.remove(projetil)
            else:
                tela.blit(projetil_boss_animado.get_imagem(), projetil)

        # Limpar meteoros fora da tela
        meteoros = [meteoro for meteoro in meteoros if meteoro["rect"].y < altura]

    if not loja.ativa:
        # Atualizar sprites
        if naves_animadas:
            naves_animadas[loja.nave_selecionada % len(naves_animadas)].atualizar()
        meteoro_animado.atualizar()
        projetil_animado.atualizar()
        projetil_boss_animado.atualizar()
        portal_animado.atualizar()

        # Atualizar boss
        if boss_ativo and boss:
            boss_animado.atualizar()
            boss.atualizar(jogador)

            if boss.pode_atirar():
                novos_projeteis = boss.atirar(jogador)
                projeteis_boss.extend(novos_projeteis)

        # Spawn de corações e portais
        agora = pygame.time.get_ticks()
        if agora - ultimo_coracao > intervalo_coracoes and len(coracoes) < 3:
            coracoes.append(criar_coracao())
            ultimo_coracao = agora

        if agora - ultimo_portal > intervalo_portais and len(portais) < 1 and not boss_ativo:
            portais.append(criar_portal())
            ultimo_portal = agora

        # Atualizar tempo e nível
        atualizar_pontuacao()

        # Desenhar elementos do jogo
        if boss_ativo and boss:
            tela.blit(boss_animado.get_imagem(), boss.rect)
            boss.desenhar_barra_vida(tela)

        # Desenhar explosões
        for explosao in explosoes[:]:
            tempo_decorrido = pygame.time.get_ticks() - explosao["tempo_inicio"]
            if tempo_decorrido > explosao["duracao"]:
                explosoes.remove(explosao)
            else:
                desenhar_explosao(tela, explosao)

        # Desenhar interface
        desenhar_interface()

        # Desenhar jogador
        if not game_over and naves_animadas:
            # Efeito visual para escudo/campo ativo
            if loja.verificar_escudo_ativo():
                pygame.draw.circle(tela, (0, 255, 255), jogador.center, 25, 2)
            if loja.verificar_campo_ativo():
                pygame.draw.circle(tela, (255, 255, 0), jogador.center, 30, 2)

            tela.blit(naves_animadas[loja.nave_selecionada % len(naves_animadas)].get_imagem(), jogador)
        elif game_over:
            texto_gameover = fonte_grande.render('GAME OVER', True, (255, 0, 0))
            texto_reiniciar = fonte.render('Pressione R para reiniciar', True, (255, 255, 255))
            tela.blit(texto_gameover, (largura // 2 - texto_gameover.get_width() // 2, altura // 2 - 50))
            tela.blit(texto_reiniciar, (largura // 2 - texto_reiniciar.get_width() // 2, altura // 2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()