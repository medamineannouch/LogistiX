from geopy.distance import great_circle as distance
from gurobipy import *
from tqdm import tqdm
import dash
from dash import html
from dash import dash_table
def mk_costs(plnt, dc, cust):
    """
        Instantiate costs for a given set of plants, distribution centers, and customers.

        :param plnt: Dictionary associating a plant ID to its location as (latitude, longitude).
        :param dc: Dictionary associating a distribution center ID to its location as (latitude, longitude).
        :param cust: Dictionary associating a customer ID to its location as (latitude, longitude).

        :return: Tuple with transportation costs, delivery costs, distribution center fixed costs, and distribution center variable costs.

    """
    unit_tp_cost = 1
    unit_del_cost = 10
    unit_dc_fc = 1000
    unit_dc_vc = 1

    tp_cost = {(i, j): unit_tp_cost * distance(plnt[i], dc[j]).kilometers for i in plnt for j in dc}
    del_cost = {(j, k): unit_del_cost * distance(dc[j], cust[k]).kilometers for j in dc for k in cust}
    dc_fc = {j: unit_dc_fc for j in dc}
    dc_vc = {j: unit_dc_vc for j in dc}

    return tp_cost, del_cost, dc_fc, dc_vc







def multiple_src(weight, cust, dc,  dc_ub, plnt, plnt_ub, demand, tp_cost, del_cost, dc_fc, dc_vc, dc_num):
    """
        Logistics network design, multiple sources.

        :param weight: Dictionary with product IDs and their respective unit weights.
        :param cust: Dictionary associating a customer ID to its location as (latitude, longitude).
        :param dc: Dictionary associating a distribution center ID to its location as (latitude, longitude).
        :param dc_ub: Upper bounds for distribution centers.
        :param plnt: Dictionary associating a plant ID to its location as (latitude, longitude).
        :param plnt_ub: Upper bounds for plants.
        :param demand: Dictionary mapping (customer, product) pairs to demand values.
        :param tp_cost: Unit transportation cost from plants to distribution centers.
        :param del_cost: Unit delivery cost from distribution centers to customers.
        :param dc_fc: Fixed cost for opening a distribution center.
        :param dc_vc: Unit (variable) cost for operating a distribution center.
        :param dc_num: Maximum number of distribution centers to open.

        :return: Gurobi model for the multiple-source logistics network design.

        Notes:
            - The function uses the Gurobi optimization library to formulate and solve the logistics
              network design problem as a linear programming model.
            - The model considers multiple sources (plants) and aims to minimize total costs,
              including transportation costs, delivery costs, fixed costs, and variable costs.
            - Constraints ensure that customer demand is satisfied, flow is maintained, and
              upper bounds for distribution centers and plants are respected.
            - The objective function includes terms for minimizing both fixed and variable costs,
              providing a comprehensive cost-based optimization.
    """
    prod = set(weight.keys())
    plnt_to_dc = set((i, j, p) for i in plnt for j in dc for p in prod if plnt_ub.get((i, p), 0) > 0)
    dc_to_cust = set((j, k, p) for j in dc for k in cust for p in prod if demand[k, p] > 0)

    model = Model()

    #variables
    x, y = {}, {}
    for (i, j, p) in plnt_to_dc | dc_to_cust:
        x[i, j, p] = model.addVar(vtype='C', name=f'x[{i},{j},{p}]')

    slack = {}
    for (k, p) in demand:
        if demand[k, p] > 0.:
            slack[k, p] = model.addVar(vtype="C", name=f"slack[{k},{p}]")

    for j in dc:
        y[j] = model.addVar(vtype='B', name=f'y[{j}]')

    model.update()

    Cust_Demand_Cons, DC_Flow_Cons, DC_Strong_Cons, DC_UB_Cons, DC_LB_Cons, Plnt_UB_Cons = {}, {}, {}, {}, {}, {}

    #customer demand constraint
    for k in tqdm(cust):
        for p in prod:
            if demand[k, p] > 0.:
                Cust_Demand_Cons[k, p] = model.addConstr(
                    quicksum(x[j, k, p] for j in dc if (j, k, p) in dc_to_cust) + slack[k, p]
                    ==
                    demand[k, p],
                    name=f'Cust_Demand_Cons[{k},{p}]'
                )

    # Flow conservation constraint
    for j in tqdm(dc):
        for p in prod:
            DC_Flow_Cons[j, p] = model.addConstr(
                quicksum(x[i, j, p] for i in plnt if (i, j, p) in plnt_to_dc)
                ==
                quicksum(x[j, k, p] for k in cust if (j, k, p) in dc_to_cust),
                name=f'DC_Flow_Cons[{j},{p}]'
            )


    # Strong activation constraint
    for (j, k, p) in dc_to_cust:
        DC_Strong_Cons[j, k, p] = model.addConstr(
            x[j, k, p]
            <=
            demand[k, p] * y[j],
            name=f'DC_Strong_Cons[{j},{k},{p}]'
        )

    # Upper bound constraint for distribution centers
    for j in tqdm(dc):
        DC_UB_Cons[j] = model.addConstr(
            dc_ub[j] * y[j]
            >=
            quicksum(x[i, j, p] for i in plnt for p in prod if (i, j, p) in plnt_to_dc),
            name=f'DC_UB_Cons[{j}]'
        )

    # Upper bound constraint for plants
    for i in tqdm(plnt):
        for p in prod:
            Plnt_UB_Cons[i, p] = model.addConstr(
                plnt_ub[i, p]
                >=
                quicksum(x[i, j, p] for j in dc if (i, j, p) in plnt_to_dc),
                name=f'Plnt_UB_Cons[{i},{p}]'
            )

    # Constraint on the number of distribution centers to open
    DC_Num_Cons = model.addConstr(
        quicksum(y[j] for j in dc)
        <=
        dc_num,
        name='DC_Num_Cons'
    )

    model.update()

    #Objective function
    model.setObjective(
        quicksum(weight[p] * tp_cost[i, j] * x[i, j, p] for (i, j, p) in plnt_to_dc) +
        quicksum(weight[p] * del_cost[j, k] * x[j, k, p] for (j, k, p) in dc_to_cust) +
        quicksum(dc_fc[j] * y[j] for j in dc) +
        quicksum(dc_vc[j] * x[i, j, p] for (i, j, p) in plnt_to_dc) +
        quicksum(999999 * slack[k, p] for k in cust for p in prod if demand[k, p] > 0.)
    )
    model.update()
    model.__data = x, y
    return model


def single_src(weight, cust, dc,  dc_ub, plnt, plnt_ub, demand, tp_cost, del_cost, dc_fc, dc_vc, dc_num):
    """
        Logistics network design, single source.

        :param weight: Dictionary with product IDs and their respective unit weights.
        :param cust: Dictionary associating a customer ID to its location as (latitude, longitude).
        :param dc: Dictionary associating a distribution center ID to its location as (latitude, longitude).
        :param dc_ub: Upper bounds for distribution centers.
        :param plnt: Dictionary associating a plant ID to its location as (latitude, longitude).
        :param plnt_ub: Upper bounds for plants.
        :param demand: Dictionary mapping (customer, product) pairs to demand values.
        :param tp_cost: Unit transportation cost from plants to distribution centers.
        :param del_cost: Unit delivery cost from distribution centers to customers.
        :param dc_fc: Fixed cost for opening a distribution center.
        :param dc_vc: Unit (variable) cost for operating a distribution center.
        :param dc_num: Maximum number of distribution centers to open.

        :return: Gurobi model for the single-source logistics network design.

        Notes:
            - The function uses the Gurobi optimization library to formulate and solve the logistics
              network design problem as a linear programming model.
            - The model considers a single source (plant) and aims to minimize total costs,
              including transportation costs, delivery costs, fixed costs, and variable costs.
            - Constraints ensure that customer demand is satisfied, flow is maintained, and
              upper bounds for distribution centers and plants are respected.
            - The objective function includes terms for minimizing both fixed and variable costs,
              providing a comprehensive cost-based optimization.

    """
    prod = set(weight.keys())
    plnt_to_dc = set((i, j, p) for i in plnt for j in dc for p in prod if plnt_ub.get((i, p), 0) > 0)
    dc_to_cust = set((j, k, p) for j in dc for k in cust for p in prod if demand[k, p] > 0)

    model = Model()
    x, y = {}, {}
    z = {}
    for (i, j, p) in plnt_to_dc:
        x[i, j, p] = model.addVar(vtype='C', name=f'x[{i},{j},{p}]')
    for j in dc:
        for k in cust:
            z[j, k] = model.addVar(vtype="B", name=f"z[{j},{k}]")

    slack = {}
    for k in cust:
        slack[k] = model.addVar(vtype="C", name=f"slack[{k}]")

    for j in dc:
        y[j] = model.addVar(vtype='B', name=f'y[{j}]')

    model.update()

    Cust_Demand_Cons, DC_Flow_Cons, DC_Strong_Cons, DC_UB_Cons, DC_LB_Cons, Plnt_UB_Cons = {}, {}, {}, {}, {}, {}

    #Custumor demand constraint
    for k in cust:
        Cust_Demand_Cons[k] = model.addConstr(
            quicksum(z[j, k] for j in dc) + slack[k]
            == 1,
            name=f'Cust_Demand_Cons[{k}]'
        )
    # Flow conservation constraint
    for j in dc:
        for p in prod:
            DC_Flow_Cons[j, p] = model.addConstr(
                quicksum(x[i, j, p] for i in plnt if (i, j, p) in plnt_to_dc)
                ==
                quicksum(demand[k, p] * z[j, k] for k in cust),
                name=f'DC_Flow_Cons[{j},{p}]'
            )



    # Strong activation constraint
    for j in dc:
        for k in cust:
            DC_Strong_Cons[j, k] = model.addConstr(
                z[j, k]
                <=
                y[j],
                name=f'DC_Strong_Cons[{j},{k}]'
            )


    # Upper bound constraint for distribution centers
    for j in tqdm(dc):
        DC_UB_Cons[j] = model.addConstr(
            dc_ub[j] * y[j]
            >=
            quicksum(x[i, j, p] for i in plnt if (i, j, p) in plnt_to_dc),
            name=f'DC_UB_Cons[{j}]'
        )


    # Upper bound constraint for plants
    for i in tqdm(plnt):
        for p in prod:
            Plnt_UB_Cons[i, p] = model.addConstr(
                plnt_ub[i, p]
                >=
                quicksum(x[i, j, p] for j in dc if (i, j, p) in plnt_to_dc),
                name=f'Plnt_UB_Cons[{i},{p}]'
            )

    # Constraint on the number of distribution centers to open
    DC_Num_Cons = model.addConstr(
        quicksum(y[j] for j in dc)
        <=
        dc_num,
        name='DC_Num_Cons'
    )

    model.update()

    total_demand = {k: sum(demand[k, p] for p in prod) for k in cust}

    #objectivee function
    model.setObjective(
        quicksum(weight[p] * tp_cost[i, j] * x[i, j, p] for (i, j, p) in plnt_to_dc) +
        quicksum(weight[p] * del_cost[j, k] * total_demand[k] * z[j, k] for j in dc for k in cust) +
        quicksum(dc_fc[j] * y[j] for j in dc) +
        quicksum(dc_vc[j] * x[i, j, p] for (i, j, p) in plnt_to_dc) +
        quicksum(99999999 * slack[k] for k in cust)
    )
    model.update()
    model.__data = x, y
    return model


def multiple_src2(weight, cust, dc,  dc_ub, plnt, plnt_ub, demand, tp_cost, del_cost, dc_fc, dc_vc, dc_num):
    """
        Logistics network design, multiple sources.

        :param weight: Dictionary with product IDs and their respective unit weights.
        :param cust: Dictionary associating a customer ID to its location as (latitude, longitude).
        :param dc: Dictionary associating a distribution center ID to its location as (latitude, longitude).
        :param dc_ub: Upper bounds for distribution centers.
        :param plnt: Dictionary associating a plant ID to its location as (latitude, longitude).
        :param plnt_ub: Upper bounds for plants.
        :param demand: Dictionary mapping (customer, product) pairs to demand values.
        :param tp_cost: Unit transportation cost from plants to distribution centers.
        :param del_cost: Unit delivery cost from distribution centers to customers.
        :param dc_fc: Fixed cost for opening a distribution center.
        :param dc_vc: Unit (variable) cost for operating a distribution center.
        :param dc_num: Maximum number of distribution centers to open.

        :return: Gurobi model for the multiple-source logistics network design.

        Notes:
            - The function uses the Gurobi optimization library to formulate and solve the logistics
              network design problem as a linear programming model.
            - The model considers multiple sources (plants) and aims to minimize total costs,
              including transportation costs, delivery costs, fixed costs, and variable costs.
            - Constraints ensure that customer demand is satisfied, flow is maintained, and
              upper bounds for distribution centers and plants are respected.
            - The objective function includes terms for minimizing both fixed and variable costs,
              providing a comprehensive cost-based optimization.
    """
    prod = set(weight.keys())
    plnt_to_dc = set((i, j, p) for i in plnt for j in dc for p in prod if plnt_ub.get((i, p), 0) > 0)
    dc_to_cust = set((j, k, p) for j in dc for k in cust for p in prod if demand[k, p] > 0.)

    model = Model()

    # Decision variables for flow from plants to distribution centers
    x_plant_to_dc = {}
    for (i, j, p) in plnt_to_dc:
        x_plant_to_dc[i, j, p] = model.addVar(vtype='C', name=f'x_plant_to_dc[{i},{j},{p}]')

    # Decision variables for flow from distribution centers to customers
    x_dc_to_customer = {}
    for (j, k, p) in dc_to_cust:
        x_dc_to_customer[j, k, p] = model.addVar(vtype='C', name=f'x_dc_to_customer[{j},{k},{p}]')

    # Slack variables for customer demand
    slack = {}
    for (k, p) in demand:
        if demand[k, p] > 0.:
            slack[k, p] = model.addVar(vtype="C", name=f"slack[{k},{p}]")

    # Binary decision variables for opening distribution centers
    y = {}
    for j in dc:
        y[j] = model.addVar(vtype='B', name=f'y[{j}]')

    model.update()

    Cust_Demand_Cons, DC_Flow_Cons, DC_Strong_Cons, DC_UB_Cons, DC_LB_Cons, Plnt_UB_Cons = {}, {}, {}, {}, {}, {}

    # Customer demand constraint
    for k in tqdm(cust):
        for p in prod:
            if demand[k, p] > 0.:
                Cust_Demand_Cons[k, p] = model.addConstr(
                    quicksum(x_dc_to_customer[j, k, p] for j in dc) + slack[k, p]
                    ==
                    demand[k, p],
                    name=f'Cust_Demand_Cons[{k},{p}]'
                )

    # Flow conservation constraint
    for j in tqdm(dc):
        for p in prod:
            DC_Flow_Cons[j, p] = model.addConstr(
                quicksum(x_plant_to_dc[i, j, p] for i in plnt) +
                quicksum(x_dc_to_customer[j, k, p] for k in cust)
                ==
                quicksum(x_plant_to_dc[i, k, p] for k in cust),
                name=f'DC_Flow_Cons[{j},{p}]'
            )

    # Strong activation constraint
    for (j, k, p) in dc_to_cust:
        DC_Strong_Cons[j, k, p] = model.addConstr(
            x_dc_to_customer[j, k, p]
            <=
            demand[k, p] * y[j],
            name=f'DC_Strong_Cons[{j},{k},{p}]'
        )

    # Upper bound constraint for distribution centers
    for j in tqdm(dc):
        DC_UB_Cons[j] = model.addConstr(
            dc_ub[j] * y[j]
            >=
            quicksum(x_plant_to_dc[i, j, p] for i in plnt for p in prod),
            name=f'DC_UB_Cons[{j}]'
        )

    # Upper bound constraint for plants
    for i in tqdm(plnt):
        for p in prod:
            Plnt_UB_Cons[i, p] = model.addConstr(
                plnt_ub[i, p]
                >=
                quicksum(x_plant_to_dc[i, j, p] for j in dc if (i, j, p) in plnt_to_dc),
                name=f'Plnt_UB_Cons[{i},{p}]'
            )
    # Constraint on the number of distribution centers to open
    DC_Num_Cons = model.addConstr(
        quicksum(y[j] for j in dc)
        <=
        dc_num,
        name='DC_Num_Cons'
    )

    model.update()

    # Objective function
    model.setObjective(
        quicksum(weight[p] * tp_cost[i, j] * x_plant_to_dc[i, j, p] for (i, j, p) in plnt_to_dc) +
        quicksum(weight[p] * del_cost[j, k] * x_dc_to_customer[j, k, p] for (j, k, p) in dc_to_cust) +
        quicksum(dc_fc[j] * y[j] for j in dc) +
        quicksum(dc_vc[j] * x_plant_to_dc[i, j, p] for (i, j, p) in plnt_to_dc) +
        quicksum(999999 * slack[k, p] for k in cust for p in prod if demand[k, p] > 0.)
    )

    model.update()
    model.__data = x_plant_to_dc, x_dc_to_customer, y
    return model
