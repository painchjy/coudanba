from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import time
import os

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
        staging_server = os.environ.get('STAGING_SERVER')
        if staging_server:
            setattr(self, 'live_server_url', 'http://'+ staging_server)

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
        self.assertIn(row_text, [row.text for row in rows])

    @wait
    def wait_to_be_logged_in(self, email):
        self.browser.find_elements_by_link_text('Log out')
        navbar = self.browser.find_element_by_css_selector('.navbar')
        self.assertIn(email, navbar.text)

    @wait
    def wait_to_be_logged_out(self, email):
        self.browser.find_elements_by_name('email')
        navbar = self.browser.find_element_by_css_selector('.navbar')
        t = navbar.text

        self.assertNotIn(email, t)

    def get_item_input_box(self):
        return self.browser.find_element_by_id('id_text')
    def get_error_element(self):
        return self.browser.find_element_by_css_selector('.has-error')
