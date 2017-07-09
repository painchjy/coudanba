from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import time
import os
from .server_tools import reset_database, create_session_on_server
from selenium.webdriver.common.keys import Keys
from jus.models import Ju
from accounts.models import User
import json
from fixtures.ju import FIXTURE_JU_CONTENT
from .management.commands.create_session import create_pre_authenticated_session

MAX_WAIT = 10

class FunctionalTest(StaticLiveServerTestCase):
    
    #@classmethod
    #def setUpClass(cls):
    #    for arg in sys.argv:
    #        if 'liveserver' in arg:
    #            cls.server_url = 'http://' + arg.split('=')[1]
    #            return
    #    super().setUpClass()
    #    cls.server_url = cls.live_server_url

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.staging_server = os.environ.get('STAGING_SERVER')
        if self.staging_server:
            setattr(self, 'live_server_url', 'http://'+ self.staging_server)
            reset_database(self.staging_server)

    def load_fixture_ju(self):
        # create first ju content before test
        return Ju.objects.create(content=FIXTURE_JU_CONTENT)

    def load_fixture_user(self, email):
        # create first ju content before test
        return User.objects.create(email=email, display_name=email.split('@')[0])

    def tearDown(self):
        self.browser.quit()

    def wait(fn):
        def modified_fn(*args, **kwargs):
            start_time = time.time()
            while True:
                try:
                    return fn(*args, **kwargs)
                except (AssertionError, WebDriverException) as e:
                    if time.time() - start_time > MAX_WAIT:
                        raise e
                    time.sleep(0.5)
        return modified_fn

    # def wait_for(self, fn):
    #     start_time = time.time()
    #     while True:
    #         try:
    #             return fn()
    #         except (AssertionError, WebDriverException) as e:
    #             if time.time() - start_time > MAX_WAIT:
    #                 raise e
    #             time.sleep(0.5)
    @wait
    def wait_for(self, fn):
        return fn()


    @wait
    def wait_for_row_in_list_table(self, row_text):
        table = self.browser.find_element_by_id('id_list_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn('{} 0.00 0.00 0.00'.format(row_text), [row.text for row in rows])

    @wait
    def wait_for_row_order_in_list_table(self, cd, qty, price, cost):
        table = self.browser.find_element_by_id('id_list_table')
        rows = table.find_elements_by_tag_name('tr')
        row_text = '{} {:.2f} {:.2f} {:.2f}'.format(cd,qty,price,cost)
        self.assertIn(row_text, [row.text for row in rows])

    @wait
    def wait_for_row_order_not_in_list_table(self, cd, qty, price, cost):
        table = self.browser.find_element_by_id('id_list_table')
        rows = table.find_elements_by_tag_name('tr')
        row_text = '{} {:.2f} {:.2f} {:.2f}'.format(cd,qty,price,cost)
        self.assertNotIn(row_text, [row.text for row in rows])

    @wait
    def wait_for_row_in_ju_table(self, row_text):
        table = self.browser.find_element_by_id('id_ju_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn(row_text, ''.join([row.text for row in rows]))

    @wait
    def wait_to_be_logged_in(self, email):
        self.browser.find_elements_by_link_text('Log out')
        navbar = self.browser.find_element_by_css_selector('.navbar')
        self.assertIn(email.split('@')[0], navbar.text)

    @wait
    def wait_to_be_logged_out(self, email):
        self.browser.find_elements_by_name('email')
        navbar = self.browser.find_element_by_css_selector('.navbar')
        t = navbar.text

        self.assertNotIn(email.split('@')[0], t)

    def get_item_input_box(self):
        return self.get_item_input_box_by_id('id_text')
    def get_item_input_box_by_id(self,id):
        return self.browser.find_element_by_id(id)
    def get_error_element(self):
        return self.browser.find_element_by_css_selector('.has-error')

    def add_list_item(self, item_text):
        num_rows = max(len(self.browser.find_elements_by_css_selector('#id_list_table tr')) - 2,0)
        self.get_item_input_box().send_keys(item_text)
        self.get_item_input_box().send_keys(Keys.ENTER)
        item_number = num_rows + 1
        self.wait_for_row_in_list_table(
            '{}: {}'.format(item_number, item_text)
        )

    def add_list_item_for_orders(self, item_text):
        num_rows = len(self.browser.find_elements_by_css_selector('#id_list_table tr'))
        self.get_item_input_box().send_keys(item_text)
        self.get_item_input_box().send_keys(Keys.ENTER)
        item_number = num_rows + 1
        self.wait_for_row_in_list_table(
            '{}: {}'.format(item_number, item_text)
        )
    def create_pre_authenticated_session(self, email):
        if self.staging_server:
            session_key = create_session_on_server(self.staging_server, email)
        else:
            session_key = create_pre_authenticated_session(email)

        ## to set cookie we need to first visit the domain
        ## 404 pages load the quickest!
        self.browser.get(self.live_server_url+ "/404_no_such_url/")
        self.browser.add_cookie(dict(
            name = settings.SESSION_COOKIE_NAME,
            value = session_key,
            path = '/',
            ))
        return session_key

