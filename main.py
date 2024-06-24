from gurobipy import Model, quicksum, GRB
import pandas as pd
import numpy as np
from datos import data_dict


""" Rangos constantes """

I = 3 # tipos de cargadores distintos
HT = 10 # cantidad total de horas
M = 100 # cantidad de autos que llegan al día
D = 10 # días totales

# seed para los números generados
np.random.seed(0)


def main():
    tipos_cargadores = range(1, I + 1)
    horas_del_dia = range(1, HT + 1)
    automoviles_recibidos = range(1, M + 1)
    cantidad_dias = range(1, D + 1)

    cantidad_estacionamientos: int = data_dict["cantidad_estacionamientos"]
    costos_por_tipo: dict = data_dict["costos_por_tipo"]
    energia_por_tipo: dict = data_dict["energia_por_tipo"]
    energia_total_edificio: int = data_dict["energia_total_edificio"]
    presupuesto: int = data_dict["presupuesto"]
    satisfaccion_por_tipo: dict = data_dict["satisfaccion"]

    # mínimo para considerar al vehículo cargado
    carga_estandar = data_dict["carga_estandar"]
    
    # capacidad de potencia promedio de un vehículo eléctrico
    capacidad_potencia_media = data_dict["capacidad_potencia_media"]
    
    # carga promedio de un vehículo eléctrico cualquiera
    carga_media = data_dict["carga_media"]

    
    # randomizados (explicación en el informe)
    capacidad_por_auto = np.around(np.random.normal(loc=capacidad_potencia_media, scale=1, size=M), 2)

    carga_por_auto_dia = [np.around(np.random.normal(loc=carga_media*capacidad_por_auto[m - 1], scale=1, size=D), 2) for m in automoviles_recibidos]


    """ Parámetros """
    wc = {i: float(energia_por_tipo[str(i)]) for i in tipos_cargadores}
    wt = energia_total_edificio
    c = {i: int(costos_por_tipo[str(i)]) for i in tipos_cargadores}
    n_et = cantidad_estacionamientos
    p = presupuesto
    cb = {m: capacidad_por_auto[m - 1] for m in automoviles_recibidos}
    w = {(m, d): carga_por_auto_dia[m - 1][d - 1] for m in automoviles_recibidos for d in cantidad_dias}
    h = {i: int(satisfaccion_por_tipo[str(i)]) for i in tipos_cargadores}

    # creación modelo
    model = Model()


    """ Variables """
    # número de estacionamientos del tipo i a instalar
    n_e = model.addVars(tipos_cargadores, vtype=GRB.INTEGER)
    
    # si al auto m se le asigna un cargador de tipo i el día d
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
        carga_estandar * cb[m] for m in automoviles_recibidos for d in cantidad_dias
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
    print(f"\n\nValor óptimo: {valor_optimo}\n")


    with pd.ExcelWriter('resultados.xlsx', engine='xlsxwriter') as writer:
        df_valor_opt = pd.DataFrame(data=[f"{valor_optimo}"])
        df_valor_opt.to_excel(writer, sheet_name='Valor Óptimo')
        
        # cargadores por tipo
        data_cargadores = {f"Cargador tipo {i}": [n_e[i].x] for i in tipos_cargadores}
        df_cargadores = pd.DataFrame(data=data_cargadores)
        print(f"Cargadores instalados de cada tipo:\n{df_cargadores}\n")
        df_cargadores.to_excel(writer, sheet_name='Cargadores de cada tipo')

        gastado = sum(c[i]*n_e[i].x for i in tipos_cargadores)
        print(f"Dinero gastado: {gastado} | Diferencia: {presupuesto - gastado}")

        for d in cantidad_dias:
            data = [[sum(car[m,h,d,i].x for m in automoviles_recibidos) for h in horas_del_dia]
                    for i in tipos_cargadores]
            
            df_por_auto = pd.DataFrame(data=data, index=[f"Tipo {i}" for i in tipos_cargadores],
                            columns=[f"Hora {h}" for h in horas_del_dia])
            
            startrow = (d - 1) * (len(df_por_auto) + 2)

            df_por_auto.to_excel(writer, sheet_name='Cargadores asignados por día', startcol=0, startrow=startrow)



if __name__ == "__main__":
    main()