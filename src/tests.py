import unittest
import instance
import time
import pre_clusterer
from geopy.distance import great_circle as distance
from gurobipy import Model, GRB
from model import multiple_src, single_src, mk_costs

class TestInstances(unittest.TestCase):
    def test_location_sample(self):
        df = instance.read_data()
        for n in [10, 100, 1000]:
            print(f"testing location sample, n:{n}")
            for seed in range(1, 11):
                print(f"instance {n}:{seed}")
                (province, town, address, latitude, longitude) = instance.sample_locations(df, n, seed)
                nout = 0
                for i in province:
                    print(i, latitude[i], longitude[i], town[i])
                    nout += 1
                    if nout >= 3:
                        print("...")
                        break

    def test_instance_generation(self):
        for (prods,weight, cust, plnt, dc, dc_lb, dc_ub, demand, plnt_ub, name) in instance.mk_instances():
            for dic in [cust, plnt, dc]:
                nout = 0

                for i in dic:
                    print(i, dic[i], name[i])
                    nout += 1
                    if nout >= 3:
                        print("...\n")
                        break


    def test_pre_clusterer(self):
        """
        Test optimizing the location of a small number of dc's from set of candidates
        """
        for (prods,weight, cust, plnt, dc, dc_lb, dc_ub, demand, plnt_ub, name) in instance.mk_instances():
            start = time.process_time()
            prods = weight.keys()
            n_clusters = (10 + len(dc)) // 5
            cluster_dc = pre_clusterer.preclustering(cust, dc, prods, demand, n_clusters)
            end = time.process_time()
            print("Clustered dc's, used {} seconds".format(end - start))
            print("Selected", len(cluster_dc), "dc's out of", len(dc.keys()), "possible positions")


        """
        Unit tests for the solving functions in lnd_ms and lnd_ss.
        """

    def setUp(self):
        """
        Set up any common variables or configurations needed for the tests.
        """
        self.TIME_LIMIT = 300  # Allow Gurobi to use 5 minutes

    def test_optimization_with_small_instance(self):
        """
        Test optimizing the location of a small number of dc's from a set of candidates.
        """
        models = {
            "multiple source": multiple_src,
            "single source": single_src
        }

        for k in models:
            for (prods,weight, cust, plnt, dc, dc_lb, dc_ub, demand, plnt_ub, name) in instance.mk_instances():
                print(f"* using {k} model *")
                print(f"*** new instance, {len(plnt)} plants + {len(dc)} dc's + {len(cust)} customers ***")
                start = time.process_time()
                (tp_cost, del_cost, dc_fc, dc_vc) = mk_costs(plnt, dc, cust)
                dc_num = (20 + len(dc)) // 10

                model = models[k]( weight, cust, dc, dc_ub, plnt, plnt_ub, demand, tp_cost, del_cost, dc_fc, dc_vc, dc_num)
                model.setParam('TimeLimit', self.TIME_LIMIT)
                model.optimize()

                EPS = 1.e-6
                for x in model.getVars():
                    if x.X > EPS:
                        print(x.varName, x.X)

                end = time.process_time()
                print(f"solving MIP used {end - start} seconds")
                print()




    def test_demand_keys(self):

        for inst in instance.mk_instances():
            prods, weight, cust, plnt, dc, dc_lb, dc_ub, demand, plnt_ub, name = inst

            # Ensure that all keys in the 'demand' dictionary have corresponding entries in 'cust' and 'prods'
            for (customer, product) in demand.keys():
                self.assertIn(customer, cust, f"Customer {customer} not found in 'cust' dictionary")
                self.assertIn(product, prods, f"Product {product} not found in 'prods' list")

            # Ensure that all customers in 'cust' have corresponding entries in 'demand'
            for customer in cust.keys():
                for product in prods:
                    self.assertIn((customer, product), demand, f"Missing entry for ({customer}, {product}) in 'demand'")



if __name__ == '__main__':
    unittest.main()