from gurobipy import Model, quicksum, GRB
import pandas as pd


undefined = -1

def main():
    energia_por_tipo = pd.read_csv("data/energia_por_tipo.csv", header=None)
    satisfaccion_por_tipo = pd.read_csv("data/satisfaccion.csv", header=None)
    costo_por_tipo = pd.read_csv("data/costo_por_tipo.csv", header=None)
    energia_total_edificio = pd.read_csv("data/energia_total_edificio.csv")
    cantidad_estacionamientos = pd.read_csv("data/cantidad_estacionamientos.csv", header=None)
    presupuesto = pd.read_csv("data/presupuesto.csv", header=None)
    potencia_por_auto_dia = pd.read_csv("data/potencia_por_auto_dia.csv", header=None)
    capacidad_por_auto = pd.read_csv("data/capacidad_por_auto.csv", header=None)
    
    I = 3 # tipos de cargadores distintos
    HT = 10 # cantidad total de horas
    M = undefined # cantidad de autos que llegan TODO
    D = 3653 # días totales

    tipos_cargadores = range(1, I + 1)
    horas_del_dia = range(1, HT + 1)
    automoviles_recibidos = range(1, M + 1)
    cantidad_dias = range(1, D + 1)


    """ Parámetros """
    wc = {i:  for i in tipos_cargadores} # 1.1 - 3.3 kW
    wt = undefined
    c = {i: undefined for i in tipos_cargadores}
    n_et = undefined
    p = undefined
    cb = {m: undefined for m in automoviles_recibidos}
    w = {(m, d): undefined for m in automoviles_recibidos for d in cantidad_dias}
    h = {i: undefined for i in tipos_cargadores}


    # creación modelo
    model = Model()


    """ Variables """
    n_e = model.addVars(tipos_cargadores, vtype=GRB.INTEGER)
    
    x = model.addVars(automoviles_recibidos, tipos_cargadores, cantidad_dias,
                    vtype=GRB.BINARY)
    
    car = model.addVars(automoviles_recibidos, horas_del_dia, cantidad_dias, tipos_cargadores,
                    vtype=GRB.BINARY)
    
    t = model.addVars(automoviles_recibidos, cantidad_dias, tipos_cargadores,
                    vtype=GRB.CONTINUOUS)
    
    model.update()


    """ Restricciones """
    # TODO

    """ Función Objetivo """
    f_obj = quicksum(
        quicksum(
            quicksum(
                h[i] * x[m, i, d] for i in tipos_cargadores
                )
            for m in automoviles_recibidos
        )
        for d in cantidad_dias
    )

    model.setObjective(f_obj, GRB.MAXIMIZE)
    model.optimize()


    """ IMPRIMIR VALORES"""
    # TODO



if __name__ == "__main__":
    main()