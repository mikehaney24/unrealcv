# TODO: Test robustness, test speed
import unittest, time, sys
from checker import *
from test_common import *
from test_server import EchoServer, MessageServer
import argparse
import threading

TESTPORT = PORT + 1
NO_PORT = PORT + 10 # TODO: Make it a random port
lock_ports = {}
for port in [PORT, TESTPORT]:
    lock_ports[port] = threading.RLock()

lock_unreal_server = threading.RLock()

in_develop_mode = False
# if '--develop' in sys.argv:
#     in_develop_mode = True
#     sys.argv.remove('--develop')
# else:
#     in_develop_mode = False

# client = Client((HOST, PORT), None) # Try different port number
# in_develop_mode = False


class TestPlugin(unittest.TestCase):
    # Test a generic small game
    @classmethod
    def setUpClass(cls):
        cls.client = Client((HOST, PORT), None)
        # If can not connect, report a reasonable message

    def test_objects(self):
        response = self.client.request('vget /objects')
        self.assertTrue(validate_format(response))

        objects = response.split(' ')[:10]
        self.assertTrue(len(objects) > 0)

        print 'Number of objects %d' % len(objects)
        tasks = []
        for objname in objects:
            tasks.append(['vget /object/%s/name' % objname, objname])
            tasks.append(['vget /object/%s/color' % objname, skip])
            # TODO: add a function to check regular expression

        run_tasks(self, self.client, tasks)

    # @unittest.expectedFailure # TODO: Need to fix location
    # @unittest.skipIf(in_develop_mode, 'skip')
    def test_camera(self):
        tasks = [
            ['vget /camera/0/location', skip],
            ['vset /camera/0/rotation 0.0 0.0 0.0', 'ok'],
            ['vget /camera/0/rotation', '0.000 0.000 0.000'],
            # TODO: Change the Uri handle to exact map
            # The regexp in server needs to do exact match
            ['vset /camera/0/location 0.0 0.0 0.0', 'ok'],
            ['vget /camera/0/location', '0.000 0.000 0.000'],
        ]


        modes = ['normal', 'base_color', 'depth', 'lit', 'unlit', 'view', 'object_mask']
        for mode in modes:
            tasks.append(['vget /camera/0/%s' % mode, ispng])

        run_tasks(self, self.client, tasks)

    @unittest.skipIf(in_develop_mode, 'skip')
    def test_viewmode(self):
        tasks = []
        modes = ['depth', 'lit', 'unlit', 'normal', 'object_mask']
        for mode in modes:
            tasks.append(['vset /mode/%s' % mode, 'ok']) # TODO: Change it to vset /mode modename
            tasks.append(['vget /mode', mode])

        run_tasks(self, self.client, tasks)

'''
Stress test to measure performance and whether stable during connection lost
Also check correctness for high throughput case
'''
class TestBaseClient(unittest.TestCase):
    '''
    Test BaseClient
    '''
    @classmethod
    def setUpClass(cls):
        cls.port = TESTPORT
        lock_ports[cls.port].acquire()
        cls.server = MessageServer((HOST, cls.port))
        cls.server.start()
        # cls.base_client = BaseClient((HOST, PORT), None)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        lock_ports[cls.port].release()

    def test_send(self):
        request = "Hello"
        num_response = [0] # This is a trick for workaround
        def handler(response):
            if response == request:
                num_response[0] += 1

        client1 = BaseClient((HOST, self.port), handler)
        client2 = BaseClient((HOST, self.port), handler)
        client3 = BaseClient((HOST, self.port), handler)
        client4 = BaseClient((HOST, self.port), handler)
        for client in [client1, client2, client3, client4]:
            sent= client.send(request)
            self.assertEqual(sent, True, 'Can not send message')

        time.sleep(0.1) # Tolerate some delay
        self.assertEqual(num_response[0], 4)

    def test_no_server(self):
        '''
        Test what will happen if no server is available
        Should give reasonable error
        '''
        client = BaseClient((HOST, NO_PORT), None)
        sent = client.send('hello')
        self.assertEqual(sent, False)



class TestRealisticRendering(unittest.TestCase):
    def test_objects(self):
        '''
        Make sure the object list is the same as expected
        '''
        response = self.client.request('vget /objects')
        response = response.strip() # TODO: remove this line
        self.assertTrue(validate_format(response))

        objects = response.split(' ')
        self.assertTrue(len(objects) > 0)

        print 'Number of objects %d' % len(objects)
        tasks = []
        for objname in objects:
            tasks.append(['vget /object/%s/name' % objname, objname])
            tasks.append(['vget /object/%s/color' % objname, skip])
            # TODO: add a function to check regular expression

        run_tasks(self, self.client, tasks)


if __name__ == '__main__':
    load = unittest.defaultTestLoader.loadTestsFromTestCase

    parser = argparse.ArgumentParser()
    parser.add_argument('--travis', action='store_true') # Only run test availabe to travis CI

    args = parser.parse_args()

    # unittest.main()
    # suite = unittest.TestSuite()
    # suite.addTest(TestCommands())
    suites = []
    # s = load(TestMessageServer); suites.append(s)
    # s = load(TestBaseClient); suites.append(s)
    # s = load(TestClient); suites.append(s)

    if not args.travis:
        s = load(TestPlugin); suites.append(s)
        # s = load(TestRealisticRendering); suites.append(s)

    suite_obj = unittest.TestSuite(suites)
    # suite.run()
    unittest.TextTestRunner().run(suite_obj)
