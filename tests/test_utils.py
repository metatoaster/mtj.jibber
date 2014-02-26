from unittest import TestCase
import tempfile

from mtj.jibber import utils


class Consumer(object):
    loaded = None
    def load(self, config):
        self.loaded = config


class UtilsTestCase(TestCase):

    def test_read_config(self):
        tf = tempfile.NamedTemporaryFile()
        tf.write(b'test')
        tf.flush()
        self.assertEqual(utils.read_config(tf.name), 'test')

    def test_read_config_fail(self):
        self.assertIsNone(utils.read_config(__file__ + '.not_exist'))


class ConfigFileTestCase(TestCase):

    def test_read_config(self):
        tf = tempfile.NamedTemporaryFile()
        tf.write(b'test')
        tf.flush()

        consumer = Consumer()
        cf = utils.ConfigFile(tf.name, consumer.load)
        result = cf.load()

        self.assertEqual(result, 'test')
        self.assertEqual(consumer.loaded, 'test')

    def test_read_config_fail(self):
        tf = __file__ + '.not_exist'

        consumer = Consumer()
        cf = utils.ConfigFile(tf, consumer.load)
        result = cf.load()

        self.assertIsNone(result)
        self.assertIsNone(consumer.loaded)
