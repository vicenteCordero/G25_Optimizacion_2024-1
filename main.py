from gurobipy import Model, quicksum, GRB
import pandas as pd
import numpy as np


""" Constantes """
# definidas en bibliografía
CARGA_ESTANDAR = 0.75 # mínimo para considerar al vehículo cargado
CARGA_MAXIMA = 0.8 # máximo que debe cargarse la batería

CAPACIDAD_POTENCIA_MEDIA = 30 # capacidad de potencia promedio de un vehículo eléctrico
CARGA_MEDIA = 0.5 # carga promedio de un vehículo eléctrico cualquiera


I = 3 # tipos de cargadores distintos
HT = 8 # cantidad total de horas
M = 10 # cantidad de autos que llegan
D = 5 # días totales

# seed para los números generados
np.random.seed(0)


def main():
    tipos_cargadores = range(1, I + 1)
    horas_del_dia = range(1, HT + 1)
    automoviles_recibidos = range(1, M + 1)
    cantidad_dias = range(1, D + 1)


    # recolectados en archivos .csv
    energia_por_tipo = pd.read_csv("data/energia_por_tipo.csv", header=None)
    satisfaccion_por_tipo = pd.read_csv("data/satisfaccion.csv", header=None)
    costos_por_tipo = pd.read_csv("data/costos_por_tipo.csv", header=None)
    energia_total_edificio = pd.read_csv("data/energia_total_edificio.csv", header=None)
    cantidad_estacionamientos = pd.read_csv("data/cantidad_estacionamientos.csv", header=None)
    presupuesto = pd.read_csv("data/presupuesto.csv", header=None)


    # randomizados (explicación en el informe)
    capacidad_por_auto = np.around(np.random.normal(loc=CAPACIDAD_POTENCIA_MEDIA, scale=1, size=M), 2)

    carga_por_auto_dia = [np.around(np.random.normal(loc=CARGA_MEDIA*capacidad_por_auto[m - 1], scale=1, size=D), 2) for m in automoviles_recibidos]


    """ Parámetros """
    wc = {i: float(energia_por_tipo.iat[i - 1, 1]) for i in tipos_cargadores}
    wt = int(energia_total_edificio.iat[0, 0])
    c = {i: int(costos_por_tipo.iat[i - 1, 1]) for i in tipos_cargadores}
    n_et = int(cantidad_estacionamientos.iat[0, 0])
    p = int(presupuesto.iat[0, 0])
    cb = {m: capacidad_por_auto[m - 1] for m in automoviles_recibidos}
    w = {(m, d): carga_por_auto_dia[m - 1][d - 1] for m in automoviles_recibidos for d in cantidad_dias}
    h = {i: int(satisfaccion_por_tipo.iat[i - 1, 1]) for i in tipos_cargadores}

    # creación modelo
    model = Model()


    """ Variables """
    # número de estacionamientos del tipo i a instalar
    n_e = model.addVars(tipos_cargadores, vtype=GRB.INTEGER)
    
    # si al auto m se le asigna  un cargador de tipo i el día d
    x = model.addVars(automoviles_recibidos, tipos_cargadores, cantidad_dias,
                    vtype=GRB.BINARY)
    
    # si el auto m está cargando con cargador tipo i en la hora h el día d
    car = model.addVars(automoviles_recibidos, horas_del_dia, cantidad_dias, tipos_cargadores,
                    vtype=GRB.BINARY)
    
    # cantidad de horas que el auto m está cargando el día d con el cargador i
    t = model.addVars(automoviles_recibidos, cantidad_dias, tipos_cargadores,
                    vtype=GRB.CONTINUOUS)
    
    model.update()


    """ Restricciones """
    # cantidad instalados menor o igual a los totales disponibles
    model.addConstr((
        quicksum(n_e[i] for i in tipos_cargadores) <= n_et
    ), name="R1")

    
    # no se puede superar presupuesto
    model.addConstr((
        p >= quicksum(c[i] * n_e[i] for i in tipos_cargadores)
    ), name="R2")


    # potencia total consumida es menor o igual a la capacidad máx. del edificio
    model.addConstrs((
        wt >= quicksum(quicksum(car[m, h, d, i] * wc[i] for i in tipos_cargadores) for m in automoviles_recibidos)
        for h in horas_del_dia for d in cantidad_dias
    ), name="R3")


    # carga mínima de cada auto (carga estándar)
    model.addConstrs((
        quicksum(t[m, d, i] * wc[i] for i in tipos_cargadores) + w[m, d] >=
        CARGA_ESTANDAR * cb[m] for m in automoviles_recibidos for d in cantidad_dias
    ), name="R4")


    # cada vehículo se carga, a lo más, al 80% de su capacidad máxima de kW
    model.addConstrs((
        quicksum(x[m, i, d] for i in tipos_cargadores) <= (0.8 * cb[m])/w[m, d]
        for m in automoviles_recibidos for d in cantidad_dias
    ), name="R5")


    # definición de T_mid
    model.addConstrs((
        t[m, d, i] == (0.8 * cb[m] - w[m, d])/wc[i] * x[m, i, d]
        for i in tipos_cargadores for m in automoviles_recibidos for d in cantidad_dias
    ), name="R6")


    # el tiempo que un auto ocupa un estacionamiento
    # es al menos el necesario para una carga estándar
    model.addConstrs((
        quicksum(quicksum(car[m, h, d, i] for i in tipos_cargadores) for h in horas_del_dia) >=
        quicksum(t[m, d, i] for i in tipos_cargadores)
        for m in automoviles_recibidos for d in cantidad_dias
    ), name="R7")


    model.addConstrs((
        quicksum(quicksum(car[m, h, d, i] for i in tipos_cargadores) for h in horas_del_dia) <=
        quicksum(t[m, d, i] + 1 for i in tipos_cargadores)
        for m in automoviles_recibidos for d in cantidad_dias
    ), name="R8")


    # para que un auto m esté cargando con tipo i, debe estar en dicho estacionamiento
    model.addConstrs((
        x[m, i, d] >= car[m, h, d, i] for h in horas_del_dia for d in cantidad_dias
        for i in tipos_cargadores for m in automoviles_recibidos
    ), name="R9")


    # un auto solo puede tener un estacionamiento por día
    model.addConstrs((
        1 >= quicksum(x[m, i, d] for i in tipos_cargadores)
        for m in automoviles_recibidos for d in cantidad_dias
    ), name="R10")


    # La cantidad de autos que se cargan con cargador tipo i en cualquier día no puede superar
    # la cantidad de estacionamientos instalada de ese tipo
    model.addConstrs((
        n_e[i] >= quicksum(x[m, i, d] for m in automoviles_recibidos)
        for i in tipos_cargadores for d in cantidad_dias
    ), name="R11")



    # cantidad de estacionamientos es entero positivo
    model.addConstrs((
        n_e[i] >= 0 for i in tipos_cargadores
    ), name="R12")


    # tiempo de carga es real positivo
    model.addConstrs((
        t[m, d, i] >= 0
        for m in automoviles_recibidos for d in cantidad_dias for i in tipos_cargadores
    ), name="R13")

    

    """ Función Objetivo """
    f_obj = quicksum(
        quicksum(
            quicksum(
                h[i] * x[m, i, d] for i in tipos_cargadores
            ) for m in automoviles_recibidos
        ) for d in cantidad_dias
    )

    model.setObjective(f_obj, GRB.MAXIMIZE)
    model.optimize()


    """ GUARDAR VALORES """

    valor_optimo = model.ObjVal
    print(valor_optimo)

    data = {f"Cargador tipo {i}": [n_e[i].x] for i in tipos_cargadores}
    df_cargadores = pd.DataFrame(data=data)
    print(df_cargadores)




if __name__ == "__main__":
    main()