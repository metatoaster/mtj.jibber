from unittest import TestCase

import re

from mtj.jibber.stanza import admin_query


class StanzaTestCase(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_admin_query_jid(self):
        result = admin_query('room@example.com', jid='test@example.com')
        self.assertEqual(result['to'], 'room@example.com')

        # sleekxmpp iq does not provide any real helpers for the below.
        # raw xml handling code it is.
        self.assertEqual(result.get_payload()[0][0].attrib['jid'],
            'test@example.com')

    def test_admin_query_nick(self):
        result = admin_query('room@example.com', nick='tester')
        self.assertEqual(result['to'], 'room@example.com')

        # sleekxmpp iq does not provide any real helpers for the below.
        # raw xml handling code it is.
        self.assertEqual(result.get_payload()[0][0].attrib['nick'],
            'tester')

    def test_admin_missing_nick_jid(self):
        self.assertRaises(ValueError, admin_query, 'room@example.com')

    def test_admin_bad_role(self):
        self.assertRaises(TypeError, admin_query, 'room@example.com',
            jid='test@example.com', role='bad_role')
