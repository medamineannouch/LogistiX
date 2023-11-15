import unittest
import instance


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
        for (weight, cust, plnt, dc, dc_lb, dc_ub, demand, plnt_ub, name) in instance.instances():
            for dic in [cust, plnt, dc]:
                nout = 0
                for i in dic:
                    print(i, dic[i], name[i])
                    nout += 1
                    if nout >= 3:
                        print("...\n")
                        break

if __name__ == '__main__':
    unittest.main()