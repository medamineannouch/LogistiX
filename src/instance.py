""" Generate multiple instances of logistic optimization problems
    for different scenarios to evaluate and test the optimization algorithm"""



import pandas as pd
import random
import numpy as np


"""
def read_data(filename="../data/data_ma.xlsx"):
    df = pd.read_excel(filename,index_col="zip")
    df.index = df.index.map(str)
    return df

def read_plant_data(filename="../data/data_ma.xlsx"):
    df = pd.read_excel(filename,index_col="zip")
    df.index = df.index.map(str)
    return df
def read_customers_data(filename="../data/data_ma.xlsx"):
    df = pd.read_excel(filename,index_col="zip")
    df.index = df.index.map(str)
    return df
def read_dc_data(filename="../data/data_ma.xlsx"):
    df = pd.read_excel(filename,index_col="zip")
    df.index = df.index.map(str)
    return df
"""

def sample_locations(df, n_locations, rnd_stat):
    """
        Sample locations from the DataFrame.

        :param df: DataFrame with location information.
        :param n_locations: Number of locations to sample.
        :param rnd_stat: Random state for reproducibility.
        :return: Tuple of dictionaries containing sampled location information.

    """
    sample = df.sample(n=n_locations, random_state=rnd_stat)
    return (
        sample['province'].to_dict(),
        sample['town'].to_dict(),
        sample['address'].to_dict(),
        sample['latitude'].to_dict(),
        sample['longitude'].to_dict()
    )


def generate_products(num_products):
    """
       Generate product IDs and weights.

       Parameters:
       - num_products (int): Number of products.

       Returns:
       - tuple: Tuple containing a list of product IDs and a dictionary of weights.

    """
    prods = [f"P{p:02}" for p in range(1, num_products + 1)]
    weights = {prod: random.randint(1, 10) for prod in prods}
    return prods, weights


def generate_locations(df, num_locations, random_state):
    """
        Generate location information for customers, distribution centers, and plants.

        Parameters:
        - df (pd.DataFrame): DataFrame with location information.
        - num_locations (int): Number of locations to generate.
        - random_state (np.random.RandomState): Random state for reproducibility.

        Returns:
        - dict: Dictionary containing location information for province, town, address, latitude, and longitude.

    """

    sample = df.sample(n=num_locations, random_state=random_state)
    province = sample['province'].to_dict()
    town = sample['town'].to_dict()
    address = sample['address'].to_dict()
    latitude = sample['latitude'].to_dict()
    longitude = sample['longitude'].to_dict()

    return {
        'province': province,
        'town': town,
        'address': address,
        'latitude': latitude,
        'longitude': longitude
    }


def generate_customer_names(locations):
    """
        Generate customer names based on location information.

        Parameters:
        - locations (dict): Dictionary containing location information.

        Returns:
        - dict: Dictionary mapping location IDs to customer names.

    """
    return {z: f"C-{str(locations['province'][z])}{str(locations['town'][z])}{str(locations['address'][z])}" for z in
            locations['address'].keys()}


def generate_demand(cust, prods):
    """
        Generate random demand for products from customers.

        Parameters:
        - cust (dict): Dictionary containing customer locations.
        - prods (list): List of product IDs.

        Returns:
        - dict: Dictionary mapping (customer, product) pairs to demand values.

    """
    return {(c, p): random.randint(10, 100) for c in cust for p in prods}


def generate_distribution_centers(cust_len,locations):
    """
        Generate distribution center locations and bounds.

        Parameters:
        - df (pd.DataFrame): DataFrame with location information.
        - n_dcs (int): Number of distribution centers.
        - random_state (np.random.RandomState): Random state for reproducibility.
        - cust_len (int): Number of customers.

        Returns:
        - tuple: Tuple containing dictionaries for distribution center locations, lower bounds, and upper bounds.
          (dc, dc_lb, dc_ub)

    """
    dc = {z: (locations['latitude'][z], locations['longitude'][z]) for z in locations['address'].keys()}
    dc_lb = {z: 0 for z in locations['address'].keys()}
    dc_ub = {z: (1000 + 25 * random.randint(1, 9) * cust_len) for z in locations['address'].keys()}
    return dc, dc_lb, dc_ub


def generate_plants(nplant, prod_demand,location):
    """
        Generate plant locations and upper bounds.

        Parameters:
        - df (pd.DataFrame): DataFrame with location information.
        - nplant (int): Number of plants.
        - random_state (np.random.RandomState): Random state for reproducibility.
        - prod_demand (dict): Dictionary containing product demands.

        Returns:
        - tuple: Tuple containing dictionaries for plant locations and upper bounds.
          (plant, plant_ub)

    """
    print(f"generating {nplant}")
    plant = {z: (location['latitude'][z], location['longitude'][z]) for z in location['address'].keys()}
    plant_ub = {(z, p): (prod_demand[p] / nplant + 1000) for z in location['address'].keys() for p in
                prod_demand.keys()}
    print("generate_plants function : ", len(plant))
    return plant, plant_ub


def mk_instance_v2(df, nplant, nd, nc, nprod, seed):
    """
        Create an instance of the logistics network design problem.

        Parameters:
        - df (pd.DataFrame): DataFrame with location information.
        - nplant (int): Number of plants.
        - nd (int): Number of distribution centers.
        - nc (int): Number of customers.
        - nprod (int): Number of products.
        - seed (int): Seed for randomization.

        Returns:
        - tuple: Tuple containing information for weight, customer locations, plant locations,
          distribution center locations, lower bounds, upper bounds, demand , plant upper bounds and name

    """
    print("Number of plants (mk_instance begining):", nplant)
    print("Number of customers (mk_instance begining ):", nc)
    random.seed(seed)
    rnd_stat = np.random.RandomState(seed=seed)

    prods, weight = generate_products(nprod)

    locations_cust = generate_locations(df, nc, rnd_stat)
    locations_plant=generate_locations(df,nplant,rnd_stat)
    cust = {z: (locations_cust['latitude'][z], locations_cust['longitude'][z]) for z in locations_cust['address'].keys()}
    locations_dc=generate_locations(df,nd,rnd_stat)

    demand = generate_demand(cust, prods)
    name = generate_customer_names(locations_cust)
    dc, dc_lb, dc_ub = generate_distribution_centers( len(cust),locations_dc)

    plant, plant_ub = generate_plants( nplant, {p: sum(demand[c, p] for c in cust) for p in prods},locations_plant)
    print("Number of plants (mk_instance at the end ):", len(plant))
    print("Number of customers (mk_instance at the end ):", len(cust))

    return  weight, cust, plant, dc, dc_lb, dc_ub, demand, plant_ub, name

def mk_instance(df_plant,df_cust,df_dc, nplant, nd, nc, nprod, seed):
    """
        Create an instance of the logistics network design problem.

        Parameters:
        - df_plant (pd.DataFrame): DataFrame with plants location information .
        - df_cust (pd.DataFrame): DataFrame with customers location information.
        - df_dc (pd.DataFrame): DataFrame with distribution centers location information.
        - nplant (int): Number of plants.
        - nd (int): Number of distribution centers.
        - nc (int): Number of customers.
        - nprod (int): Number of products.
        - seed (int): Seed for randomization.

        Returns:
        - tuple: Tuple containing information for weight, customer locations, plant locations,
          distribution center locations, lower bounds, upper bounds, demand , plant upper bounds and name

    """
    print("Number of plants (mk_instance begining):", nplant)
    print("Number of customers (mk_instance begining ):", nc)
    random.seed(seed)
    rnd_stat = np.random.RandomState(seed=seed)

    prods, weight = generate_products(nprod)

    locations_cust = generate_locations(df_cust, nc, rnd_stat)
    locations_plant=generate_locations(df_plant,nplant,rnd_stat)
    cust = {z: (locations_cust['latitude'][z], locations_cust['longitude'][z]) for z in
            locations_cust['address'].keys()}
    locations_dc=generate_locations(df_dc,nd,rnd_stat)

    demand = generate_demand(cust, prods)
    name = generate_customer_names(locations_cust)
    dc, dc_lb, dc_ub = generate_distribution_centers( len(cust),locations_dc)

    plant, plant_ub = generate_plants( nplant, {p: sum(demand[c, p] for c in cust) for p in prods},locations_plant)
    print("Number of plants (mk_instance at the end ):", len(plant))
    print("Number of customers (mk_instance at the end ):", len(cust))

    return  weight, cust, plant, dc, dc_lb, dc_ub, demand, plant_ub, name

def mk_instances():
    """
        Generate instances of the logistics network design problem.

        Yields:
        - tuple: Tuple containing information for weight, customer locations, plant locations,
          distribution center locations, lower bounds, upper bounds, demand, plant upper bounds, and customer names.

    """
    df_plant= read_plant_data()
    df_cust=read_customers_data()
    df_dc = read_dc_data()
    n_plants = 2
    n_prods = 3
    seeds = range(1, 11)
    for n_custs in [10]:
        n_dcs = n_custs
        for seed in seeds:

            (weight, cust, plnt, dc, dc_lb, dc_ub, demand, plnt_ub, name) = \
                mk_instance(df_plant,df_cust,df_dc, n_plants, n_dcs, n_custs, n_prods, seed)
            yield (weight, cust, plnt, dc, dc_lb, dc_ub, demand, plnt_ub, name)



