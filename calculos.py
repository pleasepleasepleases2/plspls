import math
import globals
def calcular_progresso_evento(cursor, id_usuario, evento):
    cursor.execute("SELECT COUNT(*) FROM evento WHERE evento = %s", (evento,))
    total_cartas_evento = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM inventario inv
        JOIN evento ev ON inv.id_personagem = ev.id_personagem
        WHERE inv.id_usuario = %s AND ev.evento = %s
    """, (id_usuario, evento))
    cartas_usuario = cursor.fetchone()[0]

    if total_cartas_evento == 0:
        progresso = 0
    else:
        progresso = (cartas_usuario / total_cartas_evento) * 100

    barra_progresso = '█' * math.floor(progresso / 10) + '░' * (10 - math.floor(progresso / 10))
    return f"{barra_progresso} {progresso:.2f}%"

def gerar_id_unico():
    if "ultimo_id" not in globals.user_data:
        globals.user_data["ultimo_id"] = 0
    globals.user_data["ultimo_id"] += 1
    return globals.user_data["ultimo_id"]
