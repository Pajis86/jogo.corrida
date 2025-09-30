import random
import pygame
import os
import math

pygame.init()

largura, altura = 400, 600
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("Nave vs Meteoros")
clock = pygame.time.Clock()

# == CORREÇÃO: Caminho das imagens ==
# Usando caminho relativo (mesma pasta do script)
caminho_imagens = os.path.dirname(os.path.abspath(__file__))
print(f"Procurando imagens em: {caminho_imagens}")

# == Sistema de Pontuação, tempo e níveis ===
fonte = pygame.font.Font(None, 36)
fonte_pequena = pygame.font.Font(None, 24)
pontuacao = 0
tempo_inicio = pygame.time.get_ticks()
tempo_atual = 0
nivel = 1
velocidade_base = 3
vida_jogador = 3
max_vida = 5

# == Sistema de Munição e Recarga ==
municao_maxima = 10
municao_atual = municao_maxima
ultimo_recarga = pygame.time.get_ticks()
intervalo_recarga = 10000  # 10 segundos para recarregar TODA a munição
recarregando = False
tempo_inicio_recarga = 0

# == Sistema de Lazer/Kamehameha ==
lazer_ativado = False
lazer_tempo_inicio = 0
lazer_duracao = 2000  # 2 segundos
lazer_cooldown = 10000  # 10 segundos de cooldown
ultimo_lazer = 0
lazer_carregando = False
lazer_carregamento_tempo = 0

# == Sistema de Habilidades Especiais ==
# Cooldowns para cada nave (0-5 correspondendo às naves)
habilidade_cooldown = [0, 0, 0, 0, 0, 0]
habilidade_duracao = [0, 0, 0, 0, 0, 0]
habilidade_ativa = [False, False, False, False, False, False]
meteoros_congelados = []
escudo_ativo = False
escudo_tempo_fim = 0
tiro_triplo_ativo = False
tiro_triplo_contador = 0  # Contador de tiros triplos restantes
velocidade_dupla_ativa = False
velocidade_dupla_tempo_fim = 0

# == Sistema de Boss Múltiplo ==
bosses = []  # Lista para armazenar múltiplos bosses


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
    def __init__(self, nivel_boss, x, usar_lazer=False):
        self.nivel_boss = nivel_boss
        self.usar_lazer = usar_lazer
        self.vida_maxima = 80 + (nivel_boss // 5) * 40  # Menos vida para múltiplos bosses
        self.vida = self.vida_maxima
        self.largura = 70
        self.altura = 70
        self.rect = pygame.Rect(x, 50, self.largura, self.altura)
        self.velocidade = 2 + (nivel_boss // 5) * 0.5
        self.ultimo_tiro = pygame.time.get_ticks()
        self.intervalo_tiros = max(500, 1000 - (nivel_boss // 5) * 100)
        self.tiros_simultaneos = 1 + (nivel_boss // 5)

        # Sistema de lazer para o boss
        self.lazer_ativado = False
        self.lazer_tempo_inicio = 0
        self.lazer_duracao = 1500  # 1.5 segundos
        self.ultimo_lazer = 0
        self.lazer_cooldown = 8000  # 8 segundos

    def atualizar(self, jogador_rect):
        # Seguir o jogador suavemente
        if self.rect.centerx < jogador_rect.centerx:
            self.rect.x += min(self.velocidade, jogador_rect.centerx - self.rect.centerx)
        elif self.rect.centerx > jogador_rect.centerx:
            self.rect.x -= min(self.velocidade, self.rect.centerx - jogador_rect.centerx)

        # Manter o boss dentro da tela
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > largura:
            self.rect.right = largura

    def pode_atirar(self):
        agora = pygame.time.get_ticks()
        return agora - self.ultimo_tiro > self.intervalo_tiros

    def pode_usar_lazer(self):
        if not self.usar_lazer:
            return False
        agora = pygame.time.get_ticks()
        return agora - self.ultimo_lazer > self.lazer_cooldown

    def ativar_lazer(self):
        if self.pode_usar_lazer():
            self.lazer_ativado = True
            self.lazer_tempo_inicio = pygame.time.get_ticks()
            self.ultimo_lazer = pygame.time.get_ticks()
            return True
        return False

    def atirar(self, jogador_rect):
        self.ultimo_tiro = pygame.time.get_ticks()
        projeteis = []

        # Diferentes padrões de tiro baseados no nível
        if self.tiros_simultaneos == 1:
            # Tiro único direcionado ao jogador
            direcao_x = jogador_rect.centerx - self.rect.centerx
            direcao_y = jogador_rect.centery - self.rect.centery

            # Calcular ângulo para direção do projétil
            angulo = math.atan2(direcao_y, direcao_x)

            x = self.rect.centerx - 5
            y = self.rect.bottom
            projeteis.append({
                "rect": pygame.Rect(x, y, 10, 20),
                "velocidade_x": math.cos(angulo) * 5,
                "velocidade_y": math.sin(angulo) * 5
            })

        else:
            # Tiros múltiplos em leque
            for i in range(self.tiros_simultaneos):
                offset = (i - (self.tiros_simultaneos - 1) / 2) * 15

                # Para bosses nível 10+, calcular direção para o jogador
                if self.nivel_boss >= 10:
                    direcao_x = jogador_rect.centerx - (self.rect.centerx + offset)
                    direcao_y = jogador_rect.centery - self.rect.centery
                    angulo = math.atan2(direcao_y, direcao_x)

                    x = self.rect.centerx - 5 + offset
                    y = self.rect.bottom
                    projeteis.append({
                        "rect": pygame.Rect(x, y, 10, 20),
                        "velocidade_x": math.cos(angulo) * 5,
                        "velocidade_y": math.sin(angulo) * 5
                    })
                else:
                    # Tiros normais para baixo
                    x = self.rect.centerx - 5 + offset
                    y = self.rect.bottom
                    projeteis.append({
                        "rect": pygame.Rect(x, y, 10, 20),
                        "velocidade_x": 0,
                        "velocidade_y": 7
                    })

        return projeteis

    def levar_dano(self, dano):
        self.vida -= dano
        return self.vida <= 0

    def desenhar_barra_vida(self, surface):
        barra_largura = 80
        barra_altura = 8
        x = self.rect.centerx - barra_largura // 2
        y = self.rect.top - 15

        pygame.draw.rect(surface, (255, 0, 0), (x, y, barra_largura, barra_altura))
        vida_largura = int((self.vida / self.vida_maxima) * barra_largura)
        cor_vida = (0, 255, 0) if self.usar_lazer else (
        255, 255, 0)  # Verde para boss normal, amarelo para boss com lazer
        pygame.draw.rect(surface, cor_vida, (x, y, vida_largura, barra_altura))

    def desenhar_lazer(self, surface, jogador_rect):
        if not self.lazer_ativado:
            return False

        agora = pygame.time.get_ticks()
        tempo_decorrido = agora - self.lazer_tempo_inicio

        if tempo_decorrido > self.lazer_duracao:
            self.lazer_ativado = False
            return False

        # Criar um raio laser do boss até o jogador
        largura_lazer = 15
        cor_lazer = (255, 0, 0)  # Laser vermelho para o boss

        # Calcular direção do laser
        start_pos = (self.rect.centerx, self.rect.bottom)
        end_pos = (jogador_rect.centerx, jogador_rect.top)

        # Desenhar linha do laser
        pygame.draw.line(surface, cor_lazer, start_pos, end_pos, largura_lazer)

        # Efeito de brilho
        for i in range(3):
            cor_brilho = (255, 100 - i * 30, 100 - i * 30)
            pygame.draw.line(surface, cor_brilho, start_pos, end_pos, largura_lazer - i * 3)

        # Partículas no laser
        for _ in range(8):
            progresso = random.uniform(0, 1)
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * progresso
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * progresso
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            pygame.draw.circle(surface, (255, 255, 200), (int(x) + offset_x, int(y) + offset_y), 2)

        # Verificar colisão com jogador
        laser_rect = pygame.Rect(
            min(start_pos[0], end_pos[0]) - largura_lazer // 2,
            min(start_pos[1], end_pos[1]) - largura_lazer // 2,
            abs(end_pos[0] - start_pos[0]) + largura_lazer,
            abs(end_pos[1] - start_pos[1]) + largura_lazer
        )

        if laser_rect.colliderect(jogador_rect):
            return True  # Indica que o jogador foi atingido

        return False


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

# ---- carregar sprites ------
naves_arquivos = [
    "nave_azulroxo3.gif",
    "nave_laranja3.gif",
    "nave_rosa2.gif",
    "nave_verde3.gif",
    "nave_vermelho1.gif",
    "nave_vermelho3.gif"
]

naves_existentes = [nave for nave in naves_arquivos if nave in arquivos_disponiveis]
if not naves_existentes:
    naves_existentes = [arquivos_disponiveis[0]] if arquivos_disponiveis else ["placeholder"]

naves_animadas = []
for nave_arquivo in naves_existentes:
    naves_animadas.append(SpriteAnimado([nave_arquivo], (40, 40), 200))

# Meteoro - criar diferentes tamanhos
tamanho_meteoro_normal = 60
tamanho_meteoro_grande = 80

if "meteoro.gif" in arquivos_disponiveis:
    meteoro_animado_normal = SpriteAnimado(["meteoro.gif"], (tamanho_meteoro_normal, tamanho_meteoro_normal), 150)
    meteoro_animado_grande = SpriteAnimado(["meteoro.gif"], (tamanho_meteoro_grande, tamanho_meteoro_grande), 150)
else:
    meteoro_animado_normal = SpriteAnimado([naves_existentes[0]], (tamanho_meteoro_normal, tamanho_meteoro_normal), 150)
    meteoro_animado_grande = SpriteAnimado([naves_existentes[0]], (tamanho_meteoro_grande, tamanho_meteoro_grande), 150)

# Projétil do jogador
if "projetil_base.gif" in arquivos_disponiveis:
    projetil_animado = SpriteAnimado(["projetil_base.gif"], (15, 25), 100)
else:
    projetil_animado = SpriteAnimado([naves_existentes[0]], (15, 25), 100)

# Projétil do boss
if "projetil_boss.gif" in arquivos_disponiveis:
    projetil_boss_animado = SpriteAnimado(["projetil_boss.gif"], (15, 25), 100)
else:
    projetil_boss_animado = SpriteAnimado([naves_existentes[0]], (15, 25), 100)

# Boss
if "nave_boss.gif" in arquivos_disponiveis:
    boss_animado = SpriteAnimado(["nave_boss.gif"], (70, 70), 200)
else:
    boss_animado = SpriteAnimado([naves_existentes[0]], (70, 70), 200)

# Coração
if "coracao.png" in arquivos_disponiveis:
    coracao_img = pygame.transform.scale(pygame.image.load(os.path.join(caminho_imagens, "coracao.png")), (30, 30))
else:
    coracao_img = pygame.Surface((30, 30))
    coracao_img.fill((255, 0, 0))

# Portal
if "portal.gif" in arquivos_disponiveis:
    portal_animado = SpriteAnimado(["portal.gif"], (60, 60), 150)
else:
    portal_animado = SpriteAnimado([naves_existentes[0]], (60, 60), 150)

# Variáveis globais do jogo
jogador = pygame.Rect(180, 500, 40, 40)
nave_selecionada = 0
velocidade = 5
meteoros = []
projeteis = []
projeteis_boss = []
explosoes = []
bosses = []  # Agora usamos lista de bosses
boss_ativo = False
ultimo_boss_derrotado = 0  # Nível do último boss derrotado
coracoes = []
portais = []
ultimo_coracao = pygame.time.get_ticks()
intervalo_coracoes = 15000
ultimo_portal = pygame.time.get_ticks()
intervalo_portais = 30000


def criar_meteoro():
    # A partir do nível 5, alguns meteoros serão maiores e se moverão lateralmente
    if nivel >= 5 and random.random() < 0.4:  # 40% de chance de meteoro especial
        tamanho = tamanho_meteoro_grande
        velocidade_x = random.uniform(-2, 2)  # Movimento lateral
        velocidade_y = velocidade_base + (nivel * 1.2)
        rotacao_speed = random.uniform(-2, 2)
        x = random.randint(0, largura - tamanho)
        rect = pygame.Rect(x, -tamanho, tamanho, tamanho)
        return {
            "rect": rect,
            "velocidade_y": velocidade_y,
            "velocidade_x": velocidade_x,
            "rotacao": 0,
            "rotacao_speed": rotacao_speed,
            "grande": True,
            "congelado": False,
            "congelado_tempo": 0
        }
    else:
        # Meteoro normal
        tamanho = tamanho_meteoro_normal
        x = random.randint(0, largura - tamanho)
        rect = pygame.Rect(x, -tamanho, tamanho, tamanho)
        velocidade_y = velocidade_base + (nivel * 1.2)
        rotacao_speed = random.uniform(-2, 2)
        return {
            "rect": rect,
            "velocidade_y": velocidade_y,
            "velocidade_x": 0,  # Sem movimento lateral
            "rotacao": 0,
            "rotacao_speed": rotacao_speed,
            "grande": False,
            "congelado": False,
            "congelado_tempo": 0
        }


def criar_projetil():
    if municao_atual > 0 and not recarregando:
        x = jogador.centerx - 7
        y = jogador.top
        return {"rect": pygame.Rect(x, y, 15, 25), "rotacao": 0}
    return None


def criar_projeteis_triplo():
    projeteis = []
    if municao_atual > 0 and not recarregando:
        # Tiro central
        projeteis.append({"rect": pygame.Rect(jogador.centerx - 7, jogador.top, 15, 25), "rotacao": 0})
        # Tiro esquerdo
        projeteis.append({"rect": pygame.Rect(jogador.centerx - 20, jogador.top, 15, 25), "rotacao": -10})
        # Tiro direito
        projeteis.append({"rect": pygame.Rect(jogador.centerx + 6, jogador.top, 15, 25), "rotacao": 10})
    return projeteis


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


# =============================================
# SISTEMA DE HABILIDADES ESPECIAIS ATUALIZADO
# =============================================

def ativar_habilidade():
    global habilidade_cooldown, habilidade_duracao, habilidade_ativa
    global meteoros_congelados, escudo_ativo, escudo_tempo_fim
    global tiro_triplo_ativo, tiro_triplo_contador
    global velocidade_dupla_ativa, velocidade_dupla_tempo_fim
    global vida_jogador

    agora = pygame.time.get_ticks()
    nave_idx = nave_selecionada

    # Verificar se a habilidade está em cooldown
    if agora - habilidade_cooldown[nave_idx] < get_cooldown_habilidade(nave_idx):
        return False

    # Ativar habilidade baseada na nave selecionada
    if nave_idx == 0:  # Nave Azul-Roxo - Campo de Congelamento
        habilidade_ativa[0] = True
        habilidade_duracao[0] = agora + 3000  # 3 segundos

        # Congelar todos os meteoros atuais
        for meteoro in meteoros[:]:
            if not meteoro["congelado"]:
                meteoro["congelado"] = True
                meteoro["congelado_tempo"] = agora + 3000
                meteoros_congelados.append(meteoro)

        print("Campo de Congelamento ativado!")

    elif nave_idx == 1:  # Nave Laranja - Escudo de Plasma
        escudo_ativo = True
        escudo_tempo_fim = agora + 5000  # 5 segundos
        habilidade_ativa[1] = True
        habilidade_duracao[1] = agora + 5000
        print("Escudo de Plasma ativado!")

    elif nave_idx == 2:  # Nave Rosa - Teletransporte Quântico
        # Teleportar para posição aleatória segura
        nova_x = random.randint(40, largura - 40)
        nova_y = random.randint(300, 500)
        jogador.x = nova_x
        jogador.y = nova_y

        # Criar efeito de teletransporte
        explosoes.append(criar_explosao(jogador.centerx, jogador.centery, 60))
        habilidade_ativa[2] = True
        print("Teletransporte Quântico ativado!")

    elif nave_idx == 3:  # Nave Verde - Cura Regenerativa
        if vida_jogador < max_vida:
            vida_jogador += 1
            print("Vida recuperada!")
        else:
            # Se já estiver com vida máxima, ativa escudo temporário
            escudo_ativo = True
            escudo_tempo_fim = agora + 3000  # 3 segundos
            print("Escudo temporário ativado!")

        habilidade_ativa[3] = True
        explosoes.append(criar_explosao(jogador.centerx, jogador.centery, 40))

    elif nave_idx == 4:  # Nave Vermelha 1 - Rajada Tripla
        tiro_triplo_ativo = True
        tiro_triplo_contador = 10  # 10 tiros triplos
        habilidade_ativa[4] = True
        print("Rajada Tripla ativada! Próximos 10 tiros serão triplos!")

    elif nave_idx == 5:  # Nave Vermelha 3 - Super Velocidade
        velocidade_dupla_ativa = True
        velocidade_dupla_tempo_fim = agora + 4000  # 4 segundos
        habilidade_ativa[5] = True
        habilidade_duracao[5] = agora + 4000
        print("Super Velocidade ativada!")

    # Atualizar cooldown
    habilidade_cooldown[nave_idx] = agora
    return True


def get_cooldown_habilidade(nave_idx):
    cooldowns = [15000, 20000, 10000, 30000, 25000, 12000]  # Cooldowns em milissegundos
    return cooldowns[nave_idx]


def get_nome_habilidade(nave_idx):
    nomes = [
        "Campo de Congelamento (Q)",
        "Escudo de Plasma (W)",
        "Teletransporte (E)",
        "Cura Regenerativa (R)",
        "Rajada Tripla (T)",
        "Super Velocidade (Y)"
    ]
    return nomes[nave_idx]


def atualizar_habilidades():
    global meteoros_congelados, escudo_ativo, tiro_triplo_ativo, tiro_triplo_contador, velocidade_dupla_ativa
    global habilidade_ativa, habilidade_duracao

    agora = pygame.time.get_ticks()

    # Atualizar estado das habilidades
    for i in range(6):
        if habilidade_ativa[i] and agora > habilidade_duracao[i]:
            habilidade_ativa[i] = False

    # Congelamento (Nave 0)
    if habilidade_ativa[0]:
        # Atualizar meteoros congelados e remover os que foram destruídos
        for meteoro in meteoros_congelados[:]:
            if meteoro not in meteoros:  # Se o meteoro foi destruído
                meteoros_congelados.remove(meteoro)
            elif agora > meteoro["congelado_tempo"]:
                meteoro["congelado"] = False
                meteoros_congelados.remove(meteoro)
    else:
        # Descongelar todos se a habilidade acabou
        for meteoro in meteoros_congelados:
            if meteoro in meteoros:  # Só descongelar se ainda existir
                meteoro["congelado"] = False
        meteoros_congelados.clear()

    # Escudo (Nave 1)
    if escudo_ativo and agora > escudo_tempo_fim:
        escudo_ativo = False

    # Rajada Tripla (Nave 4) - Agora baseada em contador
    if tiro_triplo_ativo and tiro_triplo_contador <= 0:
        tiro_triplo_ativo = False

    # Super Velocidade (Nave 5)
    if velocidade_dupla_ativa and agora > velocidade_dupla_tempo_fim:
        velocidade_dupla_ativa = False


def desenhar_escudo(surface):
    if escudo_ativo:
        # Desenhar escudo pulsante
        tempo = pygame.time.get_ticks()
        raio = 30 + int(5 * math.sin(tempo / 200))

        # Escudo laranja com gradiente
        for i in range(3):
            cor_escudo = (255, 165 - i * 20, 0)
            pygame.draw.circle(surface, cor_escudo, jogador.center, raio - i * 5, 2)

        # Partículas de energia
        for _ in range(8):
            angulo = random.uniform(0, 6.28)
            distancia = raio - 5
            x = jogador.centerx + int(distancia * math.cos(angulo))
            y = jogador.centery + int(distancia * math.sin(angulo))
            pygame.draw.circle(surface, (255, 255, 100), (x, y), 2)


def desenhar_meteoros_congelados(surface):
    for meteoro in meteoros_congelados:
        if meteoro["congelado"] and meteoro in meteoros:  # Só desenhar se ainda existir
            # Desenhar aura de gelo ao redor do meteoro
            rect = meteoro["rect"]
            pygame.draw.circle(surface, (100, 200, 255), rect.center, rect.width // 2 + 5, 2)

            # Partículas de gelo
            for _ in range(3):
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)
                x = rect.centerx + offset_x
                y = rect.centery + offset_y
                pygame.draw.circle(surface, (200, 230, 255), (x, y), 2)


def desenhar_efeito_velocidade(surface):
    if velocidade_dupla_ativa:
        # Desenhar rastro de velocidade
        for i in range(3):
            offset = (i + 1) * 8
            cor = (255, 50 + i * 20, 50 + i * 20)
            rect_rastro = pygame.Rect(jogador.x, jogador.y + offset, jogador.width, jogador.height)
            pygame.draw.rect(surface, cor, rect_rastro, 2)


def ativar_lazer():
    global lazer_ativado, lazer_tempo_inicio, ultimo_lazer, lazer_carregando, lazer_carregamento_tempo

    agora = pygame.time.get_ticks()

    if not lazer_ativado and not lazer_carregando and agora - ultimo_lazer > lazer_cooldown:
        lazer_carregando = True
        lazer_carregamento_tempo = agora
        lazer_tempo_inicio = 0  # Inicializar a variável


def desenhar_lazer(surface):
    global lazer_ativado, lazer_carregando, bosses, pontuacao, lazer_tempo_inicio, ultimo_lazer

    if not lazer_ativado and not lazer_carregando:
        return

    agora = pygame.time.get_ticks()

    # Efeito de carregamento
    if lazer_carregando:
        tempo_carregamento = agora - lazer_carregamento_tempo
        progresso = min(tempo_carregamento / 1000, 1.0)  # 1 segundo de carregamento

        # Desenhar barra de carregamento acima da nave
        barra_largura = 40
        barra_altura = 5
        x = jogador.centerx - barra_largura // 2
        y = jogador.top - 10

        pygame.draw.rect(surface, (100, 100, 100), (x, y, barra_largura, barra_altura))
        pygame.draw.rect(surface, (0, 255, 255), (x, y, int(barra_largura * progresso), barra_altura))

        if progresso >= 1.0:
            lazer_carregando = False
            lazer_ativado = True
            lazer_tempo_inicio = agora

    # Efeito do lazer ativo
    if lazer_ativado:
        tempo_decorrido = agora - lazer_tempo_inicio
        progresso = min(tempo_decorrido / lazer_duracao, 1.0)

        # Criar um raio laser que vai da nave até o topo da tela
        largura_lazer = 20 + int(10 * math.sin(tempo_decorrido / 50))  # Efeito pulsante

        # Cor do laser (azul ciano)
        cor_base = (0, 200, 255)
        cor_brilho = (100, 255, 255)

        # Desenhar o laser principal
        rect_lazer = pygame.Rect(
            jogador.centerx - largura_lazer // 2,
            0,
            largura_lazer,
            jogador.top
        )

        # Gradiente do laser
        for i in range(largura_lazer):
            intensidade = 0.5 + 0.5 * math.sin((tempo_decorrido + i * 10) / 30)
            cor = (
                int(cor_base[0] * intensidade),
                int(cor_base[1] * intensidade),
                int(cor_base[2] * intensidade)
            )
            pygame.draw.line(
                surface,
                cor,
                (rect_lazer.x + i, rect_lazer.y),
                (rect_lazer.x + i, rect_lazer.bottom),
                1
            )

        # Brilho central
        pygame.draw.rect(surface, cor_brilho, rect_lazer, 2)

        # Partículas no laser
        for _ in range(5):
            x = random.randint(rect_lazer.left, rect_lazer.right)
            y = random.randint(rect_lazer.top, rect_lazer.bottom)
            raio = random.randint(2, 5)
            pygame.draw.circle(surface, (255, 255, 200), (x, y), raio)

        # Efeito de partículas na base do laser
        for _ in range(10):
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-5, 5)
            x = jogador.centerx + offset_x
            y = jogador.top + offset_y
            raio = random.randint(1, 3)
            pygame.draw.circle(surface, (255, 255, 200), (x, y), raio)

        # Verificar colisões com o laser
        if lazer_ativado:
            # Destruir meteoros no caminho do laser
            for meteoro in meteoros[:]:
                if (meteoro["rect"].colliderect(rect_lazer) or
                        meteoro["rect"].colliderect(
                            pygame.Rect(rect_lazer.x - 5, rect_lazer.y, rect_lazer.width + 10, rect_lazer.height))):
                    explosoes.append(criar_explosao(meteoro["rect"].centerx, meteoro["rect"].centery, 70))
                    meteoros.remove(meteoro)
                    pontuacao += 50

            # Destruir projéteis do boss no caminho do laser
            for projetil in projeteis_boss[:]:
                if projetil["rect"].colliderect(rect_lazer):
                    explosoes.append(criar_explosao(projetil["rect"].centerx, projetil["rect"].centery, 30))
                    projeteis_boss.remove(projetil)

            # Dar dano nos bosses
            for boss in bosses[:]:
                if boss.rect.colliderect(rect_lazer):
                    explosoes.append(criar_explosao(boss.rect.centerx, boss.rect.centery, 40))
                    if boss.levar_dano(5):  # Dano contínuo no boss
                        explosoes.append(criar_explosao(boss.rect.centerx, boss.rect.centery, 100))
                        pontuacao += 500
                        bosses.remove(boss)

        # Desativar laser após a duração
        if progresso >= 1.0:
            lazer_ativado = False
            ultimo_lazer = agora


def atualizar_municao():
    global municao_atual, recarregando, tempo_inicio_recarga

    agora = pygame.time.get_ticks()

    # Iniciar recarga se a munição acabou
    if municao_atual <= 0 and not recarregando:
        recarregando = True
        tempo_inicio_recarga = agora

    # Recarregar munição após 10 segundos
    if recarregando:
        tempo_recarga = agora - tempo_inicio_recarga
        if tempo_recarga >= intervalo_recarga:
            municao_atual = municao_maxima
            recarregando = False


def criar_bosses(nivel_boss):
    global bosses, boss_ativo

    bosses.clear()

    if nivel_boss >= 10:
        # Dois bosses para níveis 10+
        boss1_x = largura // 3 - 35
        boss2_x = 2 * largura // 3 - 35

        # Um boss normal e um com lazer
        bosses.append(Boss(nivel_boss, boss1_x, usar_lazer=False))
        bosses.append(Boss(nivel_boss, boss2_x, usar_lazer=True))
        print(f"DOIS BOSSES apareceram! Nível {nivel_boss} - Um deles usa LAZER!")
    else:
        # Um boss normal para níveis abaixo de 10
        boss_x = largura // 2 - 35
        bosses.append(Boss(nivel_boss, boss_x, usar_lazer=False))
        print(f"BOSS apareceu! Nível {nivel_boss}")

    boss_ativo = True


def avancar_nivel(quantidade):
    global nivel, pontuacao, boss_ativo
    nivel_anterior = nivel
    nivel += quantidade
    pontuacao += quantidade * 200

    for i in range(nivel_anterior + 1, nivel + 1):
        if i % 5 == 0 and not boss_ativo and len(bosses) == 0 and i > ultimo_boss_derrotado:
            criar_bosses(i)
            break


def atualizar_nivel():
    global nivel, boss_ativo, ultimo_boss_derrotado
    novo_nivel = max(1, pontuacao // 300 + 1)

    if novo_nivel > nivel:
        nivel = novo_nivel

    # CORREÇÃO: Só spawna boss se for um nível múltiplo de 5 E maior que o último boss derrotado
    if nivel % 5 == 0 and not boss_ativo and len(bosses) == 0 and nivel > ultimo_boss_derrotado:
        criar_bosses(nivel)


def atualizar_pontuacao():
    global pontuacao, tempo_atual
    tempo_atual = (pygame.time.get_ticks() - tempo_inicio) // 1000
    pontuacao = tempo_atual * 15
    atualizar_nivel()


def desenhar_vidas():
    for i in range(vida_jogador):
        x = largura - 40 - (i * 35)
        y = 10
        tela.blit(coracao_img, (x, y))


def desenhar_interface():
    texto_pontuacao = fonte.render(f'Pontos: {pontuacao}', True, (255, 255, 255))
    tela.blit(texto_pontuacao, (10, 10))

    minutos = tempo_atual // 60
    segundos = tempo_atual % 60
    texto_tempo = fonte.render(f'Tempo: {minutos:02d}:{segundos:02d}', True, (255, 255, 255))
    tela.blit(texto_tempo, (10, 50))

    texto_nivel = fonte.render(f'Nível: {nivel}', True, (255, 255, 255))
    tela.blit(texto_nivel, (10, 90))

    texto_nave = fonte.render(f'Nave: {nave_selecionada + 1}', True, (255, 255, 255))
    tela.blit(texto_nave, (10, 130))

    # Mostrar munição
    if recarregando:
        tempo_restante = max(0, intervalo_recarga - (pygame.time.get_ticks() - tempo_inicio_recarga))
        segundos_restantes = tempo_restante // 1000
        texto_municao = fonte.render(f'Recarregando: {segundos_restantes}s', True, (255, 200, 0))
    else:
        texto_municao = fonte.render(f'Munição: {municao_atual}/{municao_maxima}', True, (255, 255, 255))
    tela.blit(texto_municao, (10, 170))

    # Mostrar habilidade atual e cooldown
    agora = pygame.time.get_ticks()
    cooldown_restante = max(0,
                            get_cooldown_habilidade(nave_selecionada) - (agora - habilidade_cooldown[nave_selecionada]))
    segundos_cooldown = cooldown_restante // 1000

    nome_habilidade = get_nome_habilidade(nave_selecionada)

    # Mostrar contador de tiros triplos se for a nave 4
    if nave_selecionada == 4 and tiro_triplo_ativo:
        texto_habilidade = fonte_pequena.render(f'Rajada: {tiro_triplo_contador} tiros', True, (255, 255, 0))
    elif cooldown_restante > 0:
        texto_habilidade = fonte_pequena.render(f'{nome_habilidade}: {segundos_cooldown}s', True, (200, 200, 200))
    else:
        texto_habilidade = fonte_pequena.render(f'{nome_habilidade}: PRONTO', True, (0, 255, 0))

    tela.blit(texto_habilidade, (10, 200))

    desenhar_vidas()

    if boss_ativo:
        texto_boss = fonte.render('BOSS!', True, (255, 0, 0))
        tela.blit(texto_boss, (largura - 100, 10))

        # Mostrar quantidade de bosses
        if len(bosses) > 1:
            texto_boss_count = fonte_pequena.render(f'Bosses: {len(bosses)}', True, (255, 255, 255))
            tela.blit(texto_boss_count, (largura - 120, 40))

    # Mostrar cooldown do lazer
    cooldown_restante_lazer = max(0, lazer_cooldown - (agora - ultimo_lazer))
    segundos_cooldown_lazer = cooldown_restante_lazer // 1000

    if cooldown_restante_lazer > 0:
        texto_lazer = fonte_pequena.render(f'Lazer: {segundos_cooldown_lazer}s', True, (200, 200, 200))
    else:
        texto_lazer = fonte_pequena.render('Lazer: PRONTO (L)', True, (0, 255, 255))

    tela.blit(texto_lazer, (largura - 150, altura - 60))

    texto_instrucoes = fonte_pequena.render('1-6: Trocar nave | ESPACO: Atirar | L: Lazer', True, (200, 200, 200))
    tela.blit(texto_instrucoes, (10, altura - 90))
    texto_instrucoes2 = fonte_pequena.render('Q/W/E/R/T/Y: Habilidades especiais', True, (200, 200, 200))
    tela.blit(texto_instrucoes2, (10, altura - 60))
    texto_instrucoes3 = fonte_pequena.render('R: Reiniciar', True, (200, 200, 200))
    tela.blit(texto_instrucoes3, (10, altura - 30))


def trocar_nave(numero):
    global nave_selecionada
    if 0 <= numero - 1 < len(naves_animadas):
        nave_selecionada = numero - 1


def rotacionar_imagem(imagem, angulo):
    return pygame.transform.rotate(imagem, angulo)


rodando = True
game_over = False

while rodando:
    tela.fill((0, 0, 40))

    for i in range(50):
        x = random.randint(0, largura)
        y = random.randint(0, altura)
        pygame.draw.circle(tela, (255, 255, 255), (x, y), 1)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_1 and len(naves_animadas) >= 1:
                trocar_nave(1)
            elif evento.key == pygame.K_2 and len(naves_animadas) >= 2:
                trocar_nave(2)
            elif evento.key == pygame.K_3 and len(naves_animadas) >= 3:
                trocar_nave(3)
            elif evento.key == pygame.K_4 and len(naves_animadas) >= 4:
                trocar_nave(4)
            elif evento.key == pygame.K_5 and len(naves_animadas) >= 5:
                trocar_nave(5)
            elif evento.key == pygame.K_6 and len(naves_animadas) >= 6:
                trocar_nave(6)
            elif evento.key == pygame.K_SPACE and not game_over:
                if tiro_triplo_ativo:
                    # Criar 3 projéteis em leque
                    novos_projeteis = criar_projeteis_triplo()
                    for projetil in novos_projeteis:
                        projeteis.append(projetil)
                    municao_atual -= 1
                    tiro_triplo_contador -= 1
                    if tiro_triplo_contador <= 0:
                        tiro_triplo_ativo = False
                        print("Rajada Tripla acabou!")
                else:
                    # Tiro normal
                    novo_projetil = criar_projetil()
                    if novo_projetil is not None:
                        projeteis.append(novo_projetil)
                        municao_atual -= 1
            elif evento.key == pygame.K_l and not game_over:
                ativar_lazer()
            elif evento.key == pygame.K_q and not game_over:  # Habilidade Nave 0
                ativar_habilidade()
            elif evento.key == pygame.K_w and not game_over:  # Habilidade Nave 1
                ativar_habilidade()
            elif evento.key == pygame.K_e and not game_over:  # Habilidade Nave 2
                ativar_habilidade()
            elif evento.key == pygame.K_r and not game_over:  # Habilidade Nave 3
                ativar_habilidade()
            elif evento.key == pygame.K_t and not game_over:  # Habilidade Nave 4
                ativar_habilidade()
            elif evento.key == pygame.K_y and not game_over:  # Habilidade Nave 5
                ativar_habilidade()
            elif evento.key == pygame.K_r and game_over:
                # Reiniciar jogo
                jogador = pygame.Rect(180, 500, 40, 40)
                meteoros = []
                projeteis = []
                projeteis_boss = []
                explosoes = []
                coracoes = []
                portais = []
                bosses = []
                boss_ativo = False
                pontuacao = 0
                nivel = 1
                vida_jogador = 3
                municao_atual = municao_maxima
                recarregando = False
                lazer_ativado = False
                lazer_carregando = False
                ultimo_lazer = 0
                # Resetar habilidades
                habilidade_cooldown = [0, 0, 0, 0, 0, 0]
                habilidade_duracao = [0, 0, 0, 0, 0, 0]
                habilidade_ativa = [False, False, False, False, False, False]
                meteoros_congelados = []
                escudo_ativo = False
                tiro_triplo_ativo = False
                tiro_triplo_contador = 0
                velocidade_dupla_ativa = False
                tempo_inicio = pygame.time.get_ticks()
                ultimo_boss_derrotado = 0
                game_over = False

    if naves_animadas:
        naves_animadas[nave_selecionada].atualizar()
    meteoro_animado_normal.atualizar()
    meteoro_animado_grande.atualizar()
    projetil_animado.atualizar()
    projetil_boss_animado.atualizar()
    portal_animado.atualizar()

    # Atualizar bosses
    for boss in bosses[:]:
        boss_animado.atualizar()
        boss.atualizar(jogador)

        if boss.pode_atirar():
            novos_projeteis = boss.atirar(jogador)
            projeteis_boss.extend(novos_projeteis)

        # Boss com lazer pode ativar lazer
        if boss.usar_lazer and random.random() < 0.02:  # 2% de chance por frame
            boss.ativar_lazer()

        # Desenhar e verificar colisão do lazer do boss
        if boss.desenhar_lazer(tela, jogador):
            # Jogador foi atingido pelo lazer do boss
            if not escudo_ativo:
                explosoes.append(criar_explosao(jogador.centerx, jogador.centery, 60))
                vida_jogador -= 2  # Dano maior do lazer do boss
                if vida_jogador <= 0:
                    game_over = True

    agora = pygame.time.get_ticks()
    if agora - ultimo_coracao > intervalo_coracoes and len(coracoes) < 3:
        coracoes.append(criar_coracao())
        ultimo_coracao = agora

    if agora - ultimo_portal > intervalo_portais and len(portais) < 1 and not boss_ativo:
        portais.append(criar_portal())
        ultimo_portal = agora

    # Atualizar sistemas
    atualizar_municao()
    atualizar_habilidades()

    if not game_over:
        # Calcular velocidade baseada na habilidade
        velocidade_atual = velocidade * 2 if velocidade_dupla_ativa else velocidade

        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT] and jogador.left > 0:
            jogador.x -= velocidade_atual
        if teclas[pygame.K_RIGHT] and jogador.right < largura:
            jogador.x += velocidade_atual
        if teclas[pygame.K_UP] and jogador.top > 0:
            jogador.y -= velocidade_atual
        if teclas[pygame.K_DOWN] and jogador.bottom < altura:
            jogador.y += velocidade_atual

        if not boss_ativo and random.randint(1, max(5, 60 - nivel * 3)) == 1:
            meteoros.append(criar_meteoro())

        for meteoro in meteoros[:]:
            # Só mover se não estiver congelado
            if not meteoro["congelado"]:
                meteoro["rect"].y += meteoro["velocidade_y"]
                meteoro["rect"].x += meteoro["velocidade_x"]
                meteoro["rotacao"] += meteoro["rotacao_speed"]

                # Fazer meteoros quicarem nas paredes laterais
                if meteoro["rect"].left <= 0 or meteoro["rect"].right >= largura:
                    meteoro["velocidade_x"] *= -1

            # Verificar colisão com jogador (ignorar se escudo ativo)
            if meteoro["rect"].colliderect(jogador):
                if not escudo_ativo:
                    explosoes.append(criar_explosao(meteoro["rect"].centerx, meteoro["rect"].centery, 70))
                    vida_jogador -= 1
                    if vida_jogador <= 0:
                        game_over = True
                else:
                    # Destruir meteoro se escudo ativo
                    explosoes.append(criar_explosao(meteoro["rect"].centerx, meteoro["rect"].centery, 50))
                    pontuacao += 25

                if meteoro in meteoros:
                    meteoros.remove(meteoro)

            # Escolher a imagem correta baseada no tamanho do meteoro
            if meteoro["grande"]:
                meteoro_img_rotacionada = rotacionar_imagem(meteoro_animado_grande.get_imagem(), meteoro["rotacao"])
            else:
                meteoro_img_rotacionada = rotacionar_imagem(meteoro_animado_normal.get_imagem(), meteoro["rotacao"])

            tela.blit(meteoro_img_rotacionada, meteoro["rect"])

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

        # CORREÇÃO: Usar uma lista auxiliar para remover projéteis
        projeteis_a_remover = []

        for projetil in projeteis[:]:
            # Aumentar velocidade do projétil se habilidade de velocidade ativa
            velocidade_projetil = 15 if velocidade_dupla_ativa else 10
            projetil["rect"].y -= velocidade_projetil
            projetil["rotacao"] += 5

            # Verificar colisão com meteoros
            for meteoro in meteoros[:]:
                if projetil["rect"].colliderect(meteoro["rect"]):
                    explosoes.append(criar_explosao(meteoro["rect"].centerx, meteoro["rect"].centery, 70))
                    projeteis_a_remover.append(projetil)
                    if meteoro in meteoros:
                        meteoros.remove(meteoro)
                    pontuacao += 50
                    break

            # Verificar colisão com bosses
            for boss in bosses[:]:
                if projetil["rect"].colliderect(boss.rect):
                    explosoes.append(criar_explosao(projetil["rect"].centerx, projetil["rect"].centery, 30))
                    projeteis_a_remover.append(projetil)
                    if boss.levar_dano(10):
                        explosoes.append(criar_explosao(boss.rect.centerx, boss.rect.centery, 100))
                        pontuacao += 500
                        # CORREÇÃO: Registrar que este boss foi derrotado
                        ultimo_boss_derrotado = boss.nivel_boss
                        bosses.remove(boss)
                        if len(bosses) == 0:
                            boss_ativo = False
                    break

            # Verificar se saiu da tela
            if projetil["rect"].bottom < 0:
                projeteis_a_remover.append(projetil)
            else:
                projetil_img_rotacionada = rotacionar_imagem(projetil_animado.get_imagem(), projetil["rotacao"])
                tela.blit(projetil_img_rotacionada, projetil["rect"])

        # Remover projéteis marcados para remoção
        for projetil in projeteis_a_remover:
            if projetil in projeteis:
                projeteis.remove(projetil)

        for projetil in projeteis_boss[:]:
            # Atualizar movimento dos projéteis do boss
            projetil["rect"].x += projetil["velocidade_x"]
            projetil["rect"].y += projetil["velocidade_y"]

            if projetil["rect"].colliderect(jogador):
                if not escudo_ativo:
                    explosoes.append(criar_explosao(projetil["rect"].centerx, projetil["rect"].centery, 40))
                    projeteis_boss.remove(projetil)
                    vida_jogador -= 1
                    if vida_jogador <= 0:
                        game_over = True
                else:
                    # Destruir projétil se escudo ativo
                    explosoes.append(criar_explosao(projetil["rect"].centerx, projetil["rect"].centery, 20))
                    projeteis_boss.remove(projetil)
                    pontuacao += 10

            elif (projetil["rect"].top > altura or
                  projetil["rect"].left < 0 or
                  projetil["rect"].right > largura):
                projeteis_boss.remove(projetil)
            else:
                tela.blit(projetil_boss_animado.get_imagem(), projetil["rect"])

        # Remover meteoros que saíram da tela
        meteoros = [meteoro for meteoro in meteoros if meteoro["rect"].y < altura]

    # Desenhar efeitos visuais das habilidades
    desenhar_meteoros_congelados(tela)
    desenhar_escudo(tela)
    desenhar_efeito_velocidade(tela)

    # Desenhar e atualizar lazer
    desenhar_lazer(tela)

    # Desenhar bosses
    for boss in bosses:
        tela.blit(boss_animado.get_imagem(), boss.rect)
        boss.desenhar_barra_vida(tela)

    for explosao in explosoes[:]:
        tempo_decorrido = pygame.time.get_ticks() - explosao["tempo_inicio"]
        if tempo_decorrido > explosao["duracao"]:
            explosoes.remove(explosao)
        else:
            desenhar_explosao(tela, explosao)

    atualizar_pontuacao()
    desenhar_interface()

    if not game_over and naves_animadas:
        tela.blit(naves_animadas[nave_selecionada].get_imagem(), jogador)
    elif game_over:
        texto_gameover = fonte.render('GAME OVER', True, (255, 0, 0))
        texto_reiniciar = fonte.render('Pressione R para reiniciar', True, (255, 255, 255))
        tela.blit(texto_gameover, (largura // 2 - 80, altura // 2 - 50))
        tela.blit(texto_reiniciar, (largura // 2 - 150, altura // 2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
