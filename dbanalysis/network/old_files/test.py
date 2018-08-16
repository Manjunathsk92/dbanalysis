import unittest

class networktest(unittest.TestCase):
    
    def test_load(self):
        from simple_network2 import simple_network
        import pickle
        with open('simple_network_concated','rb') as handle:
            self.n = pickle.load(handle)
    def test_starting_out(self):
        pass

def main():
    unittest.main()

if __name__ == "__main__":
    main()
